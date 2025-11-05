"""
Konfiguration für OSS goEcommerce
Zentrale Konfigurationsdatei für alle Einstellungen
"""

import os

# Supabase-Verbindung deaktiviert - nur n8n Workflow wird verwendet
SUPABASE_AVAILABLE = False
print("INFO: Supabase-Verbindung deaktiviert - nur n8n Workflow wird verwendet")

# Import n8n Workflow Manager
try:
    from n8n_workflow_manager import N8nWorkflowManager
    N8N_AVAILABLE = True
    print("OK: n8n Workflow Manager erfolgreich importiert!")
except ImportError as e:
    N8N_AVAILABLE = False
    print(f"HINWEIS: n8n Workflow Manager nicht verfügbar: {e}")
except Exception as e:
    N8N_AVAILABLE = False
    print(f"HINWEIS: Fehler beim Laden von n8n Workflow Manager: {e}")

# Standard-Konfiguration
DEFAULT_CONFIG = {
    "app_name": "OSS goEcommerce - TARIC-Suche",
    "app_version": "1.0.0",
    "min_window_size": (1200, 800),
    "default_window_size": (1400, 900),
    "license_service_name": "OSS_goEcommerce",
    "license_file": "license_config.json",
    "n8n": {
        "default_workflow_url": "https://agentic.go-ecommerce.de/webhook-test/v1/users/tarics",
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
