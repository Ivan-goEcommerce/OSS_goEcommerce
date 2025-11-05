"""
License Service für OSS goEcommerce
Service-Klasse für Lizenz-Verwaltung
Wrapper um LicenseManager für Service-Architektur
"""

import requests
from typing import Optional, Tuple, Dict, Any
from app.core.logging_config import get_logger
from app.managers.license_manager import LicenseManager

logger = get_logger(__name__)


class LicenseService:
    """
    Service-Klasse für Lizenz-Verwaltung.
    Wrapper um LicenseManager für einfache Integration.
    """
    
    def __init__(self):
        """Initialisiert den License Service"""
        self.license_manager = LicenseManager()
        logger.debug("LicenseService initialisiert")
    
    def save_license(self, license_number: str, email: str) -> bool:
        """
        Speichert Lizenzdaten.
        
        Args:
            license_number: Lizenznummer
            email: E-Mail-Adresse
            
        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        logger.info(f"Speichere Lizenz: {license_number}")
        result = self.license_manager.save_license(license_number, email)
        if result:
            logger.info("Lizenz erfolgreich gespeichert")
        else:
            logger.error("Fehler beim Speichern der Lizenz")
        return result
    
    def load_license(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Lädt Lizenzdaten.
        
        Returns:
            Tuple (license_number, email) oder (None, None) wenn nicht gefunden
        """
        logger.debug("Lade Lizenzdaten")
        license_number, email = self.license_manager.load_license()
        if license_number and email:
            logger.debug("Lizenzdaten erfolgreich geladen")
        else:
            logger.warning("Keine Lizenzdaten gefunden")
        return license_number, email
    
    def has_license(self) -> bool:
        """
        Prüft ob Lizenzdaten vorhanden sind.
        
        Returns:
            True wenn vorhanden, sonst False
        """
        result = self.license_manager.has_license()
        logger.debug(f"Lizenz vorhanden: {result}")
        return result
    
    def clear_license(self) -> bool:
        """
        Löscht alle Lizenzdaten.
        
        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        logger.info("Lösche Lizenzdaten")
        result = self.license_manager.clear_license()
        if result:
            logger.info("Lizenzdaten erfolgreich gelöscht")
        else:
            logger.error("Fehler beim Löschen der Lizenzdaten")
        return result
    
    def check_license_via_endpoint(
        self, 
        endpoint_url: str = "https://agentic.go-ecommerce.de/webhook/v1/check-license"
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Sendet gespeicherte Lizenzdaten aus Keyring an Endpoint zur Validierung.
        
        Args:
            endpoint_url: URL des License-Check-Endpoints
            
        Returns:
            Tuple (success: bool, response_data: Dict, message: str)
            - success: True wenn Request erfolgreich war
            - response_data: Response-Daten als Dictionary
            - message: Status-Meldung
        """
        # Lade gespeicherte Lizenzdaten
        license_number, email = self.load_license()
        
        # DEBUG: Zeige was geladen wurde
        from app.core.debug_manager import debug_print
        debug_print(f"DEBUG check_license_via_endpoint: Geladene Daten aus Keyring:")
        debug_print(f"  License Number: {license_number}")
        debug_print(f"  Email: {email}")
        
        if not license_number or not email:
            error_msg = "Keine Lizenzdaten im Keyring gefunden"
            logger.warning(error_msg)
            return False, {}, error_msg
        
        try:
            logger.info(f"Prüfe Lizenz über Endpoint: {endpoint_url}")
            logger.info(f"WICHTIG: Sende Lizenzdaten - Lizenznummer: {license_number}, E-Mail: {email}")
            logger.debug(f"Lizenznummer: {license_number[:4]}..., E-Mail: {email[:3]}...")
            
            # Headers genau wie vom Server erwartet (automatisch gesetzt)
            headers = {
                'Connection': 'keep-alive',
                'Host': 'agentic.go-ecommerce.de',
                'X-Forwarded-Scheme': 'https',
                'X-Forwarded-Proto': 'https',
                'X-Forwarded-For': '209.198.144.29',
                'X-Real-Ip': '209.198.144.29',
                # 'Content-Length' wird automatisch von requests gesetzt (0 für leeren Body)
                'User-Agent': 'python-requests/2.31.0',
                'Accept-Encoding': 'gzip, deflate',
                'Accept': '*/*',
                'X-License-Number': license_number,
                'X-License-Email': email
            }
            
            # POST Request ohne Payload (nur Headers mit Lizenzdaten)
            # requests setzt Content-Length automatisch auf 0 für leeren Body
            response = requests.post(
                endpoint_url,
                headers=headers,
                data=b"",  # Leerer Payload (bytes) - Content-Length: 0 wird automatisch gesetzt
                timeout=30
            )
            
            logger.info(f"License-Check Response Status: {response.status_code}")
            
            # Versuche JSON-Response zu parsen
            try:
                response_data = response.json()
                logger.debug(f"Response Data: {response_data}")
            except ValueError:
                # Wenn kein JSON, verwende Text
                response_data = {"raw_response": response.text}
                logger.warning("Response ist kein JSON, verwende Text")
            
            # Prüfe HTTP-Status
            if response.status_code != 200:
                error_msg = f"License-Check fehlgeschlagen: HTTP {response.status_code}"
                logger.error(error_msg)
                return False, response_data, error_msg
            
            # Prüfe auch die Response-Daten auf Gültigkeit
            # Server kann 200 zurückgeben, aber status: 'invalid' in der Response haben
            if isinstance(response_data, dict):
                status = response_data.get('status', '').lower()
                
                if status == 'valid':
                    success_msg = "Lizenz erfolgreich geprüft und gültig"
                    logger.info(success_msg)
                    return True, response_data, success_msg
                elif status == 'invalid':
                    reason = response_data.get('reason', 'Unbekannter Grund')
                    error_msg = f"Lizenz ungültig: {reason}"
                    logger.error(f"License-Check: {error_msg} - Response: {response_data}")
                    return False, response_data, error_msg
                else:
                    # Status unbekannt - prüfe ob 'valid' irgendwo in den Daten ist
                    logger.warning(f"Unbekannter Status in Response: {status}, Response: {response_data}")
                    # Wenn kein klarer Status, aber HTTP 200, nehmen wir an es ist OK
                    success_msg = "Lizenzprüfung durchgeführt (Status unklar)"
                    logger.info(success_msg)
                    return True, response_data, success_msg
            else:
                # Response ist kein Dict - bei HTTP 200 nehmen wir an es ist OK
                success_msg = "Lizenzprüfung durchgeführt"
                logger.info(success_msg)
                return True, response_data, success_msg
                
        except requests.exceptions.Timeout:
            error_msg = "Timeout beim License-Check"
            logger.error(error_msg)
            return False, {}, error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"Netzwerkfehler beim License-Check: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg
        except Exception as e:
            error_msg = f"Unerwarteter Fehler beim License-Check: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, {}, error_msg

