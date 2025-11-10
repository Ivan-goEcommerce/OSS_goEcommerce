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
        
        WICHTIG: Trigger wird NUR erstellt, wenn BEIDE Verbindungen funktionieren!
        
        Prüfungsablauf:
        1. Erste Prüfung: Beide Verbindungen (Datenbank + Endpoint)
        2. Daten abrufen und verarbeiten
        3. FINALE Prüfung: Beide Verbindungen nochmal prüfen
        4. Trigger erstellen (nur wenn beide Verbindungen funktionieren)
        
        Args:
            password: Passwort für Entschlüsselung (optional, verwendet Standard wenn None)
            
        Returns:
            Tuple (success: bool, message: str, decrypted_sql: Optional[str])
            decrypted_sql enthält die entschlüsselte und korrigierte SQL (auch bei Fehlern)
        """
        try:
            # ============================================
            # SCHRITT 1: PRÜFE BEIDE VERBINDUNGEN ZUERST
            # ============================================
            
            # Schritt 1.1: Prüfe Datenbank-Verbindung
            logger.info("Prüfe Datenbank-Verbindung...")
            if not self.database_service.has_saved_credentials():
                return False, "❌ Keine Datenbank-Credentials gefunden.\n\nBitte konfigurieren Sie zuerst die DB-Verbindung über 'DB Credentials'.", None
            
            db_success, db_message = self.database_service.test_connection()
            if not db_success:
                return False, f"❌ Datenbankverbindung fehlgeschlagen:\n\n{db_message}\n\nTrigger wird nicht erstellt.", None
            
            logger.info("✓ Datenbank-Verbindung erfolgreich")
            
            # Schritt 1.2: Prüfe Endpoint-Verbindung (Test-Request)
            logger.info(f"Prüfe Endpoint-Verbindung: {self.url}")
            headers = self._get_license_headers()
            
            try:
                # Test-Request mit kurzem Timeout um Verbindung zu prüfen
                test_response = requests.get(self.url, headers=headers, timeout=10)
                if test_response.status_code != 200:
                    error_msg = f"HTTP Fehler {test_response.status_code}: {test_response.text[:200]}"
                    logger.error(f"Endpoint-Verbindung fehlgeschlagen: {error_msg}")
                    return False, f"❌ Endpoint-Verbindung fehlgeschlagen:\n\n{error_msg}\n\nTrigger wird nicht erstellt.", None
                logger.info("✓ Endpoint-Verbindung erfolgreich")
            except requests.exceptions.Timeout:
                error_msg = "Timeout beim Testen des Endpunkts (über 10 Sekunden)"
                logger.error(error_msg)
                return False, f"❌ {error_msg}\n\nTrigger wird nicht erstellt.", None
            except requests.exceptions.RequestException as e:
                error_msg = f"Netzwerkfehler beim Testen des Endpunkts: {str(e)}"
                logger.error(error_msg)
                return False, f"❌ {error_msg}\n\nTrigger wird nicht erstellt.", None
            
            # ============================================
            # SCHRITT 2: BEIDE VERBINDUNGEN FUNKTIONIEREN
            # Jetzt Trigger-Daten abrufen und verarbeiten
            # ============================================
            
            # Schritt 2.1: Endpunkt abrufen mit Lizenz-Daten im Header
            logger.info(f"Rufe Trigger-Daten vom Endpunkt ab: {self.url}")
            response = requests.get(self.url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                error_msg = f"HTTP Fehler {response.status_code}: {response.text[:200]}"
                logger.error(error_msg)
                return False, f"❌ Fehler beim Abrufen des Endpunkts:\n\n{error_msg}", None
            
            # Schritt 2.2: Response parsen (erwartet JSON mit n8n-Format)
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
            
            # Schritt 2.3: Prüfe ob es eine Liste ist (n8n-Format)
            if not isinstance(response_data, list):
                return False, f"❌ Antwort ist keine Liste (n8n-Format erwartet):\n\n{type(response_data)}", None
            
            if not response_data:
                return False, "❌ Antwort-Liste ist leer", None
            
            # Schritt 2.4: Entschlüsselung
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
            
            # Schritt 2.5: SQL für Ausführung formatieren (entfernt BOM, Steuerzeichen etc.)
            logger.info("Formatiere SQL für Ausführung...")
            formatted_sql = self.decrypt_service.format_sql_for_execution(decrypted_text)
            
            if not formatted_sql or not formatted_sql.strip():
                return False, "❌ Formatierte SQL-Daten sind leer", None
            
            # Schritt 2.6: Trigger-Struktur korrigieren
            logger.info("Korrigiere Trigger-Struktur...")
            corrected_sql = self.decrypt_service.fix_trigger_structure(formatted_sql)
            
            # ============================================
            # SCHRITT 3: FINALE PRÜFUNG BEIDER VERBINDUNGEN
            # Trigger wird NUR erstellt, wenn BEIDE Verbindungen funktionieren
            # ============================================
            logger.info("Finale Prüfung: Beide Verbindungen müssen funktionieren...")
            
            # Schritt 3.1: Finale Prüfung Datenbank-Verbindung
            logger.info("Finale Prüfung: Datenbank-Verbindung...")
            db_success, db_message = self.database_service.test_connection()
            if not db_success:
                error_msg = f"❌ Finale Prüfung: Datenbankverbindung fehlgeschlagen:\n\n{db_message}\n\nTrigger wird NICHT erstellt."
                logger.error(error_msg)
                return False, error_msg, corrected_sql
            logger.info("✓ Finale Prüfung: Datenbank-Verbindung erfolgreich")
            
            # Schritt 3.2: Finale Prüfung Endpoint-Verbindung
            logger.info(f"Finale Prüfung: Endpoint-Verbindung: {self.url}")
            try:
                final_test_response = requests.get(self.url, headers=headers, timeout=10)
                if final_test_response.status_code != 200:
                    error_msg = f"❌ Finale Prüfung: Endpoint-Verbindung fehlgeschlagen (HTTP {final_test_response.status_code})\n\nTrigger wird NICHT erstellt."
                    logger.error(error_msg)
                    return False, error_msg, corrected_sql
                logger.info("✓ Finale Prüfung: Endpoint-Verbindung erfolgreich")
            except requests.exceptions.Timeout:
                error_msg = "❌ Finale Prüfung: Endpoint-Verbindung Timeout (über 10 Sekunden)\n\nTrigger wird NICHT erstellt."
                logger.error(error_msg)
                return False, error_msg, corrected_sql
            except requests.exceptions.RequestException as e:
                error_msg = f"❌ Finale Prüfung: Endpoint-Verbindung fehlgeschlagen: {str(e)}\n\nTrigger wird NICHT erstellt."
                logger.error(error_msg)
                return False, error_msg, corrected_sql
            
            # ============================================
            # SCHRITT 4: BEIDE VERBINDUNGEN FUNKTIONIEREN
            # Jetzt kann der Trigger sicher erstellt werden
            # ============================================
            logger.info("✅ BEIDE Verbindungen funktionieren - Trigger wird jetzt erstellt...")
            
            # Schritt 4.1: SQL ausführen (Trigger erstellen)
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

