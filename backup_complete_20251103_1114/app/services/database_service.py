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
            except Exception as e:
                logger.error(f"Fehler beim Laden der Konfiguration: {e}")
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
            'driver': 'ODBC Driver 17 for SQL Server',
            'last_tested': None
        }
    
    def save_config(
        self,
        server: str,
        username: str,
        database: str,
        driver: str = 'ODBC Driver 17 for SQL Server'
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
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Konfiguration: {e}")
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
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Passworts: {e}")
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
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Passworts: {e}")
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
        
        connection_string = (
            f"DRIVER={{{test_driver}}};"
            f"SERVER={test_server};"
            f"DATABASE={test_database};" if test_database else ""
            f"UID={test_username};"
            f"PWD={test_password};"
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
            
        except pyodbc.Error as e:
            logger.error(f"SQL Server-Fehler: {e}")
            return False, f"SQL Server-Fehler: {str(e)}"
        except Exception as e:
            logger.error(f"Verbindungsfehler: {e}")
            return False, f"Verbindungsfehler: {str(e)}"
    
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
            
        except pyodbc.Error as e:
            logger.error(f"Fehler beim Abrufen der Datenbanken: {e}")
            return []
        except Exception as e:
            logger.error(f"Verbindungsfehler: {e}")
            return []
    
    def execute_query(self, sql_query: str) -> Tuple[bool, str, Optional[List]]:
        """
        Führt eine SQL-Abfrage auf der JTL-Datenbank aus.
        
        Args:
            sql_query: SQL-Abfrage als String
            
        Returns:
            Tuple (success: bool, message: str, results: Optional[List])
        """
        try:
            connection_string = self._build_connection_string()
            
            logger.debug(f"Führe SQL-Abfrage aus: {sql_query[:100]}...")
            connection = pyodbc.connect(connection_string, timeout=10)
            cursor = connection.cursor()
            
            # SQL-Abfrage ausführen
            cursor.execute(sql_query)
            
            # Versuche Ergebnisse abzurufen (funktioniert nur bei SELECT)
            try:
                results = cursor.fetchall()
            except pyodbc.ProgrammingError:
                # Bei INSERT/UPDATE/DELETE gibt es keine Ergebnisse
                # Hole stattdessen die Anzahl betroffener Zeilen
                rowcount = cursor.rowcount
                results = None
                connection.commit()  # Commit für INSERT/UPDATE/DELETE
                logger.info(f"Abfrage erfolgreich - {rowcount} Zeilen betroffen")
                return True, f"Abfrage erfolgreich - {rowcount} Zeilen betroffen", rowcount
            
            # Für SELECT-Abfragen
            connection.commit()  # Auch bei SELECT commit (sicherheitshalber)
            cursor.close()
            connection.close()
            
            logger.info(f"Abfrage erfolgreich - {len(results) if results else 0} Ergebnisse")
            return True, "Abfrage erfolgreich", results
            
        except pyodbc.Error as e:
            logger.error(f"SQL Server-Fehler: {e}")
            return False, f"SQL Server-Fehler: {str(e)}", None
        except Exception as e:
            logger.error(f"Verbindungsfehler: {e}")
            return False, f"Verbindungsfehler: {str(e)}", None
    
    def execute_jtl_query(self, sql_query: str) -> Tuple[bool, str, Optional[List]]:
        """Alias für execute_query - Backward Compatibility"""
        return self.execute_query(sql_query)
    
    def get_article_count_with_ctaric(self) -> Tuple[bool, str, Optional[int]]:
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
            
        except pyodbc.Error as e:
            logger.error(f"SQL Server-Fehler: {e}")
            return False, f"SQL Server-Fehler: {str(e)}", None
        except Exception as e:
            logger.error(f"Verbindungsfehler: {e}")
            return False, f"Verbindungsfehler: {str(e)}", None
    
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

