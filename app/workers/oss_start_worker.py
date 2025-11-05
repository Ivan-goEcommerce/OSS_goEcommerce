"""
Worker für OSS Start Abgleich
Background-Thread für vollständigen OSS-Abgleich mit OSSStart-Klasse
"""

from PySide6.QtCore import QThread, Signal
import sys
import os
from app.managers.oss_start import OSSStart
from app.services.database_service import DatabaseService
from app.services.workflow_service import WorkflowService
from app.services.license_service import LicenseService
from app.core.debug_manager import debug_print


class OSSStartWorker(QThread):
    """Worker-Thread für OSS Start Abgleich"""
    progress = Signal(str, int, int)  # message, step, total
    finished = Signal(bool, str, dict)  # success, message, results
    decrypted_sql_ready = Signal(str)  # Signal für entschlüsseltes SQL
    
    def __init__(self):
        super().__init__()
        self.license_number = None
        self.email = None
        
        # Lade Lizenzdaten aus Keyring (muss vorhanden sein, sonst Fehler)
        self._load_license_from_keyring()
    
    def _load_license_from_keyring(self):
        """Lädt Lizenzdaten aus Keyring - wirft Fehler wenn nicht gefunden"""
        try:
            license_service = LicenseService()
            license_number, email = license_service.load_license()
            
            if not license_number or not email:
                raise ValueError(
                    "Lizenzdaten nicht gefunden! Bitte konfigurieren Sie die Lizenz über das Menü."
                )
            
            debug_print(f"INFO: Lizenzdaten aus Keyring geladen: {license_number[:4]}..., {email[:3]}...")
            self.license_number = license_number
            self.email = email
        except ValueError:
            # Re-raise ValueError (Fehler beim Laden aus Keyring)
            raise
        except Exception as e:
            debug_print(f"FEHLER beim Laden der Lizenzdaten: {e}")
            raise ValueError(
                f"Fehler beim Laden der Lizenzdaten aus Keyring: {str(e)}. "
                "Bitte konfigurieren Sie die Lizenz über das Menü."
            )
    
    def run(self):
        """Führt den OSS-Abgleich aus"""
        try:
            # Schritt 1: Initialisiere Services
            self.progress.emit("🔧 Initialisiere Services...", 0, 5)
            
            # Database Service
            db_service = DatabaseService()
            if not db_service.has_saved_credentials():
                self.finished.emit(False, "Keine JTL-Credentials gefunden. Bitte DB Credentials ausführen.", {})
                return
            
            # Teste DB-Verbindung
            success, message = db_service.test_connection()
            if not success:
                self.finished.emit(False, f"Datenbankverbindung fehlgeschlagen: {message}", {})
                return
            
            self.progress.emit("   ✓ Datenbankverbindung hergestellt", 1, 5)
            
            # Workflow Service
            workflow_service = WorkflowService(
                license_number=self.license_number,
                email=self.email
            )
            self.progress.emit("   ✓ Workflow Service initialisiert", 2, 5)
            
            # Schritt 2: Initialisiere OSSStart
            self.progress.emit("🚀 Initialisiere OSS Start...", 2, 5)
            oss_start = OSSStart(
                db_service=db_service,
                workflow_service=workflow_service,
                license_number=self.license_number,
                email=self.email
            )
            
            # Setze Progress-Callback
            def progress_callback(message, step=None, total=None):
                current_step = step if step is not None else 3
                total_steps = total if total is not None else 5
                self.progress.emit(message, current_step, total_steps)
            
            oss_start.set_progress_callback(progress_callback)
            
            # Setze Callback für entschlüsseltes SQL
            def decrypted_sql_callback(decrypted_sql: str):
                self.decrypted_sql_ready.emit(decrypted_sql)
            
            oss_start.set_decrypted_sql_callback(decrypted_sql_callback)
            
            # Schritt 3: Führe OSS-Abgleich durch
            self.progress.emit("🔄 Führe OSS-Abgleich durch...", 3, 5)
            success, message, results = oss_start.run_oss_reconciliation()
            
            # Schritt 4: Zusammenfassung
            self.progress.emit("📊 Erstelle Zusammenfassung...", 4, 5)
            
            if success:
                # Erfolg
                summary = message
                if results.get("product_count", 0) > 0:
                    summary += f"\n\n{results['product_count']} Produkte gesendet"
                if results.get("tax_data"):
                    tax_count = len(results["tax_data"]) if isinstance(results["tax_data"], list) else 1
                    summary += f"\n{tax_count} Steuersätze geholt und in DB geschrieben"
                
                self.progress.emit("   ✓ OSS-Abgleich erfolgreich abgeschlossen", 5, 5)
                self.finished.emit(True, summary, results)
            else:
                # Fehler
                error_details = []
                if not results.get("tax_rates_fetched"):
                    error_details.append("Steuersätze konnten nicht geholt werden")
                if not results.get("sql_executed"):
                    error_details.append("SQL konnte nicht ausgeführt werden")
                
                error_msg = message
                if error_details:
                    error_msg += "\n\nDetails:\n" + "\n".join(f"• {detail}" for detail in error_details)
                
                self.progress.emit("   ❌ OSS-Abgleich fehlgeschlagen", 5, 5)
                self.finished.emit(False, error_msg, results)
            
        except Exception as e:
            error_message = f"Unerwarteter Fehler: {str(e)}"
            import traceback
            debug_print(traceback.format_exc())
            self.progress.emit(f"   ❌ {error_message}", 5, 5)
            # Gib leeres dict zurück, damit keine KeyError bei Dashboard auftritt
            # Aber das SQL sollte bereits in results gespeichert sein, wenn es vorher vorhanden war
            self.finished.emit(False, error_message, {})

