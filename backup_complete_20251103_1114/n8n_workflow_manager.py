"""
n8n Workflow Manager
Backward Compatibility Wrapper

Diese Datei stellt die alte N8nWorkflowManager-Klasse zur Verfügung
für bestehenden Code, der noch den alten Import verwendet.

Die Klasse wurde nach app/managers/ verschoben.
"""

import sys
from pathlib import Path

# Stelle sicher, dass app im Pfad ist
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Importiere N8nWorkflowManager aus dem neuen Ort
from app.managers.n8n_workflow_manager import (
    N8nWorkflowManager,
    get_n8n_manager,
    search_taric_via_n8n,
    test_n8n_connection
)

# Für direkte Imports - Backward Compatibility
__all__ = ['N8nWorkflowManager', 'get_n8n_manager', 'search_taric_via_n8n', 'test_n8n_connection']

