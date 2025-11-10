"""
Statische Fehlerliste für OSS goEcommerce
Diese Datei enthält alle Fehlercodes mit Beschreibungen und Suchmustern.
Wird für Fehleranalyse und Debugging verwendet.
"""

from typing import Dict, List, Optional
from app.core.error_handler import ErrorCode


# Statische Fehlerliste: Code -> Beschreibung + Suchmuster
ERROR_DATABASE: Dict[str, Dict[str, any]] = {
    "DB001": {
        "code": "DB001",
        "name": "DB_CONNECTION_FAILED",
        "description": "Datenbankverbindung konnte nicht hergestellt werden",
        "category": "Datenbank",
        "search_patterns": [
            "connection failed",
            "cannot connect",
            "server not found",
            "network-related",
            "instance-specific",
            "pyodbc.OperationalError"
        ],
        "common_causes": [
            "SQL Server ist nicht erreichbar",
            "Falsche Server-Adresse",
            "Firewall blockiert Verbindung",
            "ODBC Driver nicht installiert"
        ],
        "solutions": [
            "Prüfen Sie die Server-Adresse",
            "Prüfen Sie die Firewall-Einstellungen",
            "Installieren Sie den ODBC Driver",
            "Testen Sie die Verbindung mit SQL Server Management Studio"
        ]
    },
    "DB002": {
        "code": "DB002",
        "name": "DB_AUTHENTICATION_FAILED",
        "description": "Datenbank-Authentifizierung fehlgeschlagen (Fehler 18456)",
        "category": "Datenbank",
        "search_patterns": [
            "18456",
            "login failed",
            "authentication failed",
            "invalid credentials",
            "password",
            "username"
        ],
        "common_causes": [
            "Falsches Passwort",
            "Benutzername existiert nicht",
            "SQL Server Authentifizierung nicht aktiviert",
            "Passwort nicht im Keyring gespeichert"
        ],
        "solutions": [
            "Prüfen Sie Benutzername und Passwort",
            "Speichern Sie das Passwort im Keyring über 'DB Credentials'",
            "Aktivieren Sie SQL Server Authentifizierung",
            "Prüfen Sie die Benutzerberechtigungen"
        ]
    },
    "DB003": {
        "code": "DB003",
        "name": "DB_QUERY_SYNTAX_ERROR",
        "description": "SQL-Syntaxfehler in der Abfrage",
        "category": "Datenbank",
        "search_patterns": [
            "42000",
            "102",
            "156",
            "syntax error",
            "incorrect syntax",
            "unexpected token"
        ],
        "common_causes": [
            "Falsche SQL-Syntax",
            "Fehlende Klammern oder Anführungszeichen",
            "Fehlendes BEGIN nach AS in CREATE TRIGGER",
            "Fehlendes END vor GO"
        ],
        "solutions": [
            "Prüfen Sie die SQL-Syntax",
            "Validieren Sie die SQL-Query in SQL Server Management Studio",
            "Prüfen Sie auf fehlende oder zusätzliche Zeichen",
            "Verwenden Sie einen SQL-Formatter"
        ]
    },
    "DB004": {
        "code": "DB004",
        "name": "DB_PERMISSION_DENIED",
        "description": "Keine Berechtigung für diese Datenbankoperation",
        "category": "Datenbank",
        "search_patterns": [
            "229",
            "230",
            "300",
            "permission denied",
            "access denied",
            "berechtigung",
            "zugriff"
        ],
        "common_causes": [
            "CREATE TRIGGER Berechtigung fehlt",
            "ALTER TABLE Berechtigung fehlt",
            "db_ddladmin Rolle fehlt",
            "Benutzer hat nicht genug Rechte"
        ],
        "solutions": [
            "Führen Sie als Administrator aus: GRANT ALTER ON OBJECT::[dbo].[tabelle] TO [benutzer]",
            "Fügen Sie den Benutzer zur db_ddladmin Rolle hinzu",
            "Verwenden Sie das Skript: grant_trigger_permissions.sql",
            "Kontaktieren Sie den Datenbankadministrator"
        ]
    },
    "DB005": {
        "code": "DB005",
        "name": "DB_OBJECT_NOT_FOUND",
        "description": "Datenbankobjekt (Tabelle, Trigger, etc.) nicht gefunden",
        "category": "Datenbank",
        "search_patterns": [
            "208",
            "2812",
            "object not found",
            "invalid object name",
            "does not exist"
        ],
        "common_causes": [
            "Objektname ist falsch geschrieben",
            "Falsche Datenbank ausgewählt",
            "Falsches Schema (z.B. dbo.tArtikel)",
            "Objekt wurde gelöscht"
        ],
        "solutions": [
            "Prüfen Sie den Objektnamen",
            "Prüfen Sie die Datenbank",
            "Prüfen Sie das Schema",
            "Führen Sie eine Suche nach dem Objekt durch"
        ]
    },
    "DB006": {
        "code": "DB006",
        "name": "DB_TIMEOUT",
        "description": "Datenbank-Operation hat das Timeout überschritten",
        "category": "Datenbank",
        "search_patterns": [
            "timeout",
            "timeout expired",
            "query timeout"
        ],
        "common_causes": [
            "Query dauert zu lange",
            "Datenbank ist überlastet",
            "Netzwerkverbindung ist langsam",
            "Timeout-Wert zu niedrig"
        ],
        "solutions": [
            "Optimieren Sie die SQL-Query",
            "Erhöhen Sie den Timeout-Wert",
            "Prüfen Sie die Netzwerkverbindung",
            "Führen Sie die Query zu einer anderen Zeit aus"
        ]
    },
    "DB007": {
        "code": "DB007",
        "name": "DB_TRANSACTION_FAILED",
        "description": "Datenbank-Transaktion ist fehlgeschlagen",
        "category": "Datenbank",
        "search_patterns": [
            "transaction failed",
            "rollback",
            "commit failed",
            "transaction error"
        ],
        "common_causes": [
            "Transaktion wurde zurückgerollt",
            "Deadlock erkannt",
            "Constraint-Verletzung",
            "Verbindung während Transaktion verloren"
        ],
        "solutions": [
            "Prüfen Sie die Transaktionslogik",
            "Wiederholen Sie die Transaktion",
            "Prüfen Sie auf Deadlocks",
            "Validieren Sie die Daten vor der Transaktion"
        ]
    },
    "DB008": {
        "code": "DB008",
        "name": "DB_CONNECTION_STRING_INVALID",
        "description": "Ungültige Datenbank-Verbindungszeichenkette",
        "category": "Datenbank",
        "search_patterns": [
            "connection string",
            "invalid connection",
            "connection parameter",
            "driver"
        ],
        "common_causes": [
            "Fehlende Parameter in Connection String",
            "Falscher ODBC Driver Name",
            "Ungültige Server-Adresse",
            "Falsches Format"
        ],
        "solutions": [
            "Prüfen Sie die Connection String Parameter",
            "Validieren Sie den ODBC Driver Namen",
            "Verwenden Sie 'DB Credentials' im Dashboard",
            "Prüfen Sie die Konfigurationsdatei"
        ]
    }
}

ERROR_NETWORK: Dict[str, Dict[str, any]] = {
    "NET001": {
        "code": "NET001",
        "name": "NET_TIMEOUT",
        "description": "Netzwerk-Timeout beim Abrufen von Daten",
        "category": "Netzwerk",
        "search_patterns": [
            "timeout",
            "read timeout",
            "connection timeout",
            "requests.exceptions.Timeout"
        ],
        "common_causes": [
            "Server antwortet nicht",
            "Netzwerkverbindung ist langsam",
            "Server ist überlastet",
            "Timeout-Wert zu niedrig"
        ],
        "solutions": [
            "Prüfen Sie die Server-Verfügbarkeit",
            "Erhöhen Sie den Timeout-Wert",
            "Prüfen Sie die Netzwerkverbindung",
            "Wiederholen Sie den Request"
        ]
    },
    "NET002": {
        "code": "NET002",
        "name": "NET_CONNECTION_REFUSED",
        "description": "Verbindung zum Server wurde abgelehnt",
        "category": "Netzwerk",
        "search_patterns": [
            "connection refused",
            "connection error",
            "requests.exceptions.ConnectionError"
        ],
        "common_causes": [
            "Server ist nicht erreichbar",
            "Falsche URL oder Port",
            "Firewall blockiert Verbindung",
            "Server läuft nicht"
        ],
        "solutions": [
            "Prüfen Sie die URL und den Port",
            "Prüfen Sie die Firewall-Einstellungen",
            "Prüfen Sie ob der Server läuft",
            "Testen Sie die Verbindung mit einem Browser"
        ]
    },
    "NET003": {
        "code": "NET003",
        "name": "NET_HTTP_ERROR",
        "description": "HTTP-Fehler beim Abrufen von Daten",
        "category": "Netzwerk",
        "search_patterns": [
            "http error",
            "status code",
            "4xx",
            "5xx",
            "requests.exceptions.HTTPError"
        ],
        "common_causes": [
            "Server gibt Fehler zurück (4xx/5xx)",
            "Authentifizierung fehlgeschlagen",
            "Ressource nicht gefunden",
            "Server-Fehler"
        ],
        "solutions": [
            "Prüfen Sie den HTTP-Status-Code",
            "Prüfen Sie die Authentifizierung",
            "Prüfen Sie die URL",
            "Kontaktieren Sie den Server-Administrator"
        ]
    },
    "NET004": {
        "code": "NET004",
        "name": "NET_SSL_ERROR",
        "description": "SSL/TLS-Fehler bei der Verbindung",
        "category": "Netzwerk",
        "search_patterns": [
            "ssl error",
            "tls error",
            "certificate",
            "ssl certificate",
            "requests.exceptions.SSLError"
        ],
        "common_causes": [
            "Ungültiges SSL-Zertifikat",
            "Zertifikat abgelaufen",
            "Zertifikat nicht vertrauenswürdig",
            "SSL-Version nicht unterstützt"
        ],
        "solutions": [
            "Prüfen Sie das SSL-Zertifikat",
            "Aktualisieren Sie das Zertifikat",
            "Prüfen Sie die SSL-Konfiguration",
            "Kontaktieren Sie den Server-Administrator"
        ]
    },
    "NET005": {
        "code": "NET005",
        "name": "NET_DNS_ERROR",
        "description": "DNS-Auflösungsfehler",
        "category": "Netzwerk",
        "search_patterns": [
            "dns error",
            "name resolution",
            "hostname",
            "could not resolve"
        ],
        "common_causes": [
            "Hostname kann nicht aufgelöst werden",
            "DNS-Server nicht erreichbar",
            "Falscher Hostname",
            "Netzwerkprobleme"
        ],
        "solutions": [
            "Prüfen Sie den Hostname",
            "Prüfen Sie die DNS-Konfiguration",
            "Testen Sie die Netzwerkverbindung",
            "Verwenden Sie eine IP-Adresse statt Hostname"
        ]
    }
}

ERROR_CONFIG: Dict[str, Dict[str, any]] = {
    "CFG001": {
        "code": "CFG001",
        "name": "CONFIG_FILE_NOT_FOUND",
        "description": "Konfigurationsdatei nicht gefunden",
        "category": "Konfiguration",
        "search_patterns": [
            "file not found",
            "config file",
            "FileNotFoundError",
            "jtl_config.json"
        ],
        "common_causes": [
            "Datei wurde gelöscht",
            "Falscher Pfad",
            "Datei wurde nicht erstellt"
        ],
        "solutions": [
            "Erstellen Sie die Konfigurationsdatei",
            "Prüfen Sie den Dateipfad",
            "Verwenden Sie 'DB Credentials' im Dashboard"
        ]
    },
    "CFG002": {
        "code": "CFG002",
        "name": "CONFIG_INVALID_JSON",
        "description": "Ungültige JSON-Konfiguration",
        "category": "Konfiguration",
        "search_patterns": [
            "json decode error",
            "invalid json",
            "JSONDecodeError",
            "expecting"
        ],
        "common_causes": [
            "JSON-Syntaxfehler",
            "Datei wurde manuell bearbeitet",
            "Datei ist beschädigt"
        ],
        "solutions": [
            "Prüfen Sie die JSON-Syntax",
            "Validieren Sie die JSON-Datei",
            "Erstellen Sie eine neue Konfigurationsdatei"
        ]
    },
    "CFG004": {
        "code": "CFG004",
        "name": "CONFIG_CREDENTIALS_MISSING",
        "description": "Anmeldedaten fehlen im Keyring",
        "category": "Konfiguration",
        "search_patterns": [
            "no password",
            "credentials missing",
            "keyring",
            "password not found"
        ],
        "common_causes": [
            "Passwort wurde nicht gespeichert",
            "Keyring wurde zurückgesetzt",
            "Falscher Keyring-Service"
        ],
        "solutions": [
            "Speichern Sie das Passwort über 'DB Credentials'",
            "Prüfen Sie den Keyring-Service",
            "Erstellen Sie die Konfiguration neu"
        ]
    },
    "CFG003": {
        "code": "CFG003",
        "name": "CONFIG_MISSING_KEY",
        "description": "Erforderlicher Konfigurationsschlüssel fehlt",
        "category": "Konfiguration",
        "search_patterns": [
            "missing key",
            "key not found",
            "required key",
            "configuration key"
        ],
        "common_causes": [
            "Konfigurationsschlüssel wurde nicht gesetzt",
            "Konfigurationsdatei unvollständig",
            "Falscher Schlüsselname"
        ],
        "solutions": [
            "Prüfen Sie die Konfigurationsdatei",
            "Ergänzen Sie fehlende Schlüssel",
            "Verwenden Sie die Standard-Konfiguration",
            "Erstellen Sie die Konfiguration neu"
        ]
    },
    "CFG005": {
        "code": "CFG005",
        "name": "CONFIG_KEYRING_ERROR",
        "description": "Fehler beim Zugriff auf den Keyring",
        "category": "Konfiguration",
        "search_patterns": [
            "keyring error",
            "keyring access",
            "keyring service",
            "keyring failed"
        ],
        "common_causes": [
            "Keyring-Service nicht verfügbar",
            "Berechtigungsprobleme",
            "Keyring-Backend-Fehler"
        ],
        "solutions": [
            "Prüfen Sie den Keyring-Service",
            "Prüfen Sie die Berechtigungen",
            "Installieren Sie ein Keyring-Backend",
            "Verwenden Sie alternative Speichermethode"
        ]
    }
}

ERROR_VALIDATION: Dict[str, Dict[str, any]] = {
    "VAL001": {
        "code": "VAL001",
        "name": "VAL_INVALID_INPUT",
        "description": "Ungültige Eingabedaten",
        "category": "Validierung",
        "search_patterns": [
            "invalid input",
            "invalid data",
            "validation error",
            "type error"
        ],
        "common_causes": [
            "Falscher Datentyp",
            "Ungültiges Format",
            "Eingabe entspricht nicht den Anforderungen"
        ],
        "solutions": [
            "Prüfen Sie den Datentyp",
            "Validieren Sie das Eingabeformat",
            "Prüfen Sie die Eingabeanforderungen"
        ]
    },
    "VAL002": {
        "code": "VAL002",
        "name": "VAL_MISSING_REQUIRED_FIELD",
        "description": "Pflichtfeld fehlt",
        "category": "Validierung",
        "search_patterns": [
            "missing field",
            "required field",
            "field required",
            "missing required"
        ],
        "common_causes": [
            "Pflichtfeld wurde nicht übergeben",
            "Feldname falsch geschrieben",
            "Datenstruktur unvollständig"
        ],
        "solutions": [
            "Prüfen Sie alle Pflichtfelder",
            "Ergänzen Sie fehlende Felder",
            "Validieren Sie die Datenstruktur"
        ]
    },
    "VAL003": {
        "code": "VAL003",
        "name": "VAL_INVALID_FORMAT",
        "description": "Ungültiges Datenformat",
        "category": "Validierung",
        "search_patterns": [
            "invalid format",
            "format error",
            "wrong format",
            "format mismatch"
        ],
        "common_causes": [
            "Datum-Format falsch",
            "E-Mail-Format ungültig",
            "URL-Format ungültig"
        ],
        "solutions": [
            "Prüfen Sie das erwartete Format",
            "Korrigieren Sie das Format",
            "Verwenden Sie Format-Validierung"
        ]
    },
    "VAL004": {
        "code": "VAL004",
        "name": "VAL_OUT_OF_RANGE",
        "description": "Wert außerhalb des erlaubten Bereichs",
        "category": "Validierung",
        "search_patterns": [
            "out of range",
            "range error",
            "value too large",
            "value too small"
        ],
        "common_causes": [
            "Wert zu groß",
            "Wert zu klein",
            "Negativer Wert nicht erlaubt"
        ],
        "solutions": [
            "Prüfen Sie den erlaubten Wertebereich",
            "Korrigieren Sie den Wert",
            "Validieren Sie den Bereich vor der Verarbeitung"
        ]
    }
}

ERROR_WORKFLOW: Dict[str, Dict[str, any]] = {
    "WF001": {
        "code": "WF001",
        "name": "WF_EXECUTION_FAILED",
        "description": "Workflow-Ausführung fehlgeschlagen",
        "category": "Workflow",
        "search_patterns": [
            "workflow execution",
            "workflow failed",
            "execution error",
            "n8n workflow"
        ],
        "common_causes": [
            "Workflow-Fehler in n8n",
            "API-Fehler",
            "Timeout bei Workflow-Ausführung"
        ],
        "solutions": [
            "Prüfen Sie den Workflow in n8n",
            "Prüfen Sie die Workflow-Logs",
            "Wiederholen Sie die Ausführung",
            "Kontaktieren Sie den n8n-Administrator"
        ]
    },
    "WF002": {
        "code": "WF002",
        "name": "WF_NOT_FOUND",
        "description": "Workflow nicht gefunden",
        "category": "Workflow",
        "search_patterns": [
            "workflow not found",
            "workflow id",
            "workflow missing"
        ],
        "common_causes": [
            "Workflow-ID falsch",
            "Workflow wurde gelöscht",
            "Falscher Workflow-Name"
        ],
        "solutions": [
            "Prüfen Sie die Workflow-ID",
            "Prüfen Sie ob der Workflow existiert",
            "Aktualisieren Sie die Workflow-Konfiguration"
        ]
    },
    "WF003": {
        "code": "WF003",
        "name": "WF_INVALID_STATE",
        "description": "Workflow in ungültigem Zustand",
        "category": "Workflow",
        "search_patterns": [
            "invalid state",
            "workflow state",
            "state error"
        ],
        "common_causes": [
            "Workflow ist bereits aktiv",
            "Workflow ist deaktiviert",
            "Workflow-Zustand inkonsistent"
        ],
        "solutions": [
            "Prüfen Sie den Workflow-Zustand",
            "Aktivieren/Deaktivieren Sie den Workflow",
            "Synchronisieren Sie den Workflow-Status"
        ]
    },
    "WF004": {
        "code": "WF004",
        "name": "WF_TIMEOUT",
        "description": "Workflow-Timeout überschritten",
        "category": "Workflow",
        "search_patterns": [
            "workflow timeout",
            "execution timeout",
            "timeout exceeded"
        ],
        "common_causes": [
            "Workflow dauert zu lange",
            "Timeout-Wert zu niedrig",
            "Workflow hängt"
        ],
        "solutions": [
            "Erhöhen Sie den Timeout-Wert",
            "Optimieren Sie den Workflow",
            "Prüfen Sie auf hängende Workflows"
        ]
    }
}

ERROR_GENERAL: Dict[str, Dict[str, any]] = {
    "GEN001": {
        "code": "GEN001",
        "name": "GEN_UNEXPECTED_ERROR",
        "description": "Unerwarteter Fehler aufgetreten",
        "category": "Allgemein",
        "search_patterns": [
            "unexpected error",
            "unexpected exception",
            "unhandled exception"
        ],
        "common_causes": [
            "Unbekannter Fehler",
            "Nicht behandelte Exception",
            "Programmierfehler"
        ],
        "solutions": [
            "Prüfen Sie die Logs für Details",
            "Kontaktieren Sie den Support",
            "Melden Sie den Fehler mit vollständigem Traceback"
        ]
    },
    "GEN002": {
        "code": "GEN002",
        "name": "GEN_NOT_IMPLEMENTED",
        "description": "Funktion noch nicht implementiert",
        "category": "Allgemein",
        "search_patterns": [
            "not implemented",
            "not yet implemented",
            "todo"
        ],
        "common_causes": [
            "Feature in Entwicklung",
            "Funktion noch nicht verfügbar"
        ],
        "solutions": [
            "Warten Sie auf die nächste Version",
            "Verwenden Sie alternative Funktion",
            "Kontaktieren Sie den Entwickler"
        ]
    },
    "GEN003": {
        "code": "GEN003",
        "name": "GEN_RESOURCE_NOT_FOUND",
        "description": "Ressource nicht gefunden",
        "category": "Allgemein",
        "search_patterns": [
            "resource not found",
            "not found",
            "missing resource"
        ],
        "common_causes": [
            "Ressource wurde gelöscht",
            "Falscher Pfad oder ID",
            "Ressource existiert nicht"
        ],
        "solutions": [
            "Prüfen Sie den Ressourcen-Pfad oder ID",
            "Erstellen Sie die Ressource",
            "Prüfen Sie die Berechtigungen"
        ]
    },
    "GEN004": {
        "code": "GEN004",
        "name": "GEN_PERMISSION_DENIED",
        "description": "Keine Berechtigung für diese Operation",
        "category": "Allgemein",
        "search_patterns": [
            "permission denied",
            "access denied",
            "forbidden",
            "unauthorized"
        ],
        "common_causes": [
            "Unzureichende Berechtigungen",
            "Dateisystem-Berechtigungen",
            "API-Berechtigungen fehlen"
        ],
        "solutions": [
            "Prüfen Sie die Berechtigungen",
            "Kontaktieren Sie den Administrator",
            "Verwenden Sie ein Konto mit ausreichenden Rechten"
        ]
    }
}

# Kombinierte Fehlerliste für einfache Suche
ALL_ERRORS: Dict[str, Dict[str, any]] = {
    **ERROR_DATABASE,
    **ERROR_NETWORK,
    **ERROR_CONFIG,
    **ERROR_VALIDATION,
    **ERROR_WORKFLOW,
    **ERROR_GENERAL
}


def find_error_by_code(code: str) -> Optional[Dict[str, any]]:
    """Findet Fehlerinformationen anhand des Codes"""
    return ALL_ERRORS.get(code.upper())


def find_error_by_pattern(text: str) -> List[Dict[str, any]]:
    """
    Findet Fehler anhand von Suchmustern im Text.
    
    Args:
        text: Text in dem gesucht werden soll (z.B. Fehlermeldung)
        
    Returns:
        Liste von gefundenen Fehlern
    """
    text_lower = text.lower()
    found_errors = []
    
    for error_code, error_info in ALL_ERRORS.items():
        for pattern in error_info.get("search_patterns", []):
            if pattern.lower() in text_lower:
                found_errors.append(error_info)
                break
    
    return found_errors


def get_all_errors() -> Dict[str, Dict[str, any]]:
    """Gibt alle Fehler zurück"""
    return ALL_ERRORS


def get_errors_by_category(category: str) -> List[Dict[str, any]]:
    """Gibt alle Fehler einer Kategorie zurück"""
    return [
        error_info
        for error_info in ALL_ERRORS.values()
        if error_info.get("category", "").lower() == category.lower()
    ]

