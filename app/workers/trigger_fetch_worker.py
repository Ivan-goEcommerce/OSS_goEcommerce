"""
Worker für automatischen Abruf und Ausführung von Trigger-Updates beim Programmstart
Verwendet den TriggerEndpointService für die eigentliche Logik
"""

from typing import Optional
from PySide6.QtCore import QThread, Signal

from app.services.trigger_endpoint_service import TriggerEndpointService
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TriggerFetchWorker(QThread):
    """Worker-Thread für Abruf, Entschlüsselung und Ausführung von Trigger-Updates"""
    
    finished = Signal(bool, str, str)  # success, message, decrypted_sql
    
    def __init__(self, trigger_endpoint_service: Optional[TriggerEndpointService] = None, password: Optional[str] = None):
        """
        Initialisiert den Worker.
        
        Args:
            trigger_endpoint_service: TriggerEndpointService Instanz (optional, wird erstellt wenn None)
            password: Passwort für Entschlüsselung (optional, verwendet Standard wenn None)
        """
        super().__init__()
        self.trigger_endpoint_service = trigger_endpoint_service or TriggerEndpointService()
        self.password = password
    
    def run(self):
        """Führt den gesamten Prozess aus: Abruf -> Entschlüsselung -> SQL-Ausführung"""
        logger.info("Starte Trigger-Update über TriggerEndpointService...")
        
        # Verwende den Service für die gesamte Logik
        success, message, decrypted_sql = self.trigger_endpoint_service.fetch_and_execute_trigger(self.password)
        
        # Signal senden (decrypted_sql kann None sein bei frühen Fehlern)
        self.finished.emit(success, message, decrypted_sql or "")

