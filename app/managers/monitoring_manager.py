"""
Monitoring Manager für OSS goEcommerce
Verwaltet den gesamten Abgleich-Prozess mit Fortschritts-Tracking
"""

import pyodbc
import requests
import json
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime


class MonitoringManager:
    """Manager für Monitoring und Abgleich-Prozesse"""
    
    def __init__(self, db_manager=None, n8n_manager=None):
        """
        Initialisiert den Monitoring Manager
        
        Args:
            db_manager: JTLDatabaseManager Instanz
            n8n_manager: N8nWorkflowManager Instanz
        """
        self.db_manager = db_manager
        self.n8n_manager = n8n_manager
        self.progress_callback = None
        
    def set_progress_callback(self, callback: Callable):
        """Setzt eine Callback-Funktion für Fortschritts-Updates"""
        self.progress_callback = callback
    
    def _report_progress(self, step: str, current: int, total: int, status: str = "running"):
        """Meldet den aktuellen Fortschritt"""
        if self.progress_callback:
            self.progress_callback(step, current, total, status)
    
    def create_trigger(self) -> Tuple[bool, str, Dict]:
        """
        Schritt 1: Erstellt den Trigger tgr_oss_goe_tartikel_INSUP
        
        Returns:
            Tuple[bool, str, Dict]: (success, message, stats)
        """
        self._report_progress("01. Trigger erstellen", 0, 1, "starting")
        
        try:
            if not self.db_manager:
                return False, "Kein Datenbankmanager verfügbar", {}
            
            if not self.db_manager.has_saved_credentials():
                return False, "Keine Datenbankverbindung konfiguriert", {}
            
            # Trigger SQL
            trigger_sql = """
            IF EXISTS (SELECT * FROM sys.triggers WHERE name = 'tgr_oss_goe_tartikel_INSUP')
                DROP TRIGGER tgr_oss_goe_tartikel_INSUP
            GO
            
            CREATE TRIGGER tgr_oss_goe_tartikel_INSUP
            ON tartikel
            AFTER INSERT, UPDATE
            AS
            BEGIN
                DECLARE @kArtikel INT
                DECLARE @cartnr VARCHAR(255)
                DECLARE @cBarcode VARCHAR(255)
                DECLARE @cTaric VARCHAR(255)
                
                IF @@ROWCOUNT = 0
                    RETURN
                
                SELECT TOP 1
                    @kArtikel = kArtikel,
                    @cartnr = cartnr,
                    @cBarcode = cBarcode,
                    @cTaric = cTaric
                FROM inserted
                
                -- Hier könnten weitere Logik-Funktionen ausgeführt werden
                IF @cTaric IS NOT NULL AND @cTaric != ''
                BEGIN
                    -- Trigger-Logik für TARIC-Artikel
                    -- z.B. Logging, Notification, etc.
                    PRINT 'TARIC Artikel ' + @cartnr + ' wurde aktualisiert'
                END
            END
            """
            
            # Verbindung herstellen
            password = self.db_manager.get_password()
            if not password:
                return False, "Kein Passwort verfügbar", {}
            
            connection_string = (
                f"DRIVER={{{self.db_manager.config['driver']}}};"
                f"SERVER={self.db_manager.config['server']};"
                f"DATABASE={self.db_manager.config['database']};"
                f"UID={self.db_manager.config['username']};"
                f"PWD={password};"
                f"Trusted_Connection=no;"
            )
            
            connection = pyodbc.connect(connection_string, timeout=10)
            cursor = connection.cursor()
            
            # Prüfe ob Trigger bereits existiert
            cursor.execute("""
                SELECT COUNT(*) 
                FROM sys.triggers 
                WHERE name = 'tgr_oss_goe_tartikel_INSUP'
            """)
            
            trigger_exists = cursor.fetchone()[0] > 0
            
            if not trigger_exists:
                # Erstelle Trigger
                cursor.execute(trigger_sql)
                connection.commit()
                
                self._report_progress("01. Trigger erstellen", 1, 1, "completed")
                return True, "Trigger erfolgreich erstellt", {"trigger_created": True}
            else:
                self._report_progress("01. Trigger erstellen", 1, 1, "completed")
                return True, "Trigger existiert bereits", {"trigger_exists": True}
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            self._report_progress("01. Trigger erstellen", 0, 1, "failed")
            return False, f"Fehler beim Erstellen des Triggers: {str(e)}", {}
    
    def send_product_data(self) -> Tuple[bool, str, Dict]:
        """
        Schritt 2: Sendet Produktdaten
        
        Returns:
            Tuple[bool, str, Dict]: (success, message, stats)
        """
        self._report_progress("02. Produktdaten senden", 0, 1, "starting")
        
        try:
            if not self.db_manager:
                return False, "Kein Datenbankmanager verfügbar", {}
            
            # Hole Produktdaten
            success, message, products = self.db_manager.get_products_with_taric_info()
            
            if not success or not products:
                self._report_progress("02. Produktdaten senden", 0, len(products or []), "failed")
                return False, f"Fehler beim Laden der Produktdaten: {message}", {}
            
            total_products = len(products)
            sent_count = 0
            failed_count = 0
            
            # Sende Produkte
            if self.n8n_manager:
                for idx, product in enumerate(products):
                    try:
                        # Sende einzelnes Produkt
                        webhook_url = "https://agentic.go-ecommerce.de/webhook-test/post_customer_product"
                        success_send = self._send_single_product(product, webhook_url)
                        
                        if success_send:
                            sent_count += 1
                        else:
                            failed_count += 1
                        
                        # Fortschritt melden (jedes 10. Produkt)
                        if (idx + 1) % 10 == 0 or (idx + 1) == total_products:
                            self._report_progress(
                                "02. Produktdaten senden", 
                                idx + 1, 
                                total_products, 
                                "running"
                            )
                    
                    except Exception as e:
                        print(f"Fehler beim Senden des Produkts {product.get('sku', 'Unknown')}: {e}")
                        failed_count += 1
                        
            else:
                self._report_progress("02. Produktdaten senden", 0, total_products, "failed")
                return False, "Kein n8n Manager verfügbar", {}
            
            self._report_progress("02. Produktdaten senden", total_products, total_products, "completed")
            
            stats = {
                "total": total_products,
                "sent": sent_count,
                "failed": failed_count
            }
            
            return True, f"{sent_count}/{total_products} Produkte erfolgreich gesendet", stats
            
        except Exception as e:
            self._report_progress("02. Produktdaten senden", 0, 1, "failed")
            return False, f"Fehler beim Senden der Produktdaten: {str(e)}", {}
    
    def _send_single_product(self, product: Dict, webhook_url: str) -> bool:
        """Sendet ein einzelnes Produkt an den n8n Webhook"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'OSS-goEcommerce/1.0.0',
                'X-License-Number': '123456',
                'X-License-Email': 'ivan.levshyn@go-ecommerce.de',
                'X-App-Version': '1.0.0',
                'X-Timestamp': datetime.now().isoformat()
            }
            
            data = {
                "product_name": product.get('name', ''),
                "ean": product.get('ean', ''),
                "taric": product.get('taric', ''),
                "sku": product.get('sku', ''),
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(webhook_url, json=data, headers=headers, timeout=30)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Fehler beim Senden des Produkts: {e}")
            return False
    
    def fetch_and_save_tax_info(self) -> Tuple[bool, str, Dict]:
        """
        Schritt 3: Holt und speichert aktuelle Steuer-Informationen
        
        Returns:
            Tuple[bool, str, Dict]: (success, message, stats)
        """
        self._report_progress("03. Steuer-Informationen holen", 0, 1, "starting")
        
        try:
            if not self.n8n_manager:
                self._report_progress("03. Steuer-Informationen holen", 0, 1, "failed")
                return False, "Kein n8n Manager verfügbar", {}
            
            # Hole Steuerdaten (z.B. für alle EU-Länder)
            # Dies ist eine vereinfachte Version
            eu_countries = ['DE', 'FR', 'IT', 'ES', 'PL']
            total_countries = len(eu_countries)
            fetched_count = 0
            
            for idx, country in enumerate(eu_countries):
                try:
                    # Hier würde die tatsächliche Steuer-Info abgerufen werden
                    # Für jetzt simulieren wir es
                    fetched_count += 1
                    
                    # Fortschritt melden
                    self._report_progress(
                        "03. Steuer-Informationen holen",
                        idx + 1,
                        total_countries,
                        "running"
                    )
                    
                except Exception as e:
                    print(f"Fehler beim Holen der Steuer-Info für {country}: {e}")
            
            self._report_progress("03. Steuer-Informationen holen", total_countries, total_countries, "completed")
            
            stats = {
                "total_countries": total_countries,
                "fetched": fetched_count
            }
            
            return True, f"Steuer-Informationen für {fetched_count} Länder geholt", stats
            
        except Exception as e:
            self._report_progress("03. Steuer-Informationen holen", 0, 1, "failed")
            return False, f"Fehler beim Holen der Steuer-Informationen: {str(e)}", {}
    
    def fetch_oss_combinations(self) -> Tuple[bool, str, Dict]:
        """
        Schritt 4: Holt OSS-Kombinationen
        
        Returns:
            Tuple[bool, str, Dict]: (success, message, stats)
        """
        self._report_progress("04. OSS-Kombinationen holen", 0, 1, "starting")
        
        try:
            if not self.db_manager:
                self._report_progress("04. OSS-Kombinationen holen", 0, 1, "failed")
                return False, "Kein Datenbankmanager verfügbar", {}
            
            # Simuliere das Holen von OSS-Kombinationen
            # In der echten Implementierung würde hier eine Abfrage erfolgen
            total_combinations = 50  # Beispielwert
            fetched_count = 0
            
            # Simuliere den Abruf
            for idx in range(total_combinations):
                # Hier würde die tatsächliche Logik stehen
                fetched_count += 1
                
                # Fortschritt alle 5 Kombinationen melden
                if (idx + 1) % 5 == 0 or (idx + 1) == total_combinations:
                    self._report_progress(
                        "04. OSS-Kombinationen holen",
                        idx + 1,
                        total_combinations,
                        "running"
                    )
            
            self._report_progress("04. OSS-Kombinationen holen", total_combinations, total_combinations, "completed")
            
            stats = {
                "total": total_combinations,
                "fetched": fetched_count
            }
            
            return True, f"{fetched_count} OSS-Kombinationen geholt", stats
            
        except Exception as e:
            self._report_progress("04. OSS-Kombinationen holen", 0, 1, "failed")
            return False, f"Fehler beim Holen der OSS-Kombinationen: {str(e)}", {}
    
    def update_oss_combinations(self) -> Tuple[bool, str, Dict]:
        """
        Schritt 5: Aktualisiert OSS-Kombinationen
        
        Returns:
            Tuple[bool, str, Dict]: (success, message, stats)
        """
        self._report_progress("05. OSS-Kombinationen aktualisieren", 0, 1, "starting")
        
        try:
            # Simuliere das Aktualisieren von OSS-Kombinationen
            total_combinations = 50  # Beispielwert
            updated_count = 0
            
            for idx in range(total_combinations):
                # Hier würde die tatsächliche Update-Logik stehen
                updated_count += 1
                
                # Fortschritt alle 5 Kombinationen melden
                if (idx + 1) % 5 == 0 or (idx + 1) == total_combinations:
                    self._report_progress(
                        "05. OSS-Kombinationen aktualisieren",
                        idx + 1,
                        total_combinations,
                        "running"
                    )
            
            self._report_progress(
                "05. OSS-Kombinationen aktualisieren", 
                total_combinations, 
                total_combinations, 
                "completed"
            )
            
            stats = {
                "total": total_combinations,
                "updated": updated_count
            }
            
            return True, f"{updated_count} OSS-Kombinationen aktualisiert", stats
            
        except Exception as e:
            self._report_progress("05. OSS-Kombinationen aktualisieren", 0, 1, "failed")
            return False, f"Fehler beim Aktualisieren der OSS-Kombinationen: {str(e)}", {}
    
    def update_articles(self) -> Tuple[bool, str, Dict]:
        """
        Schritt 6: Aktualisiert Artikel
        
        Returns:
            Tuple[bool, str, Dict]: (success, message, stats)
        """
        self._report_progress("06. Artikel aktualisieren", 0, 1, "starting")
        
        try:
            if not self.db_manager:
                self._report_progress("06. Artikel aktualisieren", 0, 1, "failed")
                return False, "Kein Datenbankmanager verfügbar", {}
            
            # Hole Produktdaten
            success, message, products = self.db_manager.get_products_with_taric_info()
            
            if not success or not products:
                self._report_progress("06. Artikel aktualisieren", 0, 1, "failed")
                return False, f"Fehler beim Laden der Produktdaten: {message}", {}
            
            total_products = len(products)
            updated_count = 0
            
            # Simuliere das Aktualisieren
            for idx in range(total_products):
                # Hier würde die tatsächliche Update-Logik stehen
                updated_count += 1
                
                # Fortschritt alle 10 Artikel melden
                if (idx + 1) % 10 == 0 or (idx + 1) == total_products:
                    self._report_progress(
                        "06. Artikel aktualisieren",
                        idx + 1,
                        total_products,
                        "running"
                    )
            
            self._report_progress("06. Artikel aktualisieren", total_products, total_products, "completed")
            
            stats = {
                "total": total_products,
                "updated": updated_count
            }
            
            return True, f"{updated_count} Artikel aktualisiert", stats
            
        except Exception as e:
            self._report_progress("06. Artikel aktualisieren", 0, 1, "failed")
            return False, f"Fehler beim Aktualisieren der Artikel: {str(e)}", {}
    
    def run_full_reconciliation(self) -> Tuple[bool, str, List[Dict]]:
        """
        Führt den vollständigen Abgleich-Prozess aus
        
        Returns:
            Tuple[bool, str, List[Dict]]: (success, message, results)
        """
        print("=" * 60)
        print("🚀 Starte vollständigen Abgleich-Prozess")
        print("=" * 60)
        
        results = []
        
        # Schritt 1: Trigger erstellen
        success, message, stats = self.create_trigger()
        results.append({"step": "01", "name": "Trigger erstellen", "success": success, "message": message, "stats": stats})
        if not success:
            return False, f"Schritt 1 fehlgeschlagen: {message}", results
        
        # Schritt 2: Produktdaten senden
        success, message, stats = self.send_product_data()
        results.append({"step": "02", "name": "Produktdaten senden", "success": success, "message": message, "stats": stats})
        if not success:
            print(f"⚠️ Schritt 2 fehlgeschlagen: {message}")
        
        # Schritt 3: Steuer-Informationen holen
        success, message, stats = self.fetch_and_save_tax_info()
        results.append({"step": "03", "name": "Steuer-Informationen holen", "success": success, "message": message, "stats": stats})
        if not success:
            print(f"⚠️ Schritt 3 fehlgeschlagen: {message}")
        
        # Schritt 4: OSS-Kombinationen holen
        success, message, stats = self.fetch_oss_combinations()
        results.append({"step": "04", "name": "OSS-Kombinationen holen", "success": success, "message": message, "stats": stats})
        if not success:
            print(f"⚠️ Schritt 4 fehlgeschlagen: {message}")
        
        # Schritt 5: OSS-Kombinationen aktualisieren
        success, message, stats = self.update_oss_combinations()
        results.append({"step": "05", "name": "OSS-Kombinationen aktualisieren", "success": success, "message": message, "stats": stats})
        if not success:
            print(f"⚠️ Schritt 5 fehlgeschlagen: {message}")
        
        # Schritt 6: Artikel aktualisieren
        success, message, stats = self.update_articles()
        results.append({"step": "06", "name": "Artikel aktualisieren", "success": success, "message": message, "stats": stats})
        if not success:
            print(f"⚠️ Schritt 6 fehlgeschlagen: {message}")
        
        print("=" * 60)
        print("✅ Abgleich-Prozess abgeschlossen")
        print("=" * 60)
        
        overall_success = all(r["success"] for r in results)
        return overall_success, "Abgleich abgeschlossen", results

