# Debug-Manager Verwendung

## Übersicht

Der zentrale Debug-Manager steuert die Anzeige von Debug-Informationen (Console-Outputs und Info-Fenster).

## Aktivierung

### Option 1: Umgebungsvariable (empfohlen)

**Windows (PowerShell):**
```powershell
$env:OSS_DEBUG="1"
python main.py
```

**Windows (CMD):**
```cmd
set OSS_DEBUG=1
python main.py
```

**Linux/Mac:**
```bash
export OSS_DEBUG=1
python main.py
```

### Option 2: Programmatisch

```python
from app.core.debug_manager import get_debug_manager

# Debug aktivieren
debug_manager = get_debug_manager()
debug_manager.enable()

# Debug deaktivieren
debug_manager.disable()

# Status prüfen
if debug_manager.is_enabled():
    print("Debug ist aktiv")
```

## Verwendung im Code

### Console-Ausgaben

**Statt `print()`:**
```python
from app.core.debug_manager import debug_print

# Alte Variante:
print("INFO: Starte Verarbeitung...")

# Neue Variante:
debug_print("INFO: Starte Verarbeitung...")
```

### Info-Fenster

**Info-Fenster anzeigen:**
```python
from app.core.debug_manager import debug_info, debug_warning, debug_error

# Info-Fenster (nur wenn Debug aktiv)
debug_info("DB-Verbindung erfolgreich", parent=self)

# Warnung (nur wenn Debug aktiv)
debug_warning("Fehlende Konfiguration", parent=self)

# Fehler (nur wenn Debug aktiv)
debug_error("Verbindung fehlgeschlagen", parent=self)
```

### Komplettes Beispiel

```python
from app.core.debug_manager import debug_print, debug_info

def check_connection(self):
    debug_print("INFO: Prüfe Verbindung...")
    
    success = self.test_connection()
    
    if success:
        debug_print("OK: Verbindung erfolgreich")
        debug_info(f"Verbindung erfolgreich:\n{self.connection_details}", self)
    else:
        debug_print("FEHLER: Verbindung fehlgeschlagen")
```

## Verhalten

- **Debug aktiviert:**
  - `debug_print()` gibt Ausgaben in die Console
  - `debug_info()`, `debug_warning()`, `debug_error()` zeigen Fenster
  
- **Debug deaktiviert:**
  - `debug_print()` gibt **nichts** aus
  - `debug_info()`, `debug_warning()`, `debug_error()` zeigen **keine** Fenster

## Wichtige Hinweise

1. **Kritische Fehler:** Verwende weiterhin `QMessageBox.critical()` für Fehler, die dem Benutzer immer angezeigt werden müssen
2. **Logging:** Für permanente Logs verwende weiterhin `logger.info()`, `logger.error()` etc.
3. **Debug-Ausgaben:** Verwende `debug_print()` nur für temporäre Debug-Informationen

## Migration

Um bestehenden Code zu migrieren:

1. Ersetze `print()` durch `debug_print()`
2. Ersetze `QMessageBox.information()` (nur für Debug) durch `debug_info()`
3. Importiere: `from app.core.debug_manager import debug_print, debug_info`

