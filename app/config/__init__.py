"""
Config-Modul für OSS goEcommerce
Zentrale Konfigurationsdatei für alle Einstellungen
"""

import os

# Importiere Endpoint-Konfiguration
from .endpoints import EndpointConfig, endpoints

# Importiere n8n Workflow Manager für Rückwärtskompatibilität
try:
    from n8n_workflow_manager import N8nWorkflowManager
    N8N_AVAILABLE = True
except ImportError:
    N8N_AVAILABLE = False
except Exception:
    N8N_AVAILABLE = False

# Verwende zentrale Endpoint-Konfiguration für default_workflow_url
try:
    DEFAULT_WORKFLOW_URL = EndpointConfig.get_endpoint("taric_search")
except Exception:
    DEFAULT_WORKFLOW_URL = "https://agentic.go-ecommerce.de/webhook/v1/users/tarics"

# Supabase-Verbindung deaktiviert - nur n8n Workflow wird verwendet
SUPABASE_AVAILABLE = False

# Standard-Konfiguration
DEFAULT_CONFIG = {
    "app_name": "OSS goEcommerce - TARIC-Suche",
    "app_version": "1.0.0",
    "min_window_size": (1200, 800),
    "default_window_size": (1400, 900),
    "license_service_name": "OSS_goEcommerce",
    "license_file": "license_config.json",
    "n8n": {
        "default_workflow_url": DEFAULT_WORKFLOW_URL,
        "default_license_number": "123456",
        "default_email": "ivan.levshyn@go-ecommerce.de"
    }
}

# Farbschema (Orange-Schwarz)
COLOR_SCHEME = {
    "window": "#1a1a1a",
    "window_text": "#ff8c00", 
    "base": "#2a2a2a",
    "alternate_base": "#1a1a1a",
    "tooltip_base": "#2a2a2a",
    "tooltip_text": "#ff8c00",
    "text": "#ff8c00",
    "button": "#ff8c00",
    "button_text": "#000000",
    "bright_text": "#ffaa00",
    "link": "#ff8c00",
    "highlight": "#ff8c00",
    "highlighted_text": "#000000"
}

def get_config():
    """Gibt die aktuelle Konfiguration zurück"""
    return DEFAULT_CONFIG.copy()

def get_color_scheme():
    """Gibt das Farbschema zurück"""
    return COLOR_SCHEME.copy()

# Exportiere alle wichtigen Funktionen und Klassen
__all__ = [
    'EndpointConfig', 
    'endpoints',
    'DEFAULT_CONFIG',
    'COLOR_SCHEME',
    'DEFAULT_WORKFLOW_URL',
    'SUPABASE_AVAILABLE',
    'N8N_AVAILABLE',
    'get_config',
    'get_color_scheme'
]

