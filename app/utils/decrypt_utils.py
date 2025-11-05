
"""
Decrypt Utils für OSS goEcommerce
Entschlüsselungsfunktionen für n8n-Format Daten
Kompatibel mit AES-256-CBC Verschlüsselung (Key: geh31m)
"""

import base64
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from typing import List, Dict


def decrypt_from_n8n_format(items: List[Dict], password: str = "geh31m") -> str:
    """
    Entschlüsselt Daten aus n8n-Format.
    
    Kompatibel mit dem n8n Verschlüsselungs-Code:
    - Key: SHA256(password) -> 256-Bit Key
    - IV: 16 Bytes, Base64-kodiert (wird jedes Mal neu generiert)
    - AES-256-CBC Verschlüsselung
    - PKCS#7 Padding (pad_len als letztes Byte)
    
    Args:
        items: Liste von n8n-Items mit verschlüsselten Daten
               Format: [{"json": {"iv": "...", "encrypted": "..."}}, ...]
        password: Passwort für Entschlüsselung (Standard: "geh31m")
        
    Returns:
        str: Entschlüsselter Klartext als String
        
    Raises:
        ValueError: Bei ungültigen Eingabedaten oder fehlenden Feldern
    """
    if not items:
        raise ValueError("Items-Liste ist leer")
    
    if not password:
        raise ValueError("Passwort darf nicht leer sein")
    
    try:
        # Generiere 256-Bit Key aus Passwort (gleich wie beim Verschlüsseln)
        # password = item.get("constants", {}).get("key")  -> "geh31m"
        password_hash = SHA256.new(password.encode())
        key = password_hash.digest()
        
        decrypted_parts = []
        
        # Verarbeite jedes Item in der Liste
        for item in items:
            if not isinstance(item, dict):
                raise ValueError(f"Item ist kein Dictionary: {type(item)}")
            
            # Extrahiere JSON-Daten aus Item
            # Unterstützt beide Formate:
            # 1. n8n-Format: {"json": {"iv": "...", "encrypted": "..."}}
            # 2. Direktes Format: {"iv": "...", "encrypted": "..."}
            if "json" in item:
                json_data = item.get("json", {})
            else:
                # Direktes Format - IV und encrypted sind im Item selbst
                json_data = item
            
            if not isinstance(json_data, dict):
                raise ValueError(f"Daten sind kein Dictionary: {type(json_data)}")
            
            # Hole IV und verschlüsselte Daten
            iv_b64 = json_data.get("iv")
            encrypted_b64 = json_data.get("encrypted")
            
            if not iv_b64:
                raise ValueError("IV fehlt im Item")
            if not encrypted_b64:
                raise ValueError("encrypted Daten fehlen im Item")
            
            # Decodiere IV und verschlüsselte Daten aus Base64
            try:
                decoded_iv = base64.b64decode(iv_b64)
                decoded_encrypted = base64.b64decode(encrypted_b64)
            except Exception as e:
                raise ValueError(f"Base64-Decodierung fehlgeschlagen: {str(e)}")
            
            # Prüfe IV-Größe (sollte 16 Bytes sein)
            if len(decoded_iv) != 16:
                raise ValueError(f"Ungültige IV-Größe: {len(decoded_iv)} (erwartet: 16)")
            
            # Erstelle AES-256-CBC Cipher (gleich wie beim Verschlüsseln)
            cipher = AES.new(key, AES.MODE_CBC, decoded_iv)
            
            # Entschlüssele
            padded_text = cipher.decrypt(decoded_encrypted)
            
            # Entferne PKCS#7 Padding
            # Padding-Länge ist im letzten Byte gespeichert
            pad_len = padded_text[-1]
            
            # Validiere Padding-Länge (sollte zwischen 1 und 16 sein)
            if pad_len < 1 or pad_len > 16:
                raise ValueError(f"Ungültige Padding-Länge: {pad_len}")
            
            # Prüfe ob alle Padding-Bytes gleich sind
            padding = padded_text[-pad_len:]
            if not all(b == pad_len for b in padding):
                raise ValueError("Ungültiges Padding-Format")
            
            # Entferne Padding
            decrypted_text = padded_text[:-pad_len]
            
            # Konvertiere bytes zu String und füge zu Ergebnis hinzu
            decrypted_str = decrypted_text.decode('utf-8')
            decrypted_parts.append(decrypted_str)
        
        # Verbinde alle entschlüsselten Teile
        result = "".join(decrypted_parts)
        
        return result
        
    except UnicodeDecodeError as e:
        raise ValueError(f"UTF-8 Decodierung fehlgeschlagen: {str(e)}")
    except Exception as e:
        # Alle anderen Fehler als ValueError weitergeben
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Entschlüsselungsfehler: {str(e)}") from e


def decrypt_single_item(item: Dict, password: str = "geh31m") -> str:
    """
    Entschlüsselt ein einzelnes n8n-Item.
    
    Args:
        item: n8n-Item mit verschlüsselten Daten
              Format: {"json": {"iv": "...", "encrypted": "..."}}
        password: Passwort für Entschlüsselung (Standard: "geh31m")
        
    Returns:
        str: Entschlüsselter Klartext als String
        
    Raises:
        ValueError: Bei ungültigen Eingabedaten oder fehlenden Feldern
    """
    return decrypt_from_n8n_format([item], password)

