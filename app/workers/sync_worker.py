"""
Worker für JTL zu n8n Synchronisation
Background-Thread für OSS-Abgleich
"""

from PySide6.QtCore import QThread, Signal
import sys
import os


class JTLToN8nSyncWorker(QThread):
    """Worker-Thread für JTL zu n8n Synchronisation"""
    progress = Signal(str)
    finished = Signal(bool, str, int)
    
    def __init__(self):
        super().__init__()
        self.webhook_url = "https://agentic.go-ecommerce.de/webhook-test/post_customer_product"
        self.license_number = "123456"
        self.email = "ivan.levshyn@go-ecommerce.de"
    
    def run(self):
        """Führt die Synchronisation aus"""
        try:
            # Importiere Manager
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from jtl_database_manager import JTLDatabaseManager
            from n8n_workflow_manager import N8nWorkflowManager
            
            # Schritt 1: Initialisiere JTL Database Manager
            self.progress.emit("📊 Verbinde zur JTL-Datenbank...")
            jtl_manager = JTLDatabaseManager()
            
            # Prüfe ob Credentials vorhanden sind
            if not jtl_manager.has_saved_credentials():
                self.finished.emit(False, "Keine JTL-Credentials gefunden. Bitte DB Credentials ausführen.", 0)
                return
            
            self.progress.emit("   ✓ Verbindung hergestellt")
            
            # Schritt 2: Hole Produktdaten von JTL
            self.progress.emit("📤 Lade Produktdaten von JTL-Datenbank...")
            success, message, products = jtl_manager.get_products_with_taric_info()
            
            if not success or not products:
                self.finished.emit(False, f"Fehler beim Laden der Produktdaten: {message}", 0)
                return
            
            self.progress.emit(f"   ✓ {message}")
            product_count = len(products)
            
            # Schritt 3: Sende Daten an n8n
            self.progress.emit("📤 Sende Daten an n8n Webhook...")
            n8n_manager = N8nWorkflowManager(
                workflow_url=None,
                license_number=self.license_number,
                email=self.email
            )
            
            success_send, response_message = n8n_manager.send_products_to_webhook(
                products, 
                webhook_url=self.webhook_url
            )
            
            if not success_send:
                self.finished.emit(False, f"Fehler beim Senden der Daten: {response_message}", product_count)
                return
            
            self.progress.emit(f"   ✓ Daten erfolgreich gesendet")
            
            # Erfolg
            success_message = f"Synchronisation erfolgreich abgeschlossen!\n\n{product_count} Produkte gesendet."
            self.finished.emit(True, success_message, product_count)
            
        except Exception as e:
            error_message = f"Unerwarteter Fehler: {str(e)}"
            import traceback
            print(traceback.format_exc())
            self.finished.emit(False, error_message, 0)

