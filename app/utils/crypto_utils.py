"""
Crypto Utilities für OSS goEcommerce
Verschlüsselungs- und Entschlüsselungsfunktionen für Daten von n8n API
"""

import base64
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from typing import Optional, Dict


class CryptoUtils:
    """Versorgt Verschlüsselungs- und Entschlüsselungsfunktionen"""
    
    @staticmethod
    def decrypt_text(encrypted_data: str, iv: str, key: str = "geh31m") -> Optional[str]:
        """
        Entschlüsselt Text, der mit AES-256-CBC verschlüsselt wurde
        
        Args:
            encrypted_data: Base64-kodierter verschlüsselter Text
            iv: Base64-kodierter Initialisierungsvektor
            key: Passwort für die Key-Generierung (Standard: "geh31m")
            
        Returns:
            Optional[str]: Entschlüsselter Text oder None bei Fehler
        """
        try:
            # Generiere 256-Bit Key aus Passwort
            password_hash = SHA256.new(key.encode())
            aes_key = password_hash.digest()
            
            # Decodiere IV und verschlüsselte Daten aus Base64
            decoded_iv = base64.b64decode(iv)
            decoded_encrypted = base64.b64decode(encrypted_data)
            
            # Erstelle AES-256-CBC Cipher
            cipher = AES.new(aes_key, AES.MODE_CBC, decoded_iv)
            
            # Entschlüssele
            padded_text = cipher.decrypt(decoded_encrypted)
            
            # Entferne Padding
            pad_len = padded_text[-1]
            decrypted_text = padded_text[:-pad_len]
            
            # Konvertiere bytes zu String
            return decrypted_text.decode('utf-8')
            
        except Exception as e:
            print(f"FEHLER: Entschlüsselung fehlgeschlagen: {e}")
            return None
    
    @staticmethod
    def encrypt_text(text: str, key: str = "geh31m") -> Dict[str, str]:
        """
        Verschlüsselt Text mit AES-256-CBC
        
        Args:
            text: Zu verschlüsselnder Text
            key: Passwort für die Key-Generierung (Standard: "geh31m")
            
        Returns:
            Dict[str, str]: Dictionary mit 'iv' und 'encrypted' (beide base64-kodiert)
        """
        try:
            from Crypto.Random import get_random_bytes
            
            # Generiere 256-Bit Key aus Passwort
            password_hash = SHA256.new(key.encode())
            aes_key = password_hash.digest()
            
            # Generiere Initialisierungsvektor (IV)
            iv = get_random_bytes(16)
            
            # Erstelle AES-256-CBC Cipher
            cipher = AES.new(aes_key, AES.MODE_CBC, iv)
            
            # Padding auf 16-Byte-Blöcke
            pad_len = 16 - len(text.encode()) % 16
            padded = text + chr(pad_len) * pad_len
            
            # Verschlüssele
            encrypted = cipher.encrypt(padded.encode())
            
            # Rückgabe als base64-kodierte Strings
            return {
                "iv": base64.b64encode(iv).decode(),
                "encrypted": base64.b64encode(encrypted).decode()
            }
            
        except Exception as e:
            print(f"FEHLER: Verschlüsselung fehlgeschlagen: {e}")
            return None
    
    @staticmethod
    def decrypt_sql_from_api(response_data: Dict) -> Optional[str]:
        """
        Entschlüsselt SQL aus API-Response
        
        Args:
            response_data: Dictionary mit 'iv' und 'encrypted' Feldern
            
        Returns:
            Optional[str]: Entschlüsselter SQL-String oder None bei Fehler
        """
        try:
            iv = response_data.get("iv")
            encrypted = response_data.get("encrypted")
            
            if not iv or not encrypted:
                print("FEHLER: IV oder encrypted Daten fehlen in Response")
                return None
            
            return CryptoUtils.decrypt_text(encrypted, iv)
            
        except Exception as e:
            print(f"FEHLER: Entschlüsselung von API-Response fehlgeschlagen: {e}")
            return None


def decrypt_test():
    """Test-Funktion für die Entschlüsselung"""
    # Beispiel-Daten vom Benutzer
    test_iv = "brfQ8uEjEuMC67+O7IzipA=="
    test_encrypted = ""  # Hier müsste der verschlüsselte SQL-String sein
    
    print("=" * 60)
    print("🧪 Test: SQL-Entschlüsselung")
    print("=" * 60)
    print()
    print(f"IV: {test_iv}")
    print(f"Encrypted: {test_encrypted}")
    print()
    
    if test_encrypted:
        result = CryptoUtils.decrypt_text(test_encrypted, test_iv)
        
        if result:
            print("✅ Entschlüsselung erfolgreich!")
            print(f"SQL: {result}")
        else:
            print("❌ Entschlüsselung fehlgeschlagen")
    else:
        print("⚠️ Keine verschlüsselten Daten zum Testen")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    decrypt_test()

