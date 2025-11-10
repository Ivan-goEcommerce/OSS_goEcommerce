"""
Error Handling System für OSS goEcommerce
Zentrales Fehlerbehandlungssystem mit Fehlercodes und strukturierten Fehlermeldungen
"""

import traceback
import json
import requests
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ErrorCode(Enum):
    """Zentrale Fehlercodes für die gesamte Anwendung"""
    
    # Datenbank-Fehler (1000-1999)
    DB_CONNECTION_FAILED = "DB001"
    DB_AUTHENTICATION_FAILED = "DB002"
    DB_QUERY_SYNTAX_ERROR = "DB003"
    DB_PERMISSION_DENIED = "DB004"
    DB_OBJECT_NOT_FOUND = "DB005"
    DB_TIMEOUT = "DB006"
    DB_TRANSACTION_FAILED = "DB007"
    DB_CONNECTION_STRING_INVALID = "DB008"
    
    # Netzwerk-Fehler (2000-2999)
    NET_TIMEOUT = "NET001"
    NET_CONNECTION_REFUSED = "NET002"
    NET_HTTP_ERROR = "NET003"
    NET_SSL_ERROR = "NET004"
    NET_DNS_ERROR = "NET005"
    
    # Konfigurations-Fehler (3000-3999)
    CONFIG_FILE_NOT_FOUND = "CFG001"
    CONFIG_INVALID_JSON = "CFG002"
    CONFIG_MISSING_KEY = "CFG003"
    CONFIG_CREDENTIALS_MISSING = "CFG004"
    CONFIG_KEYRING_ERROR = "CFG005"
    
    # Validierungs-Fehler (4000-4999)
    VAL_INVALID_INPUT = "VAL001"
    VAL_MISSING_REQUIRED_FIELD = "VAL002"
    VAL_INVALID_FORMAT = "VAL003"
    VAL_OUT_OF_RANGE = "VAL004"
    
    # Workflow-Fehler (5000-5999)
    WF_EXECUTION_FAILED = "WF001"
    WF_NOT_FOUND = "WF002"
    WF_INVALID_STATE = "WF003"
    WF_TIMEOUT = "WF004"
    
    # Allgemeine Fehler (9000-9999)
    GEN_UNEXPECTED_ERROR = "GEN001"
    GEN_NOT_IMPLEMENTED = "GEN002"
    GEN_RESOURCE_NOT_FOUND = "GEN003"
    GEN_PERMISSION_DENIED = "GEN004"


@dataclass
class AppError:
    """Strukturierte Fehlerinformation"""
    code: ErrorCode
    message: str
    details: Optional[str] = None
    original_exception: Optional[Exception] = None
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Fehler zu Dictionary"""
        return {
            'code': self.code.value,
            'message': self.message,
            'details': self.details,
            'context': self.context
        }
    
    def __str__(self) -> str:
        """String-Repräsentation des Fehlers"""
        result = f"[{self.code.value}] {self.message}"
        if self.details:
            result += f"\nDetails: {self.details}"
        return result


class ErrorHandler:
    """Zentraler Fehlerhandler für die Anwendung"""
    
    # Fehler-Mapping: Exception-Typen zu ErrorCodes
    ERROR_MAPPING: Dict[type, ErrorCode] = {
        # pyodbc Fehler
        'pyodbc.OperationalError': ErrorCode.DB_CONNECTION_FAILED,
        'pyodbc.ProgrammingError': ErrorCode.DB_QUERY_SYNTAX_ERROR,
        'pyodbc.IntegrityError': ErrorCode.DB_PERMISSION_DENIED,
        'pyodbc.DatabaseError': ErrorCode.DB_CONNECTION_FAILED,
        
        # requests Fehler
        'requests.exceptions.Timeout': ErrorCode.NET_TIMEOUT,
        'requests.exceptions.ConnectionError': ErrorCode.NET_CONNECTION_REFUSED,
        'requests.exceptions.HTTPError': ErrorCode.NET_HTTP_ERROR,
        'requests.exceptions.SSLError': ErrorCode.NET_SSL_ERROR,
        
        # JSON Fehler
        'json.JSONDecodeError': ErrorCode.CONFIG_INVALID_JSON,
        
        # File Fehler
        'FileNotFoundError': ErrorCode.CONFIG_FILE_NOT_FOUND,
        'PermissionError': ErrorCode.GEN_PERMISSION_DENIED,
    }
    
    @staticmethod
    def handle_exception(
        exception: Exception,
        error_code: Optional[ErrorCode] = None,
        context: Optional[Dict[str, Any]] = None,
        log_level: str = "error"
    ) -> AppError:
        """
        Behandelt eine Exception und erstellt strukturierte Fehlerinformation.
        
        Args:
            exception: Die aufgetretene Exception
            error_code: Optionaler spezifischer Fehlercode
            context: Zusätzlicher Kontext (z.B. SQL-Query, URL, etc.)
            log_level: Logging-Level ('debug', 'info', 'warning', 'error', 'critical')
            
        Returns:
            AppError mit strukturierten Fehlerinformationen
        """
        # Bestimme Fehlercode
        if error_code is None:
            error_code = ErrorHandler._determine_error_code(exception)
        
        # Erstelle Fehlermeldung
        message = ErrorHandler._create_error_message(exception, error_code)
        details = ErrorHandler._extract_error_details(exception)
        
        # Erstelle AppError
        app_error = AppError(
            code=error_code,
            message=message,
            details=details,
            original_exception=exception,
            context=context
        )
        
        # Logge Fehler
        ErrorHandler._log_error(app_error, log_level)
        
        return app_error
    
    @staticmethod
    def _determine_error_code(exception: Exception) -> ErrorCode:
        """Bestimmt Fehlercode basierend auf Exception-Typ"""
        exception_type = type(exception).__name__
        exception_module = type(exception).__module__
        full_name = f"{exception_module}.{exception_type}"
        
        # Prüfe direkte Zuordnung
        if full_name in ErrorHandler.ERROR_MAPPING:
            return ErrorHandler.ERROR_MAPPING[full_name]
        
        # Prüfe Exception-Typ
        if exception_type in ErrorHandler.ERROR_MAPPING:
            return ErrorHandler.ERROR_MAPPING[exception_type]
        
        # Prüfe Fehlermeldung auf bekannte Muster
        error_str = str(exception).lower()
        
        # SQL Server Fehler
        if "18456" in str(exception) or "login failed" in error_str:
            return ErrorCode.DB_AUTHENTICATION_FAILED
        if "42000" in str(exception) or "syntax" in error_str:
            return ErrorCode.DB_QUERY_SYNTAX_ERROR
        if "229" in str(exception) or "230" in str(exception) or "permission" in error_str:
            return ErrorCode.DB_PERMISSION_DENIED
        if "208" in str(exception) or "2812" in str(exception):
            return ErrorCode.DB_OBJECT_NOT_FOUND
        if "timeout" in error_str:
            return ErrorCode.DB_TIMEOUT
        
        # Netzwerk-Fehler
        if "timeout" in error_str and "request" in error_str:
            return ErrorCode.NET_TIMEOUT
        if "connection" in error_str and "refused" in error_str:
            return ErrorCode.NET_CONNECTION_REFUSED
        
        # Standard: Unerwarteter Fehler
        return ErrorCode.GEN_UNEXPECTED_ERROR
    
    @staticmethod
    def _create_error_message(exception: Exception, error_code: ErrorCode) -> str:
        """Erstellt benutzerfreundliche Fehlermeldung"""
        error_messages = {
            ErrorCode.DB_CONNECTION_FAILED: "Datenbankverbindung fehlgeschlagen",
            ErrorCode.DB_AUTHENTICATION_FAILED: "Datenbank-Authentifizierung fehlgeschlagen",
            ErrorCode.DB_QUERY_SYNTAX_ERROR: "SQL-Syntaxfehler",
            ErrorCode.DB_PERMISSION_DENIED: "Keine Berechtigung für diese Operation",
            ErrorCode.DB_OBJECT_NOT_FOUND: "Datenbankobjekt nicht gefunden",
            ErrorCode.DB_TIMEOUT: "Datenbank-Timeout",
            ErrorCode.NET_TIMEOUT: "Netzwerk-Timeout",
            ErrorCode.NET_CONNECTION_REFUSED: "Verbindung abgelehnt",
            ErrorCode.NET_HTTP_ERROR: "HTTP-Fehler",
            ErrorCode.CONFIG_FILE_NOT_FOUND: "Konfigurationsdatei nicht gefunden",
            ErrorCode.CONFIG_INVALID_JSON: "Ungültige JSON-Konfiguration",
            ErrorCode.CONFIG_CREDENTIALS_MISSING: "Anmeldedaten fehlen",
            ErrorCode.CONFIG_MISSING_KEY: "Konfigurationsschlüssel fehlt",
            ErrorCode.CONFIG_KEYRING_ERROR: "Keyring-Fehler",
            ErrorCode.DB_TRANSACTION_FAILED: "Datenbank-Transaktion fehlgeschlagen",
            ErrorCode.DB_CONNECTION_STRING_INVALID: "Ungültige Verbindungszeichenkette",
            ErrorCode.NET_SSL_ERROR: "SSL/TLS-Fehler",
            ErrorCode.NET_DNS_ERROR: "DNS-Auflösungsfehler",
            ErrorCode.VAL_INVALID_INPUT: "Ungültige Eingabe",
            ErrorCode.VAL_MISSING_REQUIRED_FIELD: "Pflichtfeld fehlt",
            ErrorCode.VAL_INVALID_FORMAT: "Ungültiges Format",
            ErrorCode.VAL_OUT_OF_RANGE: "Wert außerhalb des Bereichs",
            ErrorCode.WF_EXECUTION_FAILED: "Workflow-Ausführung fehlgeschlagen",
            ErrorCode.WF_NOT_FOUND: "Workflow nicht gefunden",
            ErrorCode.WF_INVALID_STATE: "Workflow in ungültigem Zustand",
            ErrorCode.WF_TIMEOUT: "Workflow-Timeout",
            ErrorCode.GEN_UNEXPECTED_ERROR: "Unerwarteter Fehler aufgetreten",
            ErrorCode.GEN_NOT_IMPLEMENTED: "Funktion nicht implementiert",
            ErrorCode.GEN_RESOURCE_NOT_FOUND: "Ressource nicht gefunden",
            ErrorCode.GEN_PERMISSION_DENIED: "Keine Berechtigung",
        }
        
        return error_messages.get(error_code, f"Fehler: {str(exception)}")
    
    @staticmethod
    def _extract_error_details(exception: Exception) -> str:
        """Extrahiert detaillierte Fehlerinformationen"""
        error_str = str(exception)
        
        # Für pyodbc: Extrahiere Fehlercode falls vorhanden
        if hasattr(exception, 'args') and len(exception.args) > 0:
            if isinstance(exception.args[0], str) and any(code in exception.args[0] for code in ['18456', '42000', '208', '229', '230']):
                return error_str
        
        return error_str
    
    @staticmethod
    def _log_error(app_error: AppError, log_level: str = "error"):
        """Loggt Fehler mit entsprechendem Level und sendet an Webhook"""
        log_message = f"[{app_error.code.value}] {app_error.message}"
        if app_error.details:
            log_message += f" - {app_error.details}"
        if app_error.context:
            log_message += f" - Context: {app_error.context}"
        
        if app_error.original_exception:
            log_message += f"\nOriginal Exception: {type(app_error.original_exception).__name__}"
            log_message += f"\nTraceback:\n{traceback.format_exc()}"
        
        # Logge mit entsprechendem Level
        log_func = getattr(logger, log_level, logger.error)
        log_func(log_message)
        
        # Sende Fehler an Webhook (asynchron, ohne Blockierung)
        ErrorHandler._send_error_to_webhook(app_error)
    
    @staticmethod
    def _send_error_to_webhook(app_error: AppError):
        """
        Sendet Fehler an den n8n Webhook-Endpoint.
        Wird asynchron ausgeführt und blockiert nicht bei Fehlern.
        """
        try:
            # Lade License-Informationen
            license_number, email = ErrorHandler._load_license_info()
            
            if not license_number or not email:
                logger.debug("Keine Lizenzdaten gefunden, Webhook wird nicht aufgerufen")
                return
            
            # Webhook-URL aus Single-Point-System
            try:
                from app.config.endpoints import EndpointConfig
                webhook_url = EndpointConfig.get_endpoint("error_webhook")
            except (KeyError, ImportError) as e:
                # Fallback auf hardcoded URL falls Endpoint-System nicht verfügbar
                logger.warning(f"Konnte Endpoint nicht aus Config laden, verwende Fallback: {str(e)}")
                webhook_url = "https://agentic.go-ecommerce.de/webhook/v1/oss-error"
            
            # Erstelle Payload mit Fehlerinformationen
            payload = {
                "error_code": app_error.code.value,
                "error_name": app_error.code.name,
                "message": app_error.message,
                "details": app_error.details,
                "context": app_error.context,
                "timestamp": datetime.now().isoformat(),
                "exception_type": type(app_error.original_exception).__name__ if app_error.original_exception else None,
                "exception_module": type(app_error.original_exception).__module__ if app_error.original_exception else None,
                "traceback": traceback.format_exc() if app_error.original_exception else None
            }
            
            # Headers
            headers = {
                'x-license-email': email,
                'x-license-number': license_number,
                'Content-Type': 'application/json'
            }
            
            # Sende Request (mit Timeout, damit es nicht hängt)
            response = requests.post(
                webhook_url,
                headers=headers,
                json=payload,
                timeout=10  # 10 Sekunden Timeout
            )
            
            # Prüfe Response und verarbeite n8n-Output
            if response.status_code == 200:
                logger.debug(f"Fehler erfolgreich an Webhook gesendet: {app_error.code.value}")
                
                # Verarbeite n8n-Response und zeige Error-Code/Beschreibung an
                ErrorHandler._process_webhook_response(response, app_error)
            else:
                logger.warning(f"Webhook antwortete mit Status {response.status_code}: {response.text[:200]}")
                # Versuche trotzdem Response zu verarbeiten
                ErrorHandler._process_webhook_response(response, app_error)
                
        except requests.exceptions.Timeout:
            logger.warning("Timeout beim Senden des Fehlers an Webhook")
        except requests.exceptions.ConnectionError:
            logger.warning("Verbindungsfehler beim Senden des Fehlers an Webhook")
        except Exception as e:
            # WICHTIG: Keine Rekursion! Logge nur, aber rufe handle_error NICHT auf
            logger.warning(f"Fehler beim Senden an Webhook (wird ignoriert): {str(e)}")
    
    @staticmethod
    def _process_webhook_response(response: requests.Response, app_error: AppError):
        """
        Verarbeitet die n8n-Webhook-Response und zeigt Error-Code und Beschreibung an.
        
        Args:
            response: Response-Objekt vom Webhook
            app_error: Der ursprüngliche AppError
        """
        try:
            # Versuche JSON-Response zu parsen
            try:
                response_data = response.json()
            except (ValueError, json.JSONDecodeError):
                # Wenn kein JSON, verwende Text
                response_data = {"raw_response": response.text}
            
            # Extrahiere Error-Code und Beschreibung aus n8n-Response
            error_code = None
            error_description = None
            
            # Verschiedene mögliche Formate der n8n-Response
            if isinstance(response_data, list) and len(response_data) > 0:
                # Format 1: Array (n8n-Format) - nimm erstes Item
                first_item = response_data[0]
                if isinstance(first_item, dict):
                    error_code = first_item.get('error_code') or first_item.get('code') or first_item.get('json', {}).get('error_code')
                    error_description = (
                        first_item.get('description') or 
                        first_item.get('message') or 
                        first_item.get('error') or
                        first_item.get('json', {}).get('description') or
                        first_item.get('json', {}).get('message')
                    )
            elif isinstance(response_data, dict):
                # Format 2: Direkt im Dict
                error_code = response_data.get('error_code') or response_data.get('code')
                error_description = response_data.get('description') or response_data.get('message') or response_data.get('error')
                
                # Format 3: In einem 'data' oder 'result' Feld
                if not error_code and 'data' in response_data:
                    data = response_data['data']
                    if isinstance(data, dict):
                        error_code = data.get('error_code') or data.get('code')
                        error_description = data.get('description') or data.get('message')
            
            # Zeige Dialog mit Error-Code und Beschreibung
            if error_code or error_description:
                ErrorHandler._show_error_dialog(error_code, error_description, response_data, app_error)
            else:
                # Keine strukturierten Daten, zeige vollständige Response
                logger.debug(f"n8n-Response enthält keine strukturierten Error-Daten: {response_data}")
                ErrorHandler._show_error_dialog(None, None, response_data, app_error)
                
        except Exception as e:
            # Fehler beim Verarbeiten der Response - logge nur, keine Rekursion
            logger.warning(f"Fehler beim Verarbeiten der Webhook-Response: {str(e)}")
    
    @staticmethod
    def _show_error_dialog(error_code: Optional[str], error_description: Optional[str], 
                          response_data: Any, app_error: AppError):
        """
        Zeigt einen Dialog mit Error-Code und Beschreibung aus der n8n-Response.
        Wird sicher im Main-Thread ausgeführt.
        
        Args:
            error_code: Error-Code aus n8n-Response
            error_description: Beschreibung aus n8n-Response
            response_data: Vollständige Response-Daten
            app_error: Der ursprüngliche AppError
        """
        try:
            from PySide6.QtWidgets import QMessageBox, QApplication
            from PySide6.QtCore import QThread, QTimer
            import json
            
            # Prüfe ob QApplication existiert
            app = QApplication.instance()
            if app is None:
                logger.debug("Keine QApplication-Instanz gefunden, Dialog wird nicht angezeigt")
                return
            
            # Prüfe ob App noch läuft (nicht beim Shutdown)
            try:
                if not app.thread().isRunning():
                    logger.debug("QApplication-Thread läuft nicht mehr, Dialog wird nicht angezeigt")
                    return
            except Exception:
                logger.debug("Fehler beim Prüfen des QApplication-Threads, Dialog wird nicht angezeigt")
                return
            
            # Prüfe ob wir im Main-Thread sind
            current_thread = QThread.currentThread()
            main_thread = app.thread()
            
            # Wenn nicht im Main-Thread, verwende QTimer um im Main-Thread auszuführen
            if current_thread != main_thread:
                logger.debug("Nicht im Main-Thread - verwende QTimer für Dialog-Anzeige")
                
                # Erstelle Closure mit Kopien der Daten (Thread-sicher)
                error_code_copy = str(error_code) if error_code else None
                error_description_copy = str(error_description) if error_description else None
                response_data_copy = None
                try:
                    # Versuche Response-Daten zu kopieren (begrenzt)
                    if response_data:
                        if isinstance(response_data, (dict, list)):
                            import copy
                            response_data_copy = copy.deepcopy(response_data)
                        else:
                            response_data_copy = str(response_data)[:1000]  # Begrenze
                except Exception:
                    response_data_copy = str(response_data)[:1000] if response_data else None
                
                app_error_code = app_error.code.value
                app_error_message = app_error.message[:500]  # Begrenze
                
                def show_dialog_in_main_thread():
                    """Wird im Main-Thread ausgeführt"""
                    try:
                        # Erstelle temporäres AppError-Objekt für Dialog
                        temp_app_error = AppError(
                            code=app_error.code,
                            message=app_error_message,
                            details=app_error.details,
                            original_exception=None,
                            context=app_error.context
                        )
                        ErrorHandler._create_and_show_dialog(
                            error_code_copy, 
                            error_description_copy, 
                            response_data_copy, 
                            temp_app_error
                        )
                    except Exception as e:
                        logger.warning(f"Fehler beim Anzeigen des Error-Dialogs im Main-Thread: {str(e)}", exc_info=True)
                
                # Führe im Main-Thread aus (asynchron)
                QTimer.singleShot(100, show_dialog_in_main_thread)  # 100ms Verzögerung für Sicherheit
            else:
                # Wir sind bereits im Main-Thread
                ErrorHandler._create_and_show_dialog(error_code, error_description, response_data, app_error)
            
        except Exception as e:
            # Fehler beim Anzeigen des Dialogs - logge nur, keine Rekursion
            logger.warning(f"Fehler beim Anzeigen des Error-Dialogs: {str(e)}", exc_info=True)
    
    @staticmethod
    def _create_and_show_dialog(error_code: Optional[str], error_description: Optional[str], 
                                response_data: Any, app_error: AppError):
        """
        Erstellt und zeigt den Dialog (muss im Main-Thread aufgerufen werden).
        Zeigt nur Original Error-Code und Original Message.
        
        Args:
            error_code: Error-Code aus n8n-Response (wird nicht angezeigt)
            error_description: Beschreibung aus n8n-Response (wird nicht angezeigt)
            response_data: Vollständige Response-Daten (wird nicht angezeigt)
            app_error: Der ursprüngliche AppError
        """
        try:
            from PySide6.QtWidgets import QMessageBox
            
            # Erstelle Dialog
            msg_box = QMessageBox()
            msg_box.setWindowTitle("📋 n8n Webhook Response")
            
            # Erstelle Nachricht - nur Original Error-Code und Original Message
            message_parts = []
            message_parts.append(f"🔴 Error-Code: {app_error.code.value}")
            message_parts.append(f"\n📝 Message: {app_error.message}")
            
            # Setze Text
            full_message = "\n".join(message_parts)
            
            msg_box.setText(full_message)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setStandardButtons(QMessageBox.Ok)
            
            # Setze Farbschema (falls verfügbar) - mit Fehlerbehandlung
            try:
                from app.config import get_color_scheme
                from PySide6.QtGui import QPalette, QColor
                color_scheme = get_color_scheme()
                palette = QPalette()
                palette.setColor(QPalette.Window, QColor(color_scheme["window"]))
                palette.setColor(QPalette.WindowText, QColor(color_scheme["window_text"]))
                msg_box.setPalette(palette)
            except Exception:
                pass  # Ignoriere Fehler beim Setzen des Farbschemas
            
            # Zeige Dialog (blockierend, aber sicher im Main-Thread)
            msg_box.exec()
            
        except Exception as e:
            # Fehler beim Erstellen/Anzeigen des Dialogs - logge nur
            logger.warning(f"Fehler beim Erstellen des Error-Dialogs: {str(e)}", exc_info=True)
    
    @staticmethod
    def _load_license_info() -> Tuple[Optional[str], Optional[str]]:
        """
        Lädt License-Informationen aus dem LicenseManager.
        Gibt (None, None) zurück wenn nicht verfügbar.
        """
        try:
            from app.managers.license_manager import LicenseManager
            license_manager = LicenseManager()
            license_number, email = license_manager.load_license()
            return license_number, email
        except Exception as e:
            logger.debug(f"Konnte License-Informationen nicht laden: {str(e)}")
            return None, None


def handle_error(
    exception: Exception,
    error_code: Optional[ErrorCode] = None,
    context: Optional[Dict[str, Any]] = None,
    log_level: str = "error"
) -> AppError:
    """
    Convenience-Funktion für Fehlerbehandlung.
    
    Usage:
        try:
            # Code
        except Exception as e:
            error = handle_error(e, context={'query': sql_query})
            return False, error.message
    """
    return ErrorHandler.handle_exception(exception, error_code, context, log_level)


def get_error_info(error_code: ErrorCode) -> Dict[str, str]:
    """
    Gibt Informationen zu einem Fehlercode zurück.
    Wird für die statische Fehlerliste verwendet.
    """
    return {
        'code': error_code.value,
        'description': ErrorHandler._create_error_message(Exception(), error_code),
        'category': ErrorHandler._get_error_category(error_code)
    }


def _get_error_category(error_code: ErrorCode) -> str:
    """Gibt Kategorie eines Fehlercodes zurück"""
    code_value = error_code.value
    
    if code_value.startswith('DB'):
        return 'Datenbank'
    elif code_value.startswith('NET'):
        return 'Netzwerk'
    elif code_value.startswith('CFG'):
        return 'Konfiguration'
    elif code_value.startswith('VAL'):
        return 'Validierung'
    elif code_value.startswith('WF'):
        return 'Workflow'
    else:
        return 'Allgemein'


# Alias für Kompatibilität
ErrorHandler._get_error_category = staticmethod(_get_error_category)


def install_global_exception_handler():
    """
    Installiert einen globalen Exception Handler, der ALLE unhandled exceptions erfasst.
    Muss beim App-Start aufgerufen werden.
    """
    import sys
    
    # Speichere den originalen excepthook
    original_excepthook = sys.excepthook
    
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        """
        Globaler Exception Handler für alle unhandled exceptions.
        """
        # Erstelle Exception-Objekt aus den Parametern
        if exc_value is None:
            exception = exc_type()
        else:
            exception = exc_value
        
        # Behandle den Fehler mit unserem Error-Handler
        # WICHTIG: Verwende GEN_UNEXPECTED_ERROR für unhandled exceptions
        error = handle_error(
            exception,
            error_code=ErrorCode.GEN_UNEXPECTED_ERROR,
            context={
                'exception_type': exc_type.__name__,
                'exception_module': exc_type.__module__,
                'unhandled': True
            },
            log_level="critical"
        )
        
        # Rufe auch den originalen excepthook auf (für Standard-Python-Ausgabe)
        original_excepthook(exc_type, exc_value, exc_traceback)
    
    # Installiere den globalen Handler
    sys.excepthook = global_exception_handler
    logger.info("Globaler Exception Handler installiert")


def install_qt_exception_handler(app):
    """
    Installiert einen Exception Handler für Qt-spezifische Exceptions.
    Überschreibt QApplication.notify() um auch Qt-Exceptions zu erfassen.
    
    Args:
        app: QApplication-Instanz
    """
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QObject, QEvent
    
    if not isinstance(app, QApplication):
        logger.warning("install_qt_exception_handler: app ist keine QApplication-Instanz")
        return
    
    # Speichere die originale notify-Methode
    original_notify = app.notify
    
    def qt_notify_wrapper(obj: QObject, event: QEvent) -> bool:
        """
        Wrapper für QApplication.notify() um Exceptions zu erfassen.
        """
        try:
            return original_notify(obj, event)
        except Exception as e:
            # Erfasse Qt-Exceptions
            error = handle_error(
                e,
                error_code=ErrorCode.GEN_UNEXPECTED_ERROR,
                context={
                    'qt_object': type(obj).__name__,
                    'event_type': type(event).__name__,
                    'qt_exception': True
                },
                log_level="critical"
            )
            # Re-raise die Exception (Qt erwartet das)
            raise
    
    # Überschreibe notify
    app.notify = qt_notify_wrapper
    logger.info("Qt Exception Handler installiert")
