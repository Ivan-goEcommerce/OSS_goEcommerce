"""
Database Service für OSS goEcommerce
Verwaltet JTL-Datenbankverbindungen mit sicherer Passwort-Speicherung
Refactored from jtl_database_manager.py
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import keyring
import pyodbc

from app.core.logging_config import get_logger
from app.core.error_handler import handle_error, ErrorCode

logger = get_logger(__name__)


class DatabaseService:
    """
    Service für JTL-Datenbankverbindung mit sicherer Passwort-Speicherung.
    
    Verwaltet:
    - Datenbankverbindungen
    - Passwort-Speicherung im Keyring
    - Konfigurationsdateien
    - SQL-Abfragen
    """
    
    def __init__(self, config_file: str = 'jtl_config.json'):
        """
        Initialisiert den Database Service.
        
        Args:
            config_file: Pfad zur Konfigurationsdatei
        """
        self.config_file = Path(config_file)
        self.service_name = 'OSS_goEcommerce_JTL'
        self.config = self._load_config()
        logger.debug(f"DatabaseService initialisiert - Server: {self.config.get('server', 'N/A')}")
    
    def _load_config(self) -> Dict:
        """
        Lädt Verbindungseinstellungen aus JSON-Datei.
        
        Returns:
            Dictionary mit Konfiguration oder Standard-Konfiguration
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.info("Konfiguration erfolgreich geladen")
                    return config
            except json.JSONDecodeError as e:
                error = handle_error(
                    e,
                    error_code=ErrorCode.CONFIG_INVALID_JSON,
                    context={'config_file': str(self.config_file), 'operation': 'load_config'},
                    log_level="error"
                )
                logger.error(f"JSON-Fehler beim Laden der Konfiguration: {error.message}")
                return self._get_default_config()
            except FileNotFoundError as e:
                error = handle_error(
                    e,
                    error_code=ErrorCode.CONFIG_FILE_NOT_FOUND,
                    context={'config_file': str(self.config_file), 'operation': 'load_config'},
                    log_level="warning"
                )
                logger.warning(f"Konfigurationsdatei nicht gefunden: {error.message}")
                return self._get_default_config()
            except Exception as e:
                error = handle_error(
                    e,
                    error_code=ErrorCode.GEN_UNEXPECTED_ERROR,
                    context={'config_file': str(self.config_file), 'operation': 'load_config'},
                    log_level="error"
                )
                logger.error(f"Fehler beim Laden der Konfiguration: {error.message}", exc_info=True)
                return self._get_default_config()
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """
        Gibt Standard-Konfiguration zurück.
        
        Returns:
            Dictionary mit Standard-Einstellungen
        """
        return {
            'server': r'.\JTLWAWI',
            'database': 'eazybusiness',
            'username': 'sa',
            'driver': 'py-mssql',  # Immer py-mssql Driver verwenden
            'last_tested': None
        }
    
    def save_config(
        self,
        server: str,
        username: str,
        database: str,
        driver: str = 'py-mssql'  # Immer py-mssql Driver verwenden
    ) -> bool:
        """
        Speichert Verbindungseinstellungen in JSON-Datei.
        
        Args:
            server: SQL Server Adresse
            username: Benutzername
            database: Datenbankname
            driver: ODBC Driver Name
            
        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        try:
            self.config = {
                'server': server,
                'username': username,
                'database': database,
                'driver': driver,
                'last_tested': datetime.now().isoformat()
            }
            
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info("Konfiguration erfolgreich gespeichert")
            return True
        except (IOError, OSError) as e:
            error = handle_error(
                e,
                error_code=ErrorCode.CONFIG_FILE_NOT_FOUND,
                context={'config_file': str(self.config_file), 'operation': 'save_config'},
                log_level="error"
            )
            logger.error(f"Datei-Fehler beim Speichern der Konfiguration: {error.message}")
            return False
        except json.JSONEncodeError as e:
            error = handle_error(
                e,
                error_code=ErrorCode.CONFIG_INVALID_JSON,
                context={'config_file': str(self.config_file), 'operation': 'save_config'},
                log_level="error"
            )
            logger.error(f"JSON-Fehler beim Speichern der Konfiguration: {error.message}")
            return False
        except Exception as e:
            error = handle_error(
                e,
                error_code=ErrorCode.GEN_UNEXPECTED_ERROR,
                context={'config_file': str(self.config_file), 'operation': 'save_config'},
                log_level="error"
            )
            logger.error(f"Fehler beim Speichern der Konfiguration: {error.message}", exc_info=True)
            return False
    
    def save_password(self, password: str) -> bool:
        """
        Speichert Passwort sicher im Keyring.
        
        Args:
            password: Zu speicherndes Passwort
            
        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        try:
            username_key = f"{self.config['server']}:{self.config['username']}"
            keyring.set_password(self.service_name, username_key, password)
            logger.info("Passwort erfolgreich im Keyring gespeichert")
            return True
        except keyring.errors.KeyringError as e:
            error = handle_error(
                e,
                error_code=ErrorCode.CONFIG_KEYRING_ERROR,
                context={'operation': 'save_password'},
                log_level="error"
            )
            logger.error(f"Keyring-Fehler beim Speichern des Passworts: {error.message}")
            return False
        except Exception as e:
            error = handle_error(
                e,
                error_code=ErrorCode.GEN_UNEXPECTED_ERROR,
                context={'operation': 'save_password'},
                log_level="error"
            )
            logger.error(f"Fehler beim Speichern des Passworts: {error.message}", exc_info=True)
            return False
    
    def get_password(self) -> Optional[str]:
        """
        Holt Passwort aus dem Keyring.
        
        Returns:
            Passwort oder None wenn nicht gefunden
        """
        try:
            username_key = f"{self.config['server']}:{self.config['username']}"
            password = keyring.get_password(self.service_name, username_key)
            if password:
                logger.debug("Passwort erfolgreich aus Keyring geladen")
            else:
                logger.warning("Kein Passwort im Keyring gefunden")
            return password
        except keyring.errors.KeyringError as e:
            error = handle_error(
                e,
                error_code=ErrorCode.CONFIG_KEYRING_ERROR,
                context={'operation': 'get_password'},
                log_level="error"
            )
            logger.error(f"Keyring-Fehler beim Abrufen des Passworts: {error.message}")
            return None
        except Exception as e:
            error = handle_error(
                e,
                error_code=ErrorCode.GEN_UNEXPECTED_ERROR,
                context={'operation': 'get_password'},
                log_level="error"
            )
            logger.error(f"Fehler beim Abrufen des Passworts: {error.message}", exc_info=True)
            return None
    
    def _build_connection_string(
        self,
        server: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        driver: Optional[str] = None
    ) -> str:
        """
        Erstellt SQL Server Verbindungsstring.
        
        Args:
            server: Server-Adresse (optional)
            username: Benutzername (optional)
            password: Passwort (optional)
            database: Datenbankname (optional)
            driver: ODBC Driver (optional)
            
        Returns:
            Verbindungsstring für pyodbc
        """
        test_server = server or self.config['server']
        test_username = username or self.config['username']
        test_password = password or self.get_password()
        test_database = database or self.config.get('database', '')
        test_driver = driver or self.config['driver']
        
        # DEBUG: Zeige verwendete Credentials (ohne Passwort)
        logger.debug(f"Erstelle Connection String - Server: {test_server}, Username: {test_username}, Database: {test_database}")
        if not test_password:
            logger.error("WICHTIG: Kein Passwort gefunden! Passwort muss im Keyring gespeichert sein.")
        else:
            logger.debug(f"Passwort vorhanden: {'Ja' if test_password else 'Nein'} (Länge: {len(test_password) if test_password else 0})")
        
        connection_string = (
            f"DRIVER={{{test_driver}}};"
            f"SERVER={test_server};"
            f"DATABASE={test_database};" if test_database else ""
            f"UID={test_username};"
            f"PWD={test_password or ''};"
            f"Trusted_Connection=no;"
        )
        
        return connection_string
    
    def test_connection(
        self,
        server: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        driver: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Testet SQL Server-Verbindung.
        
        Args:
            server: Server-Adresse (optional, verwendet Config wenn None)
            username: Benutzername (optional)
            password: Passwort (optional)
            database: Datenbankname (optional)
            driver: ODBC Driver (optional)
            
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            test_password = password or self.get_password()
            
            if not test_password:
                logger.warning("Kein Passwort verfügbar für Verbindungstest")
                return False, "Kein Passwort im Keyring gefunden"
            
            connection_string = self._build_connection_string(
                server, username, test_password, database, driver
            )
            
            logger.debug("Starte Verbindungstest...")
            connection = pyodbc.connect(connection_string, timeout=10)
            
            # Einfache Abfrage zum Testen
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            
            logger.info("Verbindungstest erfolgreich")
            return True, "Verbindung erfolgreich"
            
        except pyodbc.OperationalError as e:
            error_str = str(e)
            # Bestimme spezifischen ErrorCode
            if "18456" in error_str or "Login failed" in error_str:
                error_code = ErrorCode.DB_AUTHENTICATION_FAILED
            elif "timeout" in error_str.lower():
                error_code = ErrorCode.DB_TIMEOUT
            else:
                error_code = ErrorCode.DB_CONNECTION_FAILED
            
            error = handle_error(
                e,
                error_code=error_code,
                context={
                    'operation': 'test_connection',
                    'server': server or self.config.get('server'),
                    'username': username or self.config.get('username'),
                    'connection_string': connection_string[:100] if 'connection_string' in locals() else None
                },
                log_level="error"
            )
            logger.error(f"SQL Server-Fehler: {error.message}")
            
            # Spezielle Behandlung für Fehler 18456 (Authentifizierungsfehler)
            if "18456" in error_str or "Login failed" in error_str:
                used_server = server or self.config.get('server')
                used_username = username or self.config.get('username')
                logger.error("Fehler 18456: SQL Server Authentifizierung fehlgeschlagen!")
                logger.error(f"Verwendete Credentials - Server: {used_server}, Username: {used_username}")
                return False, f"Authentifizierungsfehler (18456): Passwort oder Benutzername falsch. Bitte prüfen Sie die DB-Credentials. Details: {error_str}"
            
            return False, error.message
        except pyodbc.Error as e:
            error = handle_error(
                e,
                error_code=ErrorCode.DB_CONNECTION_FAILED,
                context={
                    'operation': 'test_connection',
                    'server': server or self.config.get('server'),
                    'username': username or self.config.get('username')
                },
                log_level="error"
            )
            logger.error(f"SQL Server-Fehler: {error.message}")
            return False, error.message
        except Exception as e:
            error = handle_error(
                e,
                error_code=ErrorCode.GEN_UNEXPECTED_ERROR,
                context={'operation': 'test_connection'},
                log_level="error"
            )
            logger.error(f"Verbindungsfehler: {error.message}", exc_info=True)
            return False, error.message
    
    def get_available_databases(
        self,
        server: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        driver: Optional[str] = None
    ) -> List[str]:
        """
        Holt alle verfügbaren Datenbanken (außer System-Datenbanken).
        
        Args:
            server: Server-Adresse (optional)
            username: Benutzername (optional)
            password: Passwort (optional)
            driver: ODBC Driver (optional)
            
        Returns:
            Liste von Datenbanknamen
        """
        try:
            test_password = password or self.get_password()
            
            if not test_password:
                logger.warning("Kein Passwort verfügbar")
                return []
            
            connection_string = self._build_connection_string(
                server, username, test_password, None, driver
            )
            
            logger.debug("Lade verfügbare Datenbanken...")
            connection = pyodbc.connect(connection_string, timeout=10)
            cursor = connection.cursor()
            
            # SQL Server spezifische Abfrage für Datenbanken
            cursor.execute("SELECT name FROM sys.databases WHERE database_id > 4")
            databases = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            connection.close()
            
            logger.info(f"{len(databases)} Datenbanken gefunden")
            return databases
            
        except pyodbc.OperationalError as e:
            error = handle_error(
                e,
                error_code=ErrorCode.DB_CONNECTION_FAILED,
                context={'operation': 'get_available_databases'},
                log_level="error"
            )
            logger.error(f"Verbindungsfehler beim Abrufen der Datenbanken: {error.message}")
            return []
        except pyodbc.Error as e:
            error = handle_error(
                e,
                error_code=ErrorCode.DB_CONNECTION_FAILED,
                context={'operation': 'get_available_databases'},
                log_level="error"
            )
            logger.error(f"SQL-Fehler beim Abrufen der Datenbanken: {error.message}")
            return []
        except Exception as e:
            error = handle_error(
                e,
                error_code=ErrorCode.GEN_UNEXPECTED_ERROR,
                context={'operation': 'get_available_databases'},
                log_level="error"
            )
            logger.error(f"Verbindungsfehler: {error.message}", exc_info=True)
            return []
    
    def execute_query(self, sql_query: str) -> Tuple[bool, str, Optional[List]]:
        """
        Führt eine SQL-Abfrage auf der JTL-Datenbank aus.
        Unterstützt mehrere SQL-Batches (getrennt durch GO).
        
        Args:
            sql_query: SQL-Abfrage als String (kann mehrere Batches mit GO enthalten)
            
        Returns:
            Tuple (success: bool, message: str, results: Optional[List])
        """
        try:
            connection_string = self._build_connection_string()
            
            # Teile SQL-Query in einzelne Batches (bei GO)
            batches = self._split_sql_batches(sql_query)
            
            if not batches:
                return False, "Keine SQL-Befehle gefunden", None
            
            logger.debug(f"Führe {len(batches)} SQL-Batch(es) aus...")
            
            connection = pyodbc.connect(connection_string, timeout=30)  # Längere Timeout für Trigger
            cursor = connection.cursor()
            
            results = None
            last_rowcount = 0
            executed_batches = 0
            
            # Führe jeden Batch einzeln aus
            for i, batch in enumerate(batches, 1):
                batch = batch.strip()
                if not batch:
                    continue
                
                logger.debug(f"Führe Batch {i}/{len(batches)} aus: {batch[:100]}...")
                
                try:
                    cursor.execute(batch)
                    
                    # Versuche Ergebnisse abzurufen (funktioniert nur bei SELECT)
                    try:
                        batch_results = cursor.fetchall()
                        if batch_results is not None:
                            results = batch_results
                    except pyodbc.ProgrammingError:
                        # Bei INSERT/UPDATE/DELETE/DDL gibt es keine Ergebnisse
                        last_rowcount = cursor.rowcount
                        connection.commit()  # Commit nach jedem Batch
                    
                    executed_batches += 1
                    
                except pyodbc.ProgrammingError as e:
                    error_str = str(e)
                    error_code = getattr(e, 'args', [None])[0] if hasattr(e, 'args') and len(e.args) > 0 else None
                    
                    # Verwende unser Fehlerbehandlungssystem
                    app_error = handle_error(
                        e,
                        error_code=ErrorCode.DB_QUERY_SYNTAX_ERROR,
                        context={
                            'operation': 'execute_query',
                            'batch_num': i,
                            'total_batches': len(batches),
                            'sql_batch': batch[:200]
                        },
                        log_level="error"
                    )
                    logger.error(f"SQL-Syntaxfehler in Batch {i}/{len(batches)}: {app_error.message}")
                    
                    # Cleanup
                    try:
                        cursor.close()
                        connection.close()
                    except:
                        pass
                    
                    # Detaillierte Fehleranalyse
                    error_message = self._analyze_sql_error(error_str, error_code, batch, i, len(batches))
                    return False, error_message, None
                except pyodbc.Error as e:
                    error_str = str(e)
                    error_code = getattr(e, 'args', [None])[0] if hasattr(e, 'args') and len(e.args) > 0 else None
                    
                    # Bestimme ErrorCode basierend auf Fehlertyp
                    if "18456" in error_str or "Login failed" in error_str:
                        db_error_code = ErrorCode.DB_AUTHENTICATION_FAILED
                    elif "229" in error_str or "230" in error_str or "permission" in error_str.lower():
                        db_error_code = ErrorCode.DB_PERMISSION_DENIED
                    elif "208" in error_str or "2812" in error_str:
                        db_error_code = ErrorCode.DB_OBJECT_NOT_FOUND
                    elif "timeout" in error_str.lower():
                        db_error_code = ErrorCode.DB_TIMEOUT
                    else:
                        db_error_code = ErrorCode.DB_CONNECTION_FAILED
                    
                    # Verwende unser Fehlerbehandlungssystem
                    app_error = handle_error(
                        e,
                        error_code=db_error_code,
                        context={
                            'operation': 'execute_query',
                            'batch_num': i,
                            'total_batches': len(batches),
                            'sql_batch': batch[:200],
                            'error_code': error_code
                        },
                        log_level="error"
                    )
                    logger.error(f"SQL-Fehler in Batch {i}/{len(batches)}: {app_error.message}")
                    
                    # Cleanup
                    try:
                        cursor.close()
                        connection.close()
                    except:
                        pass
                    
                    # Detaillierte Fehleranalyse
                    error_message = self._analyze_sql_error(error_str, error_code, batch, i, len(batches))
                    return False, error_message, None
            
            # Finales Commit und Cleanup
            connection.commit()
            cursor.close()
            connection.close()
            
            # Bestimme Ergebnis-Meldung
            if results is not None:
                result_message = f"Alle Batches erfolgreich ausgeführt - {len(results)} Ergebnisse"
            elif last_rowcount > 0:
                result_message = f"Alle Batches erfolgreich ausgeführt - {last_rowcount} Zeilen betroffen"
            else:
                result_message = f"Alle {executed_batches} Batch(es) erfolgreich ausgeführt"
            
            logger.info(result_message)
            return True, result_message, results if results is not None else last_rowcount
            
        except pyodbc.OperationalError as e:
            error_str = str(e)
            error_code = getattr(e, 'args', [None])[0] if hasattr(e, 'args') and len(e.args) > 0 else None
            
            # Bestimme ErrorCode
            if "18456" in error_str or "Login failed" in error_str:
                db_error_code = ErrorCode.DB_AUTHENTICATION_FAILED
            elif "timeout" in error_str.lower():
                db_error_code = ErrorCode.DB_TIMEOUT
            else:
                db_error_code = ErrorCode.DB_CONNECTION_FAILED
            
            app_error = handle_error(
                e,
                error_code=db_error_code,
                context={
                    'operation': 'execute_query',
                    'sql_query': sql_query[:200]
                },
                log_level="error"
            )
            logger.error(f"SQL Server-Verbindungsfehler: {app_error.message}")
            
            error_message = self._analyze_sql_error(error_str, error_code, sql_query[:200], 1, 1)
            return False, error_message, None
        except pyodbc.Error as e:
            error_str = str(e)
            error_code = getattr(e, 'args', [None])[0] if hasattr(e, 'args') and len(e.args) > 0 else None
            
            # Bestimme ErrorCode
            if "42000" in error_str or "syntax" in error_str.lower():
                db_error_code = ErrorCode.DB_QUERY_SYNTAX_ERROR
            elif "229" in error_str or "230" in error_str or "permission" in error_str.lower():
                db_error_code = ErrorCode.DB_PERMISSION_DENIED
            elif "208" in error_str or "2812" in error_str:
                db_error_code = ErrorCode.DB_OBJECT_NOT_FOUND
            else:
                db_error_code = ErrorCode.DB_CONNECTION_FAILED
            
            app_error = handle_error(
                e,
                error_code=db_error_code,
                context={
                    'operation': 'execute_query',
                    'sql_query': sql_query[:200],
                    'error_code': error_code
                },
                log_level="error"
            )
            logger.error(f"SQL Server-Fehler: {app_error.message}")
            
            error_message = self._analyze_sql_error(error_str, error_code, sql_query[:200], 1, 1)
            return False, error_message, None
        except Exception as e:
            error = handle_error(
                e,
                error_code=ErrorCode.GEN_UNEXPECTED_ERROR,
                context={'operation': 'execute_query'},
                log_level="error"
            )
            logger.error(f"Verbindungsfehler: {error.message}", exc_info=True)
            return False, error.message, None
    
    def _analyze_sql_error(self, error_str: str, error_code: Optional[str], sql_batch: str, batch_num: int, total_batches: int) -> str:
        """
        Analysiert SQL-Fehler und gibt detaillierte Fehlermeldungen zurück.
        
        Args:
            error_str: Fehler-String
            error_code: ODBC-Fehlercode (falls vorhanden)
            sql_batch: SQL-Batch, der den Fehler verursacht hat
            batch_num: Batch-Nummer
            total_batches: Gesamtanzahl Batches
            
        Returns:
            Detaillierte Fehlermeldung
        """
        error_lower = error_str.lower()
        
        # 1. Authentifizierungsfehler (18456)
        if "18456" in error_str or "login failed" in error_lower or "authentifizierungsfehler" in error_lower:
            return (
                f"❌ SQL Server Authentifizierungsfehler (Fehler 18456)\n\n"
                f"Details: {error_str}\n\n"
                f"Mögliche Ursachen:\n"
                f"  • Passwort ist falsch oder fehlt im Keyring\n"
                f"  • Benutzername hat keine Berechtigung\n"
                f"  • SQL Server Authentifizierung ist nicht aktiviert\n\n"
                f"Lösung: Prüfen Sie die DB-Credentials über 'DB Credentials' im Dashboard."
            )
        
        # 2. Syntaxfehler (42000, 102, 156, etc.)
        if "42000" in error_str or "102" in error_str or "156" in error_str or "syntax" in error_lower:
            return (
                f"❌ SQL-Syntaxfehler in Batch {batch_num}/{total_batches}\n\n"
                f"Fehlercode: {error_code or '42000'}\n"
                f"Details: {error_str}\n\n"
                f"Häufige Ursachen:\n"
                f"  • Falsche Schreibweise von SQL-Befehlen\n"
                f"  • Fehlende oder zusätzliche Leerzeichen\n"
                f"  • Fehlende Klammern oder Anführungszeichen\n"
                f"  • Fehlendes BEGIN nach AS in CREATE TRIGGER\n"
                f"  • Fehlendes END vor GO\n\n"
                f"Fehlerhafter SQL-Batch:\n{sql_batch[:300]}{'...' if len(sql_batch) > 300 else ''}"
            )
        
        # 3. Zugriffsverletzung / Berechtigungsfehler (229, 230, 300, etc.)
        if "229" in error_str or "230" in error_str or "300" in error_str or "permission" in error_lower or "berechtigung" in error_lower or "zugriff" in error_lower:
            return (
                f"❌ Zugriffsverletzung / Berechtigungsfehler in Batch {batch_num}/{total_batches}\n\n"
                f"Fehlercode: {error_code or '229/230'}\n"
                f"Details: {error_str}\n\n"
                f"Der Benutzer hat nicht die erforderlichen Berechtigungen:\n"
                f"  • CREATE TRIGGER Berechtigung fehlt\n"
                f"  • ALTER TABLE Berechtigung fehlt\n"
                f"  • db_ddladmin Rolle fehlt\n\n"
                f"Lösung:\n"
                f"  1. Führen Sie als Administrator aus:\n"
                f"     GRANT ALTER ON OBJECT::[dbo].[tArtikel] TO [IhrBenutzer];\n"
                f"     ALTER ROLE db_ddladmin ADD MEMBER [IhrBenutzer];\n"
                f"  2. Oder verwenden Sie das Skript: grant_trigger_permissions.sql"
            )
        
        # 4. Objekt nicht gefunden (208, 2812)
        if "208" in error_str or "2812" in error_str or ("object" in error_lower and "not found" in error_lower):
            return (
                f"❌ Objekt nicht gefunden in Batch {batch_num}/{total_batches}\n\n"
                f"Fehlercode: {error_code or '208'}\n"
                f"Details: {error_str}\n\n"
                f"Das angeforderte Objekt (Tabelle, Trigger, etc.) existiert nicht.\n"
                f"Prüfen Sie:\n"
                f"  • Objektname ist korrekt geschrieben\n"
                f"  • Datenbank ist korrekt\n"
                f"  • Schema ist korrekt (z.B. dbo.tArtikel)"
            )
        
        # 5. Allgemeiner SQL-Fehler
        batch_info = f" (Batch {batch_num}/{total_batches})" if total_batches > 1 else ""
        return (
            f"❌ SQL Server-Fehler{batch_info}\n\n"
            f"Fehlercode: {error_code or 'Unbekannt'}\n"
            f"Details: {error_str}\n\n"
            f"Fehlerhafter SQL-Batch:\n{sql_batch[:300]}{'...' if len(sql_batch) > 300 else ''}"
        )
    
    def _split_sql_batches(self, sql_query: str) -> List[str]:
        """
        Teilt SQL-Query in einzelne Batches auf (getrennt durch GO).
        GO ist ein Batch-Separator, kein T-SQL-Befehl.
        
        Args:
            sql_query: SQL-Query mit möglichen GO-Trennern
            
        Returns:
            Liste von SQL-Batches (ohne GO)
        """
        import re
        
        # Teile bei GO (case-insensitive, mit oder ohne Semikolon davor)
        # GO muss am Anfang einer Zeile stehen (optional mit Whitespace davor)
        pattern = r'^\s*GO\s*;?\s*$'
        
        batches = []
        current_batch = []
        
        for line in sql_query.split('\n'):
            # Prüfe ob Zeile nur GO (mit optionalem Semikolon) enthält
            if re.match(pattern, line, re.IGNORECASE):
                # Wenn aktueller Batch Inhalt hat, speichere ihn
                if current_batch:
                    batch_text = '\n'.join(current_batch).strip()
                    if batch_text:
                        batches.append(batch_text)
                    current_batch = []
            else:
                # Füge Zeile zum aktuellen Batch hinzu
                current_batch.append(line)
        
        # Füge letzten Batch hinzu (falls vorhanden)
        if current_batch:
            batch_text = '\n'.join(current_batch).strip()
            if batch_text:
                batches.append(batch_text)
        
        # Wenn keine GO gefunden wurde, gibt den gesamten Query als einen Batch zurück
        if not batches:
            sql_query_stripped = sql_query.strip()
            if sql_query_stripped:
                batches.append(sql_query_stripped)
        
        return batches
    
    def get_article_count_with_taric(self) -> Tuple[bool, str, Optional[int]]:
        """
        Spezifische JTL-Abfrage: Anzahl Artikel mit ctaric.
        
        Returns:
            Tuple (success: bool, message: str, count: Optional[int])
        """
        sql_query = "SELECT DISTINCT COUNT(ctaric) FROM tartikel WHERE ctaric != ''"
        success, message, results = self.execute_query(sql_query)
        
        if success and results and len(results) > 0:
            count = results[0][0]
            logger.info(f"Anzahl Artikel mit ctaric: {count}")
            return True, f"Anzahl Artikel mit ctaric: {count}", count
        else:
            return False, message or "Keine Ergebnisse gefunden", None
    
    def get_products_with_taric_info(self) -> Tuple[bool, str, Optional[List[Dict]]]:
        """
        Holt alle Artikel mit Taric-Informationen für n8n-Übertragung.
        
        Returns:
            Tuple (success: bool, message: str, products: Optional[List[Dict]])
        """
        sql_query = """
            SELECT 
                cartnr as sku,
                cBarcode as ean, 
                cTaric as taric, 
                tArtikelBeschreibung.cname as name 
            FROM tartikel
            JOIN tArtikelBeschreibung ON tartikel.kArtikel = tArtikelBeschreibung.kArtikel
                AND kPlattform = 1 AND kSprache = 1 
            WHERE cTaric != ''
        """
        
        try:
            connection_string = self._build_connection_string()
            
            logger.debug("Lade Produkte mit TARIC-Informationen...")
            connection = pyodbc.connect(connection_string, timeout=10)
            cursor = connection.cursor()
            
            # SQL-Abfrage ausführen
            cursor.execute(sql_query)
            
            # Spaltennamen holen
            columns = [column[0] for column in cursor.description]
            
            # Ergebnisse in Dictionary-Format konvertieren
            results = []
            for row in cursor.fetchall():
                result_dict = {}
                for i, value in enumerate(row):
                    # Konvertiere None zu leerem String für JSON-Kompatibilität
                    result_dict[columns[i]] = value if value is not None else ''
                results.append(result_dict)
            
            cursor.close()
            connection.close()
            
            logger.info(f"{len(results)} Artikel mit TARIC-Informationen gefunden")
            return True, f"Artikel gefunden: {len(results)}", results
            
        except pyodbc.OperationalError as e:
            error = handle_error(
                e,
                error_code=ErrorCode.DB_CONNECTION_FAILED,
                context={'operation': 'get_products_with_taric_info'},
                log_level="error"
            )
            logger.error(f"SQL Server-Verbindungsfehler: {error.message}")
            return False, error.message, None
        except pyodbc.Error as e:
            error = handle_error(
                e,
                error_code=ErrorCode.DB_CONNECTION_FAILED,
                context={'operation': 'get_products_with_taric_info'},
                log_level="error"
            )
            logger.error(f"SQL Server-Fehler: {error.message}")
            return False, error.message, None
        except Exception as e:
            error = handle_error(
                e,
                error_code=ErrorCode.GEN_UNEXPECTED_ERROR,
                context={'operation': 'get_products_with_taric_info'},
                log_level="error"
            )
            logger.error(f"Verbindungsfehler: {error.message}", exc_info=True)
            return False, error.message, None
    
    def has_saved_credentials(self) -> bool:
        """
        Prüft ob gespeicherte Anmeldedaten vorhanden sind.
        
        Returns:
            True wenn Credentials vorhanden, sonst False
        """
        has_config = self.config_file.exists()
        has_password = self.get_password() is not None
        
        return has_config and has_password
    
    def clear_credentials(self) -> bool:
        """
        Löscht alle gespeicherten Anmeldedaten.
        
        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        try:
            # Lösche Passwort aus Keyring
            username_key = f"{self.config['server']}:{self.config['username']}"
            try:
                keyring.delete_password(self.service_name, username_key)
                logger.info("Passwort aus Keyring gelöscht")
            except keyring.errors.PasswordDeleteError:
                logger.warning("Passwort war nicht im Keyring")
            
            # Lösche Konfigurationsdatei
            if self.config_file.exists():
                self.config_file.unlink()
                logger.info("Konfigurationsdatei gelöscht")
            
            # Setze Konfiguration zurück
            self.config = self._get_default_config()
            
            logger.info("Alle Credentials erfolgreich gelöscht")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Löschen der Anmeldedaten: {e}")
            return False

