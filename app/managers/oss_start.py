"""
OSS Start Manager für OSS goEcommerce
Parent-Klasse für alle OSS-Funktionen
Orchestriert: Produkte senden, Steuersätze holen, SQL-Ausführung
"""

import requests
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime
from app.config.endpoints import EndpointConfig
from app.core.logging_config import get_logger
from app.services.decrypt_service import DecryptService
from app.services.license_service import LicenseService

logger = get_logger(__name__)


class OSSStart:
    """
    Parent-Klasse für alle OSS-Funktionen.
    Orchestriert den gesamten OSS-Abgleich-Prozess.
    """
    
    def __init__(
        self,
        db_service=None,
        workflow_service=None,
        license_number: Optional[str] = None,
        email: Optional[str] = None,
        decrypt_password: Optional[str] = None
    ):
        """
        Initialisiert den OSS Start Manager.
        
        Args:
            db_service: DatabaseService Instanz
            workflow_service: WorkflowService Instanz
            license_number: Lizenznummer für API-Requests (optional, wird aus Keyring geladen falls None)
            email: E-Mail-Adresse für API-Requests (optional, wird aus Keyring geladen falls None)
            decrypt_password: Passwort für Entschlüsselung (optional, Standard: "geh31m")
            
        Raises:
            ValueError: Wenn Lizenzdaten weder übergeben noch im Keyring gefunden werden
        """
        self.db_service = db_service
        self.workflow_service = workflow_service
        self.progress_callback = None
        self.decrypted_sql_callback = None
        
        # Lade Lizenzdaten aus Keyring, falls nicht übergeben
        if license_number is None or email is None:
            try:
                license_service = LicenseService()
                loaded_license, loaded_email = license_service.load_license()
                
                if not loaded_license or not loaded_email:
                    raise ValueError(
                        "Lizenzdaten nicht gefunden! Bitte konfigurieren Sie die Lizenz über das Menü."
                    )
                
                if license_number is None:
                    license_number = loaded_license
                if email is None:
                    email = loaded_email
                    
                logger.info(f"Lizenzdaten aus Keyring geladen: {license_number[:4]}..., {email[:3]}...")
            except ValueError:
                # Re-raise ValueError (Fehler beim Laden aus Keyring)
                raise
            except Exception as e:
                logger.error(f"Fehler beim Laden der Lizenzdaten aus Keyring: {e}")
                raise ValueError(
                    f"Fehler beim Laden der Lizenzdaten aus Keyring: {str(e)}. "
                    "Bitte konfigurieren Sie die Lizenz über das Menü."
                )
        
        # Prüfe ob beide Werte vorhanden sind
        if not license_number or not email:
            raise ValueError(
                "Lizenzdaten fehlen! Bitte konfigurieren Sie die Lizenz über das Menü."
            )
        
        self.license_number = license_number
        self.email = email
        
        # Decrypt Service für Entschlüsselung
        self.decrypt_service = DecryptService(default_password=decrypt_password or "geh31m")
        
        # Session für HTTP-Requests
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'OSS-goEcommerce/1.0.0',
            'X-License-Number': license_number,
            'X-License-Email': email,
            'X-App-Version': '1.0.0',
            'X-Timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"OSSStart initialisiert - License: {license_number[:4]}..., Email: {email[:3]}...")
    
    def set_progress_callback(self, callback: Callable):
        """Setzt eine Callback-Funktion für Fortschritts-Updates"""
        self.progress_callback = callback
    
    def set_decrypted_sql_callback(self, callback: Callable):
        """Setzt eine Callback-Funktion für entschlüsseltes SQL"""
        self.decrypted_sql_callback = callback
    
    def _report_progress(self, message: str, step: int = None, total: int = None):
        """Meldet den aktuellen Fortschritt"""
        if self.progress_callback:
            self.progress_callback(message, step, total)
        logger.info(message)
    
    def get_tax_rates(self) -> Tuple[bool, str, str]:
        """
        Holt verschlüsselte Steuersätze über GET v1/tax-rates Endpoint und entschlüsselt sie.
        
        Returns:
            Tuple[bool, decrypted_sql, message]: (success, decrypted_sql_text, message)
        """
        self._report_progress("📊 Hole aktuelle Steuersätze...")
        
        try:
            endpoint_url = EndpointConfig.get_endpoint("tax_rates")
            logger.info(f"Rufe Tax-Rates Endpoint auf: {endpoint_url}")
            
            response = self.session.get(endpoint_url, timeout=30)
            
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Fehler beim Abrufen der Steuersätze: {error_msg}")
                self._report_progress(f"   ❌ Fehler: {error_msg}")
                return False, "", error_msg
            
            # Schritt 1: Hole verschlüsselte Daten (n8n-Format)
            try:
                response_data = response.json()
                logger.info(f"Verschlüsselte Daten erhalten: {type(response_data)}")
                
                # Prüfe ob es eine Liste von Items ist (n8n-Format)
                if not isinstance(response_data, list):
                    # Versuche es als einzelnes Item zu behandeln
                    if isinstance(response_data, dict):
                        response_data = [response_data]
                    else:
                        error_msg = f"Ungültiges Datenformat: {type(response_data)}"
                        logger.error(error_msg)
                        self._report_progress(f"   ❌ {error_msg}")
                        return False, "", error_msg
                
                self._report_progress(f"   ✓ {len(response_data)} verschlüsselte Items erhalten")
                
            except Exception as e:
                error_msg = f"Fehler beim Parsen der Response: {str(e)}"
                logger.error(error_msg)
                self._report_progress(f"   ❌ {error_msg}")
                return False, "", error_msg
            
            # Schritt 2: Entschlüsselung
            self._report_progress("🔓 Entschlüssele Daten...")
            try:
                decrypted_text = self.decrypt_service.decrypt_from_n8n_format(
                    response_data,
                    self.decrypt_service.default_password
                )
                
                if not decrypted_text or not decrypted_text.strip():
                    error_msg = "Entschlüsselte Daten sind leer"
                    logger.error(error_msg)
                    self._report_progress(f"   ❌ {error_msg}")
                    return False, "", error_msg
                
                logger.info(f"Entschlüsselung erfolgreich: {len(decrypted_text)} Zeichen")
                self._report_progress(f"   ✓ Entschlüsselung erfolgreich ({len(decrypted_text)} Zeichen)")
                
            except Exception as e:
                error_msg = f"Fehler bei Entschlüsselung: {str(e)}"
                logger.error(error_msg)
                self._report_progress(f"   ❌ {error_msg}")
                return False, "", error_msg
            
            # Schritt 3: SQL für Ausführung formatieren
            self._report_progress("📝 Formatiere SQL...")
            formatted_sql = self.decrypt_service.format_sql_for_execution(decrypted_text)
            
            if not formatted_sql or not formatted_sql.strip():
                error_msg = "Formatierte SQL-Daten sind leer"
                logger.error(error_msg)
                self._report_progress(f"   ❌ {error_msg}")
                return False, "", error_msg
            
            logger.info(f"SQL formatiert: {len(formatted_sql)} Zeichen")
            self._report_progress(f"   ✓ SQL formatiert ({len(formatted_sql)} Zeichen)")
            
            # Signal für entschlüsseltes SQL senden (falls Callback vorhanden)
            if self.decrypted_sql_callback:
                try:
                    self.decrypted_sql_callback(formatted_sql)
                    logger.info("decrypted_sql_callback aufgerufen")
                except Exception as e:
                    logger.error(f"Fehler beim Aufruf von decrypted_sql_callback: {e}")
            
            return True, formatted_sql, "Steuersätze erfolgreich geholt und entschlüsselt"
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Request-Fehler: {str(e)}"
            logger.error(f"Fehler beim Abrufen der Steuersätze: {error_msg}")
            self._report_progress(f"   ❌ {error_msg}")
            return False, "", error_msg
        except Exception as e:
            error_msg = f"Unerwarteter Fehler: {str(e)}"
            logger.error(f"Fehler beim Abrufen der Steuersätze: {error_msg}")
            self._report_progress(f"   ❌ {error_msg}")
            return False, "", error_msg
    
    def execute_tax_rates_sql(self, decrypted_sql: str) -> Tuple[bool, str, Optional[str]]:
        """
        Führt entschlüsseltes SQL Statement aus, um Steuersätze in die Datenbank zu schreiben.
        
        Args:
            decrypted_sql: Entschlüsseltes SQL-Statement (bereits formatiert)
            
        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, sql_statement)
        """
        self._report_progress("💾 Führe SQL Statement aus...")
        
        try:
            if not self.db_service:
                return False, "Kein DatabaseService verfügbar", None
            
            if not self.db_service.has_saved_credentials():
                return False, "Keine Datenbankverbindung konfiguriert", None
            
            if not decrypted_sql or not decrypted_sql.strip():
                return False, "SQL-Statement ist leer", None
            
            # Optional: Trigger-Struktur korrigieren (falls nötig)
            corrected_sql = self.decrypt_service.fix_trigger_structure(decrypted_sql)
            
            # Prüfe DB-Verbindung
            success_test, message_test = self.db_service.test_connection()
            if not success_test:
                return False, f"Datenbankverbindung fehlgeschlagen: {message_test}", corrected_sql
            
            # Führe SQL aus
            logger.info(f"Führe SQL aus ({len(corrected_sql)} Zeichen):\n{corrected_sql[:500]}...")
            
            success, message, results = self.db_service.execute_query(corrected_sql)
            
            if success:
                self._report_progress(f"   ✓ SQL erfolgreich ausgeführt: {message}")
                return True, message, corrected_sql
            else:
                self._report_progress(f"   ❌ SQL-Fehler: {message}")
                return False, message, corrected_sql
                
        except Exception as e:
            error_msg = f"Fehler beim Ausführen des SQL: {str(e)}"
            logger.error(error_msg)
            self._report_progress(f"   ❌ {error_msg}")
            # Gib das SQL zurück, auch bei Exception, damit es angezeigt werden kann
            corrected_sql = self.decrypt_service.fix_trigger_structure(decrypted_sql) if decrypted_sql else None
            return False, error_msg, corrected_sql
    
    def send_products(self, products: List[Dict], webhook_url: Optional[str] = None) -> Tuple[bool, str]:
        """
        Sendet Produkte an den n8n Webhook.
        
        Args:
            products: Liste von Produktdaten
            webhook_url: Webhook URL (optional, verwendet Standard wenn None)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        self._report_progress(f"📤 Sende {len(products)} Produkte...")
        
        try:
            if not webhook_url:
                webhook_url = EndpointConfig.get_endpoint("webhook_post_customer_product")
            
            if self.workflow_service:
                success, message = self.workflow_service.send_products_to_webhook(products, webhook_url)
            else:
                # Fallback: Direkter Request
                success, message = self._send_products_direct(products, webhook_url)
            
            if success:
                self._report_progress(f"   ✓ Produkte erfolgreich gesendet: {message}")
            else:
                self._report_progress(f"   ❌ Fehler beim Senden: {message}")
            
            return success, message
            
        except Exception as e:
            error_msg = f"Fehler beim Senden der Produkte: {str(e)}"
            logger.error(error_msg)
            self._report_progress(f"   ❌ {error_msg}")
            return False, error_msg
    
    def _send_products_direct(self, products: List[Dict], webhook_url: str) -> Tuple[bool, str]:
        """Sendet Produkte direkt über HTTP POST"""
        try:
            sent_count = 0
            failed_count = 0
            
            for product in products:
                try:
                    data = {
                        "product_name": product.get('name', ''),
                        "ean": product.get('ean', ''),
                        "taric": product.get('taric', ''),
                        "sku": product.get('sku', ''),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    response = self.session.post(webhook_url, json=data, timeout=30)
                    
                    if response.status_code == 200:
                        sent_count += 1
                    else:
                        failed_count += 1
                        logger.warning(f"Produkt-Sendung fehlgeschlagen: HTTP {response.status_code}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Fehler beim Senden eines Produkts: {e}")
            
            if sent_count > 0:
                return True, f"{sent_count} Produkte gesendet" + (f", {failed_count} fehlgeschlagen" if failed_count > 0 else "")
            else:
                return False, f"Alle {failed_count} Produkt-Sendungen fehlgeschlagen"
                
        except Exception as e:
            return False, f"Fehler beim Senden der Produkte: {str(e)}"
    
    def run_oss_reconciliation(self) -> Tuple[bool, str, Dict]:
        """
        Führt den vollständigen OSS-Abgleich durch.
        Orchestriert alle Schritte:
        1. Produkte senden
        2. Steuersätze holen
        3. SQL ausführen
        
        Returns:
            Tuple[bool, str, Dict]: (success, message, results)
        """
        self._report_progress("🚀 Starte OSS-Abgleich...")
        
        results = {
            "products_sent": False,
            "tax_rates_fetched": False,
            "sql_executed": False,
            "product_count": 0,
            "tax_data": None,
            "sql_statement": None
        }
        
        # Schritt 1: Produkte senden (wenn verfügbar)
        if self.workflow_service or self.db_service:
            try:
                # Hole Produkte aus DB (wenn db_service verfügbar)
                products = []
                if self.db_service and self.db_service.has_saved_credentials():
                    # Lade Produkte mit TARIC-Informationen
                    success_load, message_load, products = self.db_service.get_products_with_taric_info()
                    if not success_load or not products:
                        logger.warning(f"Produkte konnten nicht geladen werden: {message_load}")
                        products = []
                
                if products:
                    success, message = self.send_products(products)
                    results["products_sent"] = success
                    results["product_count"] = len(products)
                    if not success:
                        logger.warning(f"Produkt-Sendung fehlgeschlagen: {message}")
                else:
                    logger.info("Keine Produkte zum Senden verfügbar")
                    
            except Exception as e:
                logger.error(f"Fehler beim Senden der Produkte: {e}")
        
        # Schritt 2: Steuersätze holen und entschlüsseln
        success, decrypted_sql, message = self.get_tax_rates()
        results["tax_rates_fetched"] = success
        results["decrypted_sql"] = decrypted_sql if success and decrypted_sql else None
        
        # Wenn Fehler beim Holen, aber decrypted_sql vorhanden ist, speichere es trotzdem
        if not success and decrypted_sql:
            logger.warning(f"Fehler beim Holen der Steuersätze, aber decrypted_sql vorhanden ({len(decrypted_sql)} Zeichen)")
            results["decrypted_sql"] = decrypted_sql
            results["sql_statement"] = decrypted_sql  # Speichere auch als sql_statement für Anzeige
        
        if not success:
            return False, f"OSS-Abgleich fehlgeschlagen: {message}", results
        
        # Schritt 3: SQL ausführen
        if decrypted_sql:
            success, message, sql_statement = self.execute_tax_rates_sql(decrypted_sql)
            results["sql_executed"] = success
            # SQL-Statement wird IMMER gespeichert, auch bei Fehlern, damit es angezeigt werden kann
            results["sql_statement"] = sql_statement if sql_statement else decrypted_sql
            
            logger.info(f"SQL-Ausführung: success={success}, sql_statement vorhanden={sql_statement is not None}")
            
            if not success:
                logger.warning(f"SQL-Ausführung fehlgeschlagen: {message}")
                # SQL-Statement wird trotzdem im results gespeichert, damit es angezeigt werden kann
        else:
            # Wenn decrypted_sql leer ist, aber tax_rates_fetched erfolgreich war
            # (sollte eigentlich nicht passieren, aber zur Sicherheit)
            logger.warning("decrypted_sql ist leer, obwohl tax_rates_fetched erfolgreich war")
            results["sql_executed"] = False
            results["sql_statement"] = None
        
        # Zusammenfassung
        if results["tax_rates_fetched"] and results["sql_executed"]:
            summary = f"OSS-Abgleich erfolgreich abgeschlossen!\n"
            summary += f"✓ Steuersätze geholt und entschlüsselt\n"
            summary += f"✓ SQL ausgeführt\n"
            if results["products_sent"]:
                summary += f"✓ {results['product_count']} Produkte gesendet"
            return True, summary, results
        else:
            return False, "OSS-Abgleich teilweise fehlgeschlagen", results

