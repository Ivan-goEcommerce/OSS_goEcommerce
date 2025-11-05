"""
Trigger Endpoint Service für OSS goEcommerce
Service-Klasse für Abruf, Entschlüsselung und Ausführung von Trigger-Updates
"""

import requests
import json
from typing import Optional, Tuple
from app.core.logging_config import get_logger
from app.services.decrypt_service import DecryptService
from app.services.database_service import DatabaseService
from app.services.license_service import LicenseService

logger = get_logger(__name__)


class TriggerEndpointService:
    """
    Service-Klasse für Trigger-Endpoint-Abruf mit automatischer Entschlüsselung und Ausführung.
    Sendet immer Lizenz-Daten im Header mit.
    """
    
    def __init__(self, decrypt_service: Optional[DecryptService] = None, 
                 database_service: Optional[DatabaseService] = None,
                 license_service: Optional[LicenseService] = None):
        """
        Initialisiert den Trigger Endpoint Service.
        
        Args:
            decrypt_service: DecryptService Instanz (optional, wird erstellt wenn None)
            database_service: DatabaseService Instanz (optional, wird erstellt wenn None)
            license_service: LicenseService Instanz (optional, wird erstellt wenn None)
        """
        self.decrypt_service = decrypt_service or DecryptService()
        self.database_service = database_service or DatabaseService()
        self.license_service = license_service or LicenseService()
        self.url = "https://agentic.go-ecommerce.de/webhook/v1/get-products-trigger"
        logger.debug("TriggerEndpointService initialisiert")
    
    def _get_license_headers(self) -> dict:
        """
        Erstellt Headers mit Lizenz-Daten.
        
        Returns:
            Dictionary mit Headers inkl. Lizenz-Daten
        """
        license_number, email = self.license_service.load_license()
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'OSS-goEcommerce/1.0.0',
            'Accept': 'application/json',
        }
        
        # Füge Lizenz-Daten hinzu, wenn verfügbar
        if license_number:
            headers['X-License-Number'] = license_number
        if email:
            headers['X-License-Email'] = email
        
        logger.debug(f"Headers erstellt - License: {license_number[:4] if license_number else 'N/A'}...")
        return headers
    
    def fetch_and_execute_trigger(self, password: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Ruft Trigger-Endpunkt ab, entschlüsselt die Antwort und führt SQL aus.
        
        Args:
            password: Passwort für Entschlüsselung (optional, verwendet Standard wenn None)
            
        Returns:
            Tuple (success: bool, message: str, decrypted_sql: Optional[str])
            decrypted_sql enthält die entschlüsselte und korrigierte SQL (auch bei Fehlern)
        """
        try:
            # Schritt 1: Endpunkt abrufen mit Lizenz-Daten im Header
            logger.info(f"Rufe Trigger-Endpunkt ab: {self.url}")
            headers = self._get_license_headers()
            
            response = requests.get(self.url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                error_msg = f"HTTP Fehler {response.status_code}: {response.text[:200]}"
                logger.error(error_msg)
                return False, f"❌ Fehler beim Abrufen des Endpunkts:\n\n{error_msg}", None
            
            # Schritt 2: Response parsen (erwartet JSON mit n8n-Format)
            try:
                response_data = response.json()
                logger.info(f"Response erhalten: {type(response_data)}")
            except json.JSONDecodeError:
                # Versuche als Text zu behandeln
                response_text = response.text.strip()
                if not response_text:
                    return False, "❌ Endpunkt hat keine Daten zurückgegeben", None
                
                # Versuche als JSON-String zu parsen
                try:
                    response_data = json.loads(response_text)
                except json.JSONDecodeError:
                    return False, f"❌ Antwort ist kein gültiges JSON:\n\n{response_text[:200]}", None
            
            # Schritt 3: Prüfe ob es eine Liste ist (n8n-Format)
            if not isinstance(response_data, list):
                return False, f"❌ Antwort ist keine Liste (n8n-Format erwartet):\n\n{type(response_data)}", None
            
            if not response_data:
                return False, "❌ Antwort-Liste ist leer", None
            
            # Schritt 4: Entschlüsselung
            logger.info(f"Entschlüssele {len(response_data)} Items...")
            try:
                decrypted_text = self.decrypt_service.decrypt_from_n8n_format(
                    response_data,
                    password
                )
                logger.info(f"Entschlüsselung erfolgreich: {len(decrypted_text)} Zeichen")
            except Exception as e:
                error_msg = f"Fehler bei Entschlüsselung: {str(e)}"
                logger.error(error_msg)
                return False, f"❌ {error_msg}", None
            
            if not decrypted_text or not decrypted_text.strip():
                return False, "❌ Entschlüsselte Daten sind leer", None
            
            # Schritt 5: SQL für Ausführung formatieren (entfernt BOM, Steuerzeichen etc.)
            logger.info("Formatiere SQL für Ausführung...")
            formatted_sql = self.decrypt_service.format_sql_for_execution(decrypted_text)
            
            if not formatted_sql or not formatted_sql.strip():
                return False, "❌ Formatierte SQL-Daten sind leer", None
            
            # Schritt 6: Trigger-Struktur korrigieren
            logger.info("Korrigiere Trigger-Struktur...")
            corrected_sql = self.decrypt_service.fix_trigger_structure(formatted_sql)
            
            # Schritt 7: Prüfe DB-Verbindung
            if not self.database_service.has_saved_credentials():
                return False, "❌ Keine Datenbank-Credentials gefunden.\n\nBitte konfigurieren Sie zuerst die DB-Verbindung über 'DB Credentials'.", corrected_sql
            
            # Teste Verbindung
            success, message = self.database_service.test_connection()
            if not success:
                return False, f"❌ Datenbankverbindung fehlgeschlagen:\n\n{message}", corrected_sql
            
            # Schritt 8: SQL ausführen
            logger.info("Führe SQL aus...")
            success, message, results = self.database_service.execute_query(corrected_sql)
            
            if success:
                # Erfolg!
                result_message = f"✅ Trigger erfolgreich aktualisiert!\n\n{message}"
                if results and isinstance(results, list):
                    result_message += f"\n\nGefundene Zeilen: {len(results)}"
                elif results:
                    result_message += f"\n\nBetroffene Zeilen: {results}"
                
                logger.info("Trigger-Update erfolgreich abgeschlossen")
                return True, result_message, corrected_sql
            else:
                # Fehler bei SQL-Ausführung
                logger.error(f"SQL-Ausführung fehlgeschlagen: {message}")
                return False, f"❌ SQL-Ausführung fehlgeschlagen:\n\n{message}", corrected_sql
        
        except requests.exceptions.Timeout:
            error_msg = "Timeout beim Abrufen des Endpunkts (über 30 Sekunden)"
            logger.error(error_msg)
            return False, f"❌ {error_msg}", None
        except requests.exceptions.RequestException as e:
            error_msg = f"Netzwerkfehler: {str(e)}"
            logger.error(error_msg)
            return False, f"❌ {error_msg}", None
        except Exception as e:
            error_msg = f"Unerwarteter Fehler: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, f"❌ {error_msg}", None

