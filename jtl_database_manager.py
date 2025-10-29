import json
import os
import keyring
import pyodbc
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class JTLDatabaseManager:
    """Manager für JTL-Datenbankverbindung mit sicherer Passwort-Speicherung"""
    
    def __init__(self):
        self.config_file = 'jtl_config.json'
        self.service_name = 'OSS_goEcommerce_JTL'
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Lädt Verbindungseinstellungen aus JSON-Datei"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Fehler beim Laden der Konfiguration: {e}")
                return self._get_default_config()
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Gibt Standard-Konfiguration zurück"""
        return {
            'server': '.\\JTLWAWI',
            'database': 'eazybusiness',
            'username': 'sa',
            'driver': 'ODBC Driver 17 for SQL Server',
            'last_tested': None
        }
    
    def save_config(self, server: str, username: str, database: str, driver: str = 'ODBC Driver 17 for SQL Server') -> bool:
        """Speichert Verbindungseinstellungen in JSON-Datei"""
        try:
            self.config = {
                'server': server,
                'username': username,
                'database': database,
                'driver': driver,
                'last_tested': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Fehler beim Speichern der Konfiguration: {e}")
            return False
    
    def save_password(self, password: str) -> bool:
        """Speichert Passwort sicher im Keyring"""
        try:
            username_key = f"{self.config['server']}:{self.config['username']}"
            keyring.set_password(self.service_name, username_key, password)
            return True
        except Exception as e:
            print(f"Fehler beim Speichern des Passworts: {e}")
            return False
    
    def get_password(self) -> Optional[str]:
        """Holt Passwort aus dem Keyring"""
        try:
            username_key = f"{self.config['server']}:{self.config['username']}"
            password = keyring.get_password(self.service_name, username_key)
            return password
        except Exception as e:
            print(f"Fehler beim Abrufen des Passworts: {e}")
            return None
    
    def test_connection(self, server: str = None, username: str = None, password: str = None, 
                       database: str = None, driver: str = None) -> Tuple[bool, str]:
        """Testet SQL Server-Verbindung"""
        try:
            # Verwende übergebene Parameter oder gespeicherte Konfiguration
            test_server = server or self.config['server']
            test_username = username or self.config['username']
            test_password = password or self.get_password()
            test_database = database or self.config['database']
            test_driver = driver or self.config['driver']
            
            if not test_password:
                return False, "Kein Passwort im Keyring gefunden"
            
            # SQL Server Verbindungsstring erstellen
            connection_string = (
                f"DRIVER={{{test_driver}}};"
                f"SERVER={test_server};"
                f"DATABASE={test_database};"
                f"UID={test_username};"
                f"PWD={test_password};"
                f"Trusted_Connection=no;"
            )
            
            # Verbindung testen
            connection = pyodbc.connect(connection_string, timeout=10)
            
            # Einfache Abfrage zum Testen
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            
            return True, "Verbindung erfolgreich"
            
        except pyodbc.Error as e:
            return False, f"SQL Server-Fehler: {str(e)}"
        except Exception as e:
            return False, f"Verbindungsfehler: {str(e)}"
    
    def get_available_databases(self, server: str = None, username: str = None, 
                               password: str = None, driver: str = None) -> List[str]:
        """Holt alle verfügbaren Datenbanken (außer System-Datenbanken)"""
        try:
            test_server = server or self.config['server']
            test_username = username or self.config['username']
            test_password = password or self.get_password()
            test_driver = driver or self.config['driver']
            
            if not test_password:
                return []
            
            # SQL Server Verbindungsstring erstellen (ohne spezifische Datenbank)
            connection_string = (
                f"DRIVER={{{test_driver}}};"
                f"SERVER={test_server};"
                f"UID={test_username};"
                f"PWD={test_password};"
                f"Trusted_Connection=no;"
            )
            
            connection = pyodbc.connect(connection_string, timeout=10)
            cursor = connection.cursor()
            
            # SQL Server spezifische Abfrage für Datenbanken
            cursor.execute("SELECT name FROM sys.databases WHERE database_id > 4")
            databases = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            connection.close()
            
            return databases
            
        except pyodbc.Error as e:
            print(f"Fehler beim Abrufen der Datenbanken: {e}")
            return []
        except Exception as e:
            print(f"Verbindungsfehler: {e}")
            return []
    
    def execute_jtl_query(self, sql_query: str) -> Tuple[bool, str, Optional[List]]:
        """Führt eine SQL-Abfrage auf der JTL-Datenbank aus"""
        try:
            # Verbindungsstring erstellen
            connection_string = (
                f"DRIVER={{{self.config['driver']}}};"
                f"SERVER={self.config['server']};"
                f"DATABASE={self.config['database']};"
                f"UID={self.config['username']};"
                f"PWD={self.get_password()};"
                f"Trusted_Connection=no;"
            )
            
            # Verbindung herstellen
            connection = pyodbc.connect(connection_string, timeout=10)
            cursor = connection.cursor()
            
            # SQL-Abfrage ausführen
            cursor.execute(sql_query)
            results = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            return True, "Abfrage erfolgreich", results
            
        except pyodbc.Error as e:
            return False, f"SQL Server-Fehler: {str(e)}", None
        except Exception as e:
            return False, f"Verbindungsfehler: {str(e)}", None
    
    def get_article_count_with_ctaric(self) -> Tuple[bool, str, Optional[int]]:
        """Spezifische JTL-Abfrage: Anzahl Artikel mit ctaric"""
        sql_query = "SELECT DISTINCT COUNT(ctaric) FROM tartikel WHERE ctaric != ''"
        success, message, results = self.execute_jtl_query(sql_query)
        
        if success and results and len(results) > 0:
            count = results[0][0]
            return True, f"Anzahl Artikel mit ctaric: {count}", count
        else:
            return False, message or "Keine Ergebnisse gefunden", None
    
    def get_products_with_taric_info(self) -> Tuple[bool, str, Optional[List[Dict]]]:
        """Holt alle Artikel mit Taric-Informationen für n8n-Übertragung"""
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
            # Verbindungsstring erstellen
            connection_string = (
                f"DRIVER={{{self.config['driver']}}};"
                f"SERVER={self.config['server']};"
                f"DATABASE={self.config['database']};"
                f"UID={self.config['username']};"
                f"PWD={self.get_password()};"
                f"Trusted_Connection=no;"
            )
            
            # Verbindung herstellen
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
            
            return True, f"Artikel gefunden: {len(results)}", results
            
        except pyodbc.Error as e:
            return False, f"SQL Server-Fehler: {str(e)}", None
        except Exception as e:
            return False, f"Verbindungsfehler: {str(e)}", None
    
    def has_saved_credentials(self) -> bool:
        """Prüft ob gespeicherte Anmeldedaten vorhanden sind"""
        return (
            os.path.exists(self.config_file) and 
            self.get_password() is not None
        )
    
    def clear_credentials(self) -> bool:
        """Löscht alle gespeicherten Anmeldedaten"""
        try:
            # Lösche Passwort aus Keyring
            username_key = f"{self.config['server']}:{self.config['username']}"
            keyring.delete_password(self.service_name, username_key)
            
            # Lösche Konfigurationsdatei
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            
            # Setze Konfiguration zurück
            self.config = self._get_default_config()
            
            return True
        except Exception as e:
            print(f"Fehler beim Löschen der Anmeldedaten: {e}")
            return False
