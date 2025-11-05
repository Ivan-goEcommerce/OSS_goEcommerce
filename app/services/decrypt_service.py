"""
Decrypt Service für OSS goEcommerce
Service-Klasse für Entschlüsselung von n8n-Format Daten
"""

from typing import List, Optional, Dict, Any
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Import decrypt_from_n8n_format wenn verfügbar
try:
    from app.utils.decrypt_utils import decrypt_from_n8n_format
    DECRYPT_UTILS_AVAILABLE = True
except ImportError:
    # Fallback wenn decrypt_utils nicht verfügbar ist
    DECRYPT_UTILS_AVAILABLE = False
    logger.warning("decrypt_utils nicht verfügbar - verwende Fallback")


class DecryptService:
    """
    Service-Klasse für Entschlüsselung.
    Wrapper um decrypt_from_n8n_format für einfache Integration.
    """
    
    def __init__(self, default_password: str = "geh31m"):
        """
        Initialisiert den Decrypt Service.
        
        Args:
            default_password: Standard-Passwort für Entschlüsselung (Standard: "geh31m")
        """
        self.default_password = default_password
        logger.debug("DecryptService initialisiert")
    
    def decrypt_from_n8n_format(
        self, 
        items: List[Dict], 
        password: Optional[str] = None
    ) -> str:
        """
        Entschlüsselt Daten aus n8n-Format.
        
        Args:
            items: Liste von n8n-Items mit verschlüsselten Daten
                   Format: [{"json": {"iv": "...", "encrypted": "..."}}, ...]
            password: Passwort für Entschlüsselung (optional, verwendet default_password wenn nicht angegeben)
            
        Returns:
            Entschlüsselter Klartext als String
            
        Raises:
            ImportError: Wenn decrypt_utils nicht verfügbar ist
            ValueError: Bei ungültigen Eingabedaten oder fehlenden Feldern
        """
        if not DECRYPT_UTILS_AVAILABLE:
            raise ImportError("decrypt_utils Modul nicht verfügbar")
        
        decrypt_password = password or self.default_password
        logger.info(f"Entschlüssele {len(items)} Items aus n8n-Format")
        
        try:
            decrypted_text = decrypt_from_n8n_format(items, decrypt_password)
            logger.info(f"Entschlüsselung erfolgreich: {len(decrypted_text)} Zeichen")
            return decrypted_text
        except ValueError as e:
            logger.error(f"Entschlüsselungsfehler: {e}")
            raise
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei Entschlüsselung: {e}")
            raise ValueError(f"Entschlüsselungsfehler: {str(e)}") from e
    
    def decrypt_text(
        self, 
        encrypted_data: str, 
        iv: str, 
        password: Optional[str] = None
    ) -> Optional[str]:
        """
        Entschlüsselt Text mit AES-256-CBC.
        
        Args:
            encrypted_data: Base64-kodierter verschlüsselter Text
            iv: Base64-kodierter Initialisierungsvektor (16 Bytes)
            password: Passwort für Entschlüsselung (optional, Standard: "geh31m")
            
        Returns:
            Entschlüsselter Text oder None bei Fehler
        """
        import base64
        from Crypto.Cipher import AES
        from Crypto.Hash import SHA256
        
        decrypt_password = password or self.default_password
        logger.debug("Entschlüssele Text mit AES-256-CBC")
        
        try:
            # Generiere 256-Bit Key aus Passwort
            password_hash = SHA256.new(decrypt_password.encode())
            key = password_hash.digest()
            
            # Decodiere IV und verschlüsselte Daten aus Base64
            decoded_iv = base64.b64decode(iv)
            decoded_encrypted = base64.b64decode(encrypted_data)
            
            # Prüfe IV-Größe
            if len(decoded_iv) != 16:
                logger.error(f"Ungültige IV-Größe: {len(decoded_iv)} (erwartet: 16)")
                return None
            
            # Erstelle AES-256-CBC Cipher
            cipher = AES.new(key, AES.MODE_CBC, decoded_iv)
            
            # Entschlüssele
            padded_text = cipher.decrypt(decoded_encrypted)
            
            # Entferne PKCS#7 Padding
            pad_len = padded_text[-1]
            
            if pad_len < 1 or pad_len > 16:
                logger.error(f"Ungültige Padding-Länge: {pad_len}")
                return None
            
            # Prüfe Padding
            padding = padded_text[-pad_len:]
            if not all(b == pad_len for b in padding):
                logger.error("Ungültiges Padding-Format")
                return None
            
            # Entferne Padding
            decrypted_text = padded_text[:-pad_len]
            
            # Konvertiere zu String
            decrypted_str = decrypted_text.decode('utf-8')
            
            logger.debug(f"Text erfolgreich entschlüsselt: {len(decrypted_str)} Zeichen")
            return decrypted_str
            
        except Exception as e:
            logger.error(f"Fehler bei Text-Entschlüsselung: {e}")
            return None
    
    def decrypt_from_json_string(self, json_string: str, password: Optional[str] = None) -> str:
        """
        Entschlüsselt Daten aus JSON-String.
        
        Args:
            json_string: JSON-String mit n8n-Items Format
                         Beispiel: '[{"json": {"iv": "...", "encrypted": "..."}}]'
            password: Passwort für Entschlüsselung (optional, Standard: "geh31m")
            
        Returns:
            Entschlüsselter Klartext als String
            
        Raises:
            ValueError: Bei ungültigem JSON oder Entschlüsselungsfehler
        """
        import json
        
        try:
            items = json.loads(json_string)
            if not isinstance(items, list):
                raise ValueError("JSON muss eine Liste sein")
            
            return self.decrypt_from_n8n_format(items, password)
        except json.JSONDecodeError as e:
            raise ValueError(f"Ungültiges JSON-Format: {str(e)}")
    
    def set_default_password(self, password: str):
        """Setzt das Standard-Passwort"""
        self.default_password = password
        logger.info("Standard-Passwort aktualisiert")

