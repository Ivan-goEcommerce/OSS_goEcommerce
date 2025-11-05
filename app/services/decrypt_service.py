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
    
    def fix_trigger_structure(self, sql_text: str) -> str:
        """
        Korrigiert die Struktur eines SQL-Triggers automatisch.
        
        Hauptproblem: Nach 'AS' muss 'BEGIN' stehen, bevor andere Statements kommen.
        Oft kommt nach 'AS' direkt 'SET NOCOUNT ON;' etc. (auch in einer Zeile).
        
        Args:
            sql_text: SQL-Text mit möglicherweise fehlerhafter Trigger-Struktur
            
        Returns:
            Korrigierter SQL-Text mit korrekter Trigger-Struktur
        """
        import re
        
        if not sql_text or not sql_text.strip():
            return sql_text
        
        logger.debug("Prüfe Trigger-Struktur auf Korrekturen...")
        
        # Prüfe ob es ein CREATE TRIGGER Statement enthält
        if not re.search(r'CREATE\s+TRIGGER', sql_text, re.IGNORECASE):
            logger.debug("Kein CREATE TRIGGER gefunden - keine Korrektur nötig")
            return sql_text
        
        corrected = sql_text
        
        # Hauptproblem: Nach AS kommt direkt SET ohne BEGIN
        # Fall 1: AS gefolgt von SET in einer Zeile: "AS SET NOCOUNT ON; SET ANSI_NULLS ON; ... BEGIN ..."
        # Finde AS gefolgt von SET-Statements bis zum ersten DECLARE oder BEGIN (im Trigger-Body)
        # Pattern: AS (whitespace) SET ... (bis DECLARE oder BEGIN, aber nicht AS BEGIN)
        pattern1 = r'(\bAS\b)\s+(SET\s+[^;]+?;.*?)(?=\s+DECLARE\b|\s+BEGIN\s+DECLARE|\s+IF\b)'
        def fix_inline_set(match):
            as_keyword = match.group(1)
            set_statements = match.group(2).strip()
            
            # Teile die SET-Statements auf (bei Semikolon)
            # Füge BEGIN nach AS ein und formatierte SET-Statements
            set_lines = []
            for stmt in set_statements.split(';'):
                stmt = stmt.strip()
                if stmt and stmt.upper().startswith('SET'):
                    set_lines.append(f"    {stmt};")
            
            if set_lines:
                fixed = f"{as_keyword}\nBEGIN\n" + "\n".join(set_lines) + "\n"
                logger.info("Trigger-Struktur korrigiert: BEGIN nach AS eingefügt (Inline-SET)")
                return fixed
            return match.group(0)  # Keine Änderung wenn keine SET-Statements gefunden
        
        # Prüfe zuerst, ob bereits BEGIN nach AS vorhanden ist
        if not re.search(r'\bAS\s+BEGIN\b', corrected, re.IGNORECASE):
            # Ersetze AS SET durch AS\nBEGIN\n    SET
            corrected = re.sub(pattern1, fix_inline_set, corrected, flags=re.IGNORECASE | re.DOTALL)
        
        # Fall 2: AS am Ende einer Zeile, SET in nächster Zeile (ohne BEGIN)
        # Pattern: AS\nSET oder AS;\nSET
        pattern2 = r'(\bAS\b)\s*;?\s*\n\s*(SET\s+NOCOUNT|SET\s+ANSI)'
        def fix_multiline_set(match):
            as_keyword = match.group(1)
            set_statement = match.group(2)
            fixed = f"{as_keyword}\nBEGIN\n    {set_statement}"
            logger.info("Trigger-Struktur korrigiert: BEGIN nach AS eingefügt (Multi-Line)")
            return fixed
        
        # Ersetze nur wenn nicht bereits BEGIN vorhanden ist
        if not re.search(r'\bAS\s+BEGIN\b', corrected, re.IGNORECASE):
            corrected = re.sub(pattern2, fix_multiline_set, corrected, flags=re.IGNORECASE)
        
        # Prüfe ob ein END vor GO fehlt (für den CREATE TRIGGER Block)
        lines = corrected.split('\n')
        in_trigger = False
        trigger_start_idx = -1
        begin_count = 0
        end_count = 0
        
        for i, line in enumerate(lines):
            # Prüfe ob CREATE TRIGGER beginnt
            if re.search(r'CREATE\s+TRIGGER', line, re.IGNORECASE):
                in_trigger = True
                trigger_start_idx = i
                begin_count = 0
                end_count = 0
                continue
            
            if in_trigger:
                # Zähle BEGIN und END
                if re.search(r'\bBEGIN\b', line, re.IGNORECASE):
                    begin_count += 1
                if re.search(r'\bEND\b', line, re.IGNORECASE):
                    end_count += 1
                
                # Prüfe ob GO kommt und END fehlt
                if re.search(r'^\s*GO\s*$', line, re.IGNORECASE):
                    if begin_count > end_count:
                        # Füge END vor GO ein
                        for j in range(i - 1, trigger_start_idx, -1):
                            if lines[j].strip() and not re.search(r'^\s*GO\s*$', lines[j], re.IGNORECASE):
                                # Füge END ein
                                if lines[j].strip().endswith(';'):
                                    lines[j] = lines[j].rstrip()[:-1] + '\nEND;'
                                else:
                                    lines[j] = lines[j].rstrip() + '\nEND'
                                logger.info("Trigger-Struktur korrigiert: END vor GO eingefügt")
                                break
                    in_trigger = False
                    trigger_start_idx = -1
                    begin_count = 0
                    end_count = 0
        
        corrected = '\n'.join(lines)
        
        # Prüfe ob die Struktur jetzt korrekt ist
        if corrected != sql_text:
            logger.info("Trigger-Struktur wurde automatisch korrigiert")
        else:
            logger.debug("Trigger-Struktur war bereits korrekt")
        
        return corrected

    def format_sql_for_execution(self, sql_text: str) -> str:
        """
        Formatiert entschlüsselte SQL-Daten für die Ausführung.
        Entfernt störende Zeichen (BOM, Steuerzeichen), behält aber die SQL-Struktur bei.
        
        Args:
            sql_text: Roher entschlüsselter SQL-Text
            
        Returns:
            Bereinigter SQL-Query-String, bereit für Ausführung
        """
        import re
        
        if not sql_text or not sql_text.strip():
            return ""
        
        # Entferne führende/abschließende Whitespace
        sql = sql_text.strip()
        
        # Entferne mögliche BOM (Byte Order Mark) am Anfang
        if sql.startswith('\ufeff'):
            sql = sql[1:].strip()
        
        # Entferne mögliche Steuerzeichen (außer normale Whitespace wie \n, \r, \t, Leerzeichen)
        # Behalte normale Whitespace-Zeichen für SQL-Formatierung
        sql = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', sql)
        
        # Entferne mögliche unsichtbare Unicode-Zeichen, die SQL stören könnten
        # Behalte aber normale Zeichen und Whitespace
        sql = re.sub(r'[\u200B-\u200D\uFEFF]', '', sql)  # Zero-Width Spaces, BOM
        
        # Finale Bereinigung: Entferne führende/abschließende Whitespace nochmal
        # BEHALTE aber Leerzeichen innerhalb des SQL-Textes
        sql = sql.strip()
        
        logger.debug(f"SQL formatiert: {len(sql)} Zeichen (ursprünglich: {len(sql_text)} Zeichen)")
        return sql

