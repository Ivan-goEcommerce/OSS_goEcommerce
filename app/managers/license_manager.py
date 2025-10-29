"""
License Manager für OSS goEcommerce
Verwaltet Lizenz-Informationen im Keyring und JSON-Dateien
"""

import os
import json
import keyring


class LicenseManager:
    """Verwaltet die Lizenz-Informationen im Keyring"""
    
    def __init__(self):
        self.service_name = "OSS_goEcommerce"
        self.license_file = "license_config.json"
    
    def save_license(self, license_number, email):
        """Speichert Lizenzdaten im Keyring und JSON"""
        try:
            # Speichere Lizenznummer im Keyring
            keyring.set_password(self.service_name, "license_number", license_number)
            
            # Speichere E-Mail im Keyring
            keyring.set_password(self.service_name, "email", email)
            
            # Speichere Metadaten in JSON
            config = {
                "license_number": license_number,
                "email": email,
                "saved_at": str(os.path.getctime(__file__)),
                "version": "1.0"
            }
            
            with open(self.license_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Fehler beim Speichern der Lizenz: {e}")
            return False
    
    def load_license(self):
        """Lädt Lizenzdaten aus Keyring"""
        try:
            license_number = keyring.get_password(self.service_name, "license_number")
            email = keyring.get_password(self.service_name, "email")
            
            if license_number and email:
                return license_number, email
            else:
                return None, None
        except Exception as e:
            print(f"Fehler beim Laden der Lizenz: {e}")
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
        except Exception as e:
            print(f"Fehler beim Löschen der Lizenz: {e}")
            return False
    
    def is_license_valid(self, license_number, email):
        """Prüft ob eine Lizenz gültig ist"""
        # Für Demo-Zwecke: Lizenz ist gültig wenn beide Felder gefüllt sind
        return bool(license_number and email and len(license_number) > 3 and '@' in email)
