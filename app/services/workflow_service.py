"""
Workflow Service für OSS goEcommerce
Service-Klasse für n8n Workflow-Integration
Wrapper um N8nWorkflowManager für Service-Architektur
"""

from typing import Dict, List, Optional, Tuple
from app.core.logging_config import get_logger
from app.managers.n8n_workflow_manager import N8nWorkflowManager

logger = get_logger(__name__)


class WorkflowService:
    """
    Service-Klasse für n8n Workflow-Integration.
    Wrapper um N8nWorkflowManager für einfache Integration.
    """
    
    def __init__(
        self, 
        workflow_url: Optional[str] = None, 
        license_number: str = "123456", 
        email: str = "ivan.levshyn@go-ecommerce.de"
    ):
        """
        Initialisiert den Workflow Service.
        
        Args:
            workflow_url: n8n Workflow URL (optional)
            license_number: Lizenznummer für Headers
            email: E-Mail-Adresse für Headers
        """
        self.workflow_manager = N8nWorkflowManager(workflow_url, license_number, email)
        logger.debug(f"WorkflowService initialisiert - URL: {self.workflow_manager.workflow_url}")
    
    def search_taric_codes(self, search_taric: str) -> Tuple[bool, List[Dict], str]:
        """
        Sucht TARIC-Codes über n8n Workflow.
        
        Args:
            search_taric: TARIC-Code zum Suchen
            
        Returns:
            Tuple (success: bool, results: List[Dict], message: str)
        """
        logger.info(f"Suche TARIC-Codes: {search_taric}")
        return self.workflow_manager.search_taric_codes(search_taric)
    
    def send_products_to_webhook(
        self, 
        products: List[Dict], 
        webhook_url: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Sendet Produktdaten an n8n Webhook.
        
        Args:
            products: Liste von Produktdaten
            webhook_url: Webhook URL (optional)
            
        Returns:
            Tuple (success: bool, message: str)
        """
        logger.info(f"Sende {len(products)} Produkte an Webhook")
        return self.workflow_manager.send_products_to_webhook(products, webhook_url)
    
    def get_workflow_url(self) -> str:
        """Gibt die aktuelle Workflow-URL zurück"""
        return self.workflow_manager.workflow_url
    
    def set_workflow_url(self, workflow_url: str):
        """Setzt eine neue Workflow-URL"""
        self.workflow_manager.workflow_url = workflow_url
        logger.info(f"Workflow-URL aktualisiert: {workflow_url}")
    
    def set_credentials(self, license_number: str, email: str):
        """Aktualisiert Lizenz-Credentials"""
        self.workflow_manager.license_number = license_number
        self.workflow_manager.email = email
        
        # Aktualisiere Session-Headers
        self.workflow_manager.session.headers.update({
            'X-License-Number': license_number,
            'X-License-Email': email,
        })
        logger.info("Workflow-Credentials aktualisiert")

