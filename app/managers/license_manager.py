"""
License Manager für OSS goEcommerce
Verwaltet Lizenz-Informationen im Keyring und JSON-Dateien
"""

import os
import json
import keyring
from app.core.debug_manager import debug_print
from app.core.error_handler import handle_error, ErrorCode
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class LicenseManager:
    """Verwaltet die Lizenz-Informationen im Keyring"""
    
    def __init__(self):
        self.service_name = "OSS_goEcommerce"
        self.license_file = "license_config.json"
    
    def save_license(self, license_number, email):
        """
        Speichert Lizenzdaten im Keyring und JSON.
        
        WICHTIG: Alte Lizenzdaten werden automatisch gelöscht/überschrieben.
        Es kann nur eine Lizenz gleichzeitig vorhanden sein.
        """
        try:
            # Lösche zuerst alte Lizenzdaten (falls vorhanden)
            try:
                keyring.delete_password(self.service_name, "license_number")
            except keyring.errors.PasswordDeleteError:
                pass  # Keine alten Daten vorhanden, ist OK
            
            try:
                keyring.delete_password(self.service_name, "email")
            except keyring.errors.PasswordDeleteError:
                pass  # Keine alten Daten vorhanden, ist OK
            
            # Lösche alte JSON-Datei (wird durch neue überschrieben)
            if os.path.exists(self.license_file):
                try:
                    os.remove(self.license_file)
                except Exception:
                    pass  # Ignoriere Fehler beim Löschen
            
            # Speichere neue Lizenznummer im Keyring
            debug_print(f"DEBUG save_license: Speichere im Keyring - License: {license_number}, Email: {email}")
            keyring.set_password(self.service_name, "license_number", license_number)
            
            # Speichere neue E-Mail im Keyring
            keyring.set_password(self.service_name, "email", email)
            
            # SOFORT verifiziere dass die Daten gespeichert wurden
            verify_license = keyring.get_password(self.service_name, "license_number")
            verify_email = keyring.get_password(self.service_name, "email")
            debug_print(f"DEBUG save_license: Verifizierung - License: {verify_license}, Email: {verify_email}")
            if verify_license != license_number or verify_email != email:
                debug_print(f"FEHLER: Daten konnten nicht korrekt im Keyring gespeichert werden!")
                debug_print(f"  Erwartet: License={license_number}, Email={email}")
                debug_print(f"  Gefunden: License={verify_license}, Email={verify_email}")
            
            # Speichere Metadaten in JSON
            from datetime import datetime
            config = {
                "license_number": license_number,
                "email": email,
                "saved_at": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            try:
                with open(self.license_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
            except (IOError, OSError) as e:
                error = handle_error(
                    e,
                    error_code=ErrorCode.CONFIG_FILE_NOT_FOUND,
                    context={'operation': 'save_license', 'file': self.license_file},
                    log_level="warning"
                )
                debug_print(f"Warnung: Konnte JSON-Datei nicht speichern: {error.message}")
                logger.warning(f"Konnte JSON-Datei nicht speichern: {error.message}")
                # Keyring-Speicherung war erfolgreich, also ist das OK
            except json.JSONEncodeError as e:
                error = handle_error(
                    e,
                    error_code=ErrorCode.CONFIG_INVALID_JSON,
                    context={'operation': 'save_license', 'file': self.license_file},
                    log_level="warning"
                )
                debug_print(f"Warnung: JSON-Encode-Fehler: {error.message}")
                logger.warning(f"JSON-Encode-Fehler: {error.message}")
                # Keyring-Speicherung war erfolgreich, also ist das OK
            
            return True
        except keyring.errors.KeyringError as e:
            error = handle_error(
                e,
                error_code=ErrorCode.CONFIG_KEYRING_ERROR,
                context={'operation': 'save_license'},
                log_level="error"
            )
            debug_print(f"Fehler beim Speichern der Lizenz: {error.message}")
            logger.error(f"Keyring-Fehler beim Speichern der Lizenz: {error.message}", exc_info=True)
            return False
        except Exception as e:
            error = handle_error(
                e,
                error_code=ErrorCode.GEN_UNEXPECTED_ERROR,
                context={'operation': 'save_license'},
                log_level="error"
            )
            debug_print(f"Fehler beim Speichern der Lizenz: {error.message}")
            logger.error(f"Unerwarteter Fehler beim Speichern der Lizenz: {error.message}", exc_info=True)
            return False
    
    def load_license(self):
        """Lädt Lizenzdaten aus Keyring"""
        try:
            license_number = keyring.get_password(self.service_name, "license_number")
            email = keyring.get_password(self.service_name, "email")
            
            # DEBUG: Zeige was geladen wurde
            debug_print(f"DEBUG load_license (Keyring):")
            debug_print(f"  Service Name: {self.service_name}")
            debug_print(f"  License Number: {license_number}")
            debug_print(f"  Email: {email}")
            
            if license_number and email:
                return license_number, email
            else:
                debug_print(f"DEBUG: Unvollständige Daten - License: {license_number is not None}, Email: {email is not None}")
                return None, None
        except keyring.errors.KeyringError as e:
            error = handle_error(
                e,
                error_code=ErrorCode.CONFIG_KEYRING_ERROR,
                context={'operation': 'load_license'},
                log_level="error"
            )
            debug_print(f"Keyring-Fehler beim Laden der Lizenz: {error.message}")
            logger.error(f"Keyring-Fehler beim Laden der Lizenz: {error.message}", exc_info=True)
            return None, None
        except Exception as e:
            error = handle_error(
                e,
                error_code=ErrorCode.GEN_UNEXPECTED_ERROR,
                context={'operation': 'load_license'},
                log_level="error"
            )
            debug_print(f"Fehler beim Laden der Lizenz: {error.message}")
            logger.error(f"Unerwarteter Fehler beim Laden der Lizenz: {error.message}", exc_info=True)
            import traceback
            traceback.print_exc()
            return None, None
    
    def has_license(self):
        """Prüft ob Lizenzdaten vorhanden sind"""
        license_number, email = self.load_license()
        return license_number is not None and email is not None
    
    def clear_license(self):
        """Löscht alle Lizenzdaten"""
        try:
            keyring.delete_password(self.service_name, "license_number")
            keyring.delete_password(self.service_name, "email")
            
            if os.path.exists(self.license_file):
                os.remove(self.license_file)
            
            return True
        except keyring.errors.KeyringError as e:
            error = handle_error(
                e,
                error_code=ErrorCode.CONFIG_KEYRING_ERROR,
                context={'operation': 'clear_license'},
                log_level="error"
            )
            debug_print(f"Keyring-Fehler beim Löschen der Lizenz: {error.message}")
            logger.error(f"Keyring-Fehler beim Löschen der Lizenz: {error.message}", exc_info=True)
            return False
        except Exception as e:
            error = handle_error(
                e,
                error_code=ErrorCode.GEN_UNEXPECTED_ERROR,
                context={'operation': 'clear_license'},
                log_level="error"
            )
            debug_print(f"Fehler beim Löschen der Lizenz: {error.message}")
            logger.error(f"Unerwarteter Fehler beim Löschen der Lizenz: {error.message}", exc_info=True)
            return False

