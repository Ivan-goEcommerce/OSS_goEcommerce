"""
Endpoint-Konfiguration für OSS goEcommerce
Single Point of Truth für alle API-Endpoint-URLs
"""

from typing import Dict


class EndpointConfig:
    """
    Zentrale Konfiguration für alle API-Endpoints.
    Single Point of Truth für Endpoint-URLs.
    """
    
    # Base URL für alle Endpoints
    BASE_URL = "https://agentic.go-ecommerce.de"
    
    # Webhook-Pfade
    WEBHOOK_BASE = f"{BASE_URL}/webhook"
    WEBHOOK_TEST_BASE = f"{BASE_URL}/webhook-test"
    
    # API v1 Endpoints
    API_V1_BASE = f"{WEBHOOK_BASE}/v1"
    API_V1_TEST_BASE = f"{WEBHOOK_TEST_BASE}/v1"
    
    # Spezifische Endpoints - Production URLs als Standard
    ENDPOINTS = {
        # License Management
        "license_check": f"{API_V1_BASE}/check-license",
        "license_check_test": f"{API_V1_TEST_BASE}/check-license",
        
        # Trigger Endpoints
        "trigger_get_products": f"{API_V1_BASE}/get-products-trigger",
        "trigger_get_products_test": f"{API_V1_TEST_BASE}/get-products-trigger",
        
        # Webhook Endpoints - Production als Standard
        "webhook_post_customer_product": f"{WEBHOOK_BASE}/post_customer_product",
        "webhook_post_customer_product_test": f"{WEBHOOK_TEST_BASE}/post_customer_product",
        
        # TARIC Search Endpoints
        "taric_search": f"{API_V1_BASE}/users/tarics",
        "taric_search_test": f"{API_V1_TEST_BASE}/users/tarics",
        
        # Tax Rates Endpoints
        "tax_rates": f"{API_V1_BASE}/tax-rates",
        "tax_rates_test": f"{API_V1_TEST_BASE}/tax-rates",
        
        # Error Handling Endpoints
        "error_webhook": f"{API_V1_BASE}/oss-error",
        "error_webhook_test": f"{API_V1_TEST_BASE}/oss-error",
    }
    
    @classmethod
    def get_endpoint(cls, key: str) -> str:
        """
        Gibt die URL für einen Endpoint-Schlüssel zurück.
        
        Args:
            key: Endpoint-Schlüssel (z.B. "license_check", "trigger_get_products")
            
        Returns:
            Endpoint-URL als String
            
        Raises:
            KeyError: Wenn der Endpoint-Schlüssel nicht gefunden wird
        """
        if key not in cls.ENDPOINTS:
            raise KeyError(f"Endpoint-Schlüssel '{key}' nicht gefunden. Verfügbare Endpoints: {list(cls.ENDPOINTS.keys())}")
        
        return cls.ENDPOINTS[key]
    
    @classmethod
    def get_all_endpoints(cls) -> Dict[str, str]:
        """
        Gibt alle Endpoints als Dictionary zurück.
        
        Returns:
            Dictionary mit allen Endpoint-URLs
        """
        return cls.ENDPOINTS.copy()
    
    @classmethod
    def set_endpoint(cls, key: str, url: str):
        """
        Setzt eine benutzerdefinierte Endpoint-URL.
        Nützlich für Tests oder lokale Entwicklung.
        
        Args:
            key: Endpoint-Schlüssel
            url: Neue Endpoint-URL
        """
        cls.ENDPOINTS[key] = url


# Globale Instanz für einfachen Zugriff
endpoints = EndpointConfig()

