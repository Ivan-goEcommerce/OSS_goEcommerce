"""
JTL Database Manager
Backward Compatibility Wrapper

Diese Datei stellt die alte JTLDatabaseManager-Klasse zur Verfügung
für bestehenden Code, der noch den alten Import verwendet.

Die Klasse wurde nach app/managers/ verschoben.
"""

import sys
from pathlib import Path

# Stelle sicher, dass app im Pfad ist
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Importiere JTLDatabaseManager aus dem neuen Ort
from app.managers.jtl_database_manager import JTLDatabaseManager

# Für direkte Imports - Backward Compatibility
__all__ = ['JTLDatabaseManager']

