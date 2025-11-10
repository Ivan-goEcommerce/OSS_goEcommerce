# Fehlerbehandlung - Best Practices Guide

## Übersicht

Die OSS goEcommerce Anwendung verwendet ein zentrales Fehlerbehandlungssystem mit:
- **Statischer Fehlerliste** (`app/core/error_codes.py`) - 30+ Fehlercodes mit Beschreibungen und Lösungen
- **Error Handler** (`app/core/error_handler.py`) - Zentrale Fehlerbehandlung mit `handle_error()`
- **ErrorCode Enum** - Konsistente Fehlercodes für die gesamte Anwendung

## Schnellstart

### 1. Basis-Fehlerbehandlung

```python
from app.core.error_handler import handle_error, ErrorCode
from app.core.logging_config import get_logger

logger = get_logger(__name__)

def my_function():
    try:
        # Dein Code hier
        return True, "Erfolg", data
    except SpecificException as e:
        error = handle_error(e, error_code=ErrorCode.DB_CONNECTION_FAILED)
        logger.error(f"Fehler: {error.message}", exc_info=True)
        return False, error.message, None
    except Exception as e:
        error = handle_error(e)
        logger.error(f"Unerwarteter Fehler: {error.message}", exc_info=True)
        return False, error.message, None
```

### 2. Fehlerliste durchsuchen

```python
from app.core.error_codes import find_error_by_code, find_error_by_pattern

# Nach Code suchen
error_info = find_error_by_code("DB002")
if error_info:
    print(f"Beschreibung: {error_info['description']}")
    print(f"Lösungen: {error_info['solutions']}")

# Nach Muster in Fehlermeldung suchen
error_message = "Login failed for user"
found_errors = find_error_by_pattern(error_message)
for error in found_errors:
    print(f"Gefunden: {error['code']} - {error['description']}")
```

## Verfügbare Fehlercodes

### Datenbank-Fehler (DB001-DB008)
- **DB001**: DB_CONNECTION_FAILED - Datenbankverbindung fehlgeschlagen
- **DB002**: DB_AUTHENTICATION_FAILED - Authentifizierung fehlgeschlagen
- **DB003**: DB_QUERY_SYNTAX_ERROR - SQL-Syntaxfehler
- **DB004**: DB_PERMISSION_DENIED - Keine Berechtigung
- **DB005**: DB_OBJECT_NOT_FOUND - Objekt nicht gefunden
- **DB006**: DB_TIMEOUT - Timeout überschritten
- **DB007**: DB_TRANSACTION_FAILED - Transaktion fehlgeschlagen
- **DB008**: DB_CONNECTION_STRING_INVALID - Ungültige Verbindungszeichenkette

### Netzwerk-Fehler (NET001-NET005)
- **NET001**: NET_TIMEOUT - Netzwerk-Timeout
- **NET002**: NET_CONNECTION_REFUSED - Verbindung abgelehnt
- **NET003**: NET_HTTP_ERROR - HTTP-Fehler
- **NET004**: NET_SSL_ERROR - SSL/TLS-Fehler
- **NET005**: NET_DNS_ERROR - DNS-Auflösungsfehler

### Konfigurations-Fehler (CFG001-CFG005)
- **CFG001**: CONFIG_FILE_NOT_FOUND - Konfigurationsdatei nicht gefunden
- **CFG002**: CONFIG_INVALID_JSON - Ungültige JSON-Konfiguration
- **CFG003**: CONFIG_MISSING_KEY - Konfigurationsschlüssel fehlt
- **CFG004**: CONFIG_CREDENTIALS_MISSING - Anmeldedaten fehlen
- **CFG005**: CONFIG_KEYRING_ERROR - Keyring-Fehler

### Validierungs-Fehler (VAL001-VAL004)
- **VAL001**: VAL_INVALID_INPUT - Ungültige Eingabe
- **VAL002**: VAL_MISSING_REQUIRED_FIELD - Pflichtfeld fehlt
- **VAL003**: VAL_INVALID_FORMAT - Ungültiges Format
- **VAL004**: VAL_OUT_OF_RANGE - Wert außerhalb des Bereichs

### Workflow-Fehler (WF001-WF004)
- **WF001**: WF_EXECUTION_FAILED - Workflow-Ausführung fehlgeschlagen
- **WF002**: WF_NOT_FOUND - Workflow nicht gefunden
- **WF003**: WF_INVALID_STATE - Workflow in ungültigem Zustand
- **WF004**: WF_TIMEOUT - Workflow-Timeout

### Allgemeine Fehler (GEN001-GEN004)
- **GEN001**: GEN_UNEXPECTED_ERROR - Unerwarteter Fehler
- **GEN002**: GEN_NOT_IMPLEMENTED - Funktion nicht implementiert
- **GEN003**: GEN_RESOURCE_NOT_FOUND - Ressource nicht gefunden
- **GEN004**: GEN_PERMISSION_DENIED - Keine Berechtigung

## Best Practices

1. **Immer spezifische Exceptions fangen** - Nicht nur `except Exception:`
2. **Error-Handler verwenden** - `handle_error()` für alle Fehler
3. **Immer loggen** - Mit Kontext und `exc_info=True`
4. **Ressourcen schließen** - Im `finally`-Block
5. **Konsistente Return-Werte** - `(bool, str, Optional[Any])`
6. **Fehlercodes verwenden** - Für bessere Fehleranalyse
7. **Statische Fehlerliste nutzen** - Für automatische Fehlererkennung

## Weitere Informationen

Siehe `.cursor/rules/error-handling.mdc` für detaillierte Patterns und Beispiele.



