"""
OSS Database Schema Manager
Verwaltet die OSS-Datenbankschema und Tabellen
"""

import pyodbc
import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.core.debug_manager import debug_print


class OSSSchemaManager:
    """Manager für OSS-Datenbankschema und Tabellen"""
    
    def __init__(self, db_manager=None):
        """
        Initialisiert den Schema Manager
        
        Args:
            db_manager: JTLDatabaseManager Instanz für Datenbankverbindung
        """
        self.db_manager = db_manager
        self.schema_name = "oss"
        self.schema_created = False
        
        # Schema-Definitionen
        self.schema_definitions = {
            "oss": {
                "description": "OSS goEcommerce Schema",
                "tables": {
                    "options": {
                        "description": "Konfigurationsoptionen für OSS",
                        "columns": {
                            "id": "INT AUTO_INCREMENT PRIMARY KEY",
                            "name": "VARCHAR(255) NOT NULL UNIQUE",
                            "value": "TEXT",
                            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
                        },
                        "indexes": [
                            "INDEX idx_name (name)",
                            "INDEX idx_created_at (created_at)"
                        ]
                    }
                }
            }
        }
    
    def initialize_schema(self) -> Tuple[bool, str]:
        """
        Initialisiert das OSS-Schema bei der ersten App-Ausführung
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not self.db_manager:
                return False, "Kein Datenbankmanager verfügbar"
            
            if not self.db_manager.has_saved_credentials():
                return False, "Keine Datenbankverbindung konfiguriert"
            
            # Teste Verbindung
            success, message = self.db_manager.test_connection()
            if not success:
                return False, f"Verbindungstest fehlgeschlagen: {message}"
            
            # Erstelle Schema
            schema_created, schema_message = self.create_schema()
            if not schema_created:
                return False, f"Schema-Erstellung fehlgeschlagen: {schema_message}"
            
            # Erstelle Tabellen
            tables_created, tables_message = self.create_tables()
            if not tables_created:
                return False, f"Tabellen-Erstellung fehlgeschlagen: {tables_message}"
            
            # Initialisiere Standarddaten
            data_initialized, data_message = self.initialize_default_data()
            if not data_initialized:
                return False, f"Standarddaten-Initialisierung fehlgeschlagen: {data_message}"
            
            self.schema_created = True
            return True, "OSS-Schema erfolgreich initialisiert"
            
        except Exception as e:
            return False, f"Fehler bei Schema-Initialisierung: {str(e)}"
    
    def create_schema(self) -> Tuple[bool, str]:
        """
        Erstellt das OSS-Schema falls es nicht existiert
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            password = self.db_manager.get_password()
            if not password:
                return False, "Kein Datenbankpasswort verfügbar"
            
            connection = pymysql.connect(
                host=self.db_manager.config['host'],
                port=self.db_manager.config['port'],
                user=self.db_manager.config['username'],
                password=password,
                charset='utf8mb4',
                connect_timeout=10
            )
            
            with connection.cursor() as cursor:
                # Prüfe ob Schema bereits existiert
                cursor.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s", (self.schema_name,))
                schema_exists = cursor.fetchone() is not None
                
                if not schema_exists:
                    # Erstelle Schema
                    create_schema_sql = f"CREATE SCHEMA `{self.schema_name}` AUTHORIZATION `{self.db_manager.config['username']}`"
                    cursor.execute(create_schema_sql)
                    connection.commit()
                    
                    debug_print(f"✅ OSS-Schema '{self.schema_name}' erstellt")
                    return True, f"Schema '{self.schema_name}' erfolgreich erstellt"
                else:
                    debug_print(f"ℹ️ OSS-Schema '{self.schema_name}' existiert bereits")
                    return True, f"Schema '{self.schema_name}' existiert bereits"
            
            connection.close()
            
        except Exception as e:
            return False, f"Fehler beim Erstellen des Schemas: {str(e)}"
    
    def create_tables(self) -> Tuple[bool, str]:
        """
        Erstellt alle Tabellen im OSS-Schema
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            password = self.db_manager.get_password()
            if not password:
                return False, "Kein Datenbankpasswort verfügbar"
            
            connection = pymysql.connect(
                host=self.db_manager.config['host'],
                port=self.db_manager.config['port'],
                user=self.db_manager.config['username'],
                password=password,
                database=self.schema_name,
                charset='utf8mb4',
                connect_timeout=10
            )
            
            with connection.cursor() as cursor:
                schema_def = self.schema_definitions[self.schema_name]
                
                for table_name, table_def in schema_def["tables"].items():
                    # Prüfe ob Tabelle bereits existiert
                    cursor.execute("""
                        SELECT TABLE_NAME 
                        FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    """, (self.schema_name, table_name))
                    
                    table_exists = cursor.fetchone() is not None
                    
                    if not table_exists:
                        # Erstelle Tabelle
                        create_table_sql = self._build_create_table_sql(table_name, table_def)
                        cursor.execute(create_table_sql)
                        
                        # Erstelle Indizes
                        for index_def in table_def.get("indexes", []):
                            try:
                                cursor.execute(index_def)
                            except Exception as e:
                                debug_print(f"⚠️ Warnung: Index konnte nicht erstellt werden: {e}")
                        
                        connection.commit()
                        debug_print(f"✅ Tabelle '{table_name}' im Schema '{self.schema_name}' erstellt")
                    else:
                        debug_print(f"ℹ️ Tabelle '{table_name}' im Schema '{self.schema_name}' existiert bereits")
            
            connection.close()
            return True, "Alle Tabellen erfolgreich erstellt/überprüft"
            
        except Exception as e:
            return False, f"Fehler beim Erstellen der Tabellen: {str(e)}"
    
    def _build_create_table_sql(self, table_name: str, table_def: Dict) -> str:
        """
        Baut den CREATE TABLE SQL-Befehl
        
        Args:
            table_name: Name der Tabelle
            table_def: Tabellendefinition
            
        Returns:
            str: SQL-Befehl zum Erstellen der Tabelle
        """
        columns = []
        for col_name, col_def in table_def["columns"].items():
            columns.append(f"`{col_name}` {col_def}")
        
        sql = f"CREATE TABLE `{table_name}` (\n  " + ",\n  ".join(columns) + "\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
        
        return sql
    
    def initialize_default_data(self) -> Tuple[bool, str]:
        """
        Initialisiert Standarddaten in den Tabellen
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            password = self.db_manager.get_password()
            if not password:
                return False, "Kein Datenbankpasswort verfügbar"
            
            connection = pymysql.connect(
                host=self.db_manager.config['host'],
                port=self.db_manager.config['port'],
                user=self.db_manager.config['username'],
                password=password,
                database=self.schema_name,
                charset='utf8mb4',
                connect_timeout=10
            )
            
            with connection.cursor() as cursor:
                # Standard-Optionen für OSS
                default_options = [
                    ("app_version", "1.0.0", "Aktuelle App-Version"),
                    ("last_execution", datetime.now().isoformat(), "Letzte App-Ausführung"),
                    ("taric_count", "0", "Anzahl TARIC-Nummern in der Datenbank"),
                    ("license_status", "active", "Lizenzstatus"),
                    ("n8n_workflow_url", "https://agentic.go-ecommerce.de/webhook-test/v1/users/tarics", "n8n Workflow URL"),
                    ("auto_refresh_interval", "30", "Auto-Refresh Intervall in Sekunden"),
                    ("database_last_update", datetime.now().isoformat(), "Letzte Datenbankaktualisierung"),
                    ("searches_today", "0", "Anzahl Suchen heute"),
                    ("total_searches", "0", "Gesamtanzahl Suchen")
                ]
                
                for name, value, description in default_options:
                    # Prüfe ob Option bereits existiert
                    cursor.execute("SELECT id FROM options WHERE name = %s", (name,))
                    if cursor.fetchone() is None:
                        # Füge Option hinzu
                        cursor.execute("""
                            INSERT INTO options (name, value) 
                            VALUES (%s, %s)
                        """, (name, value))
                        debug_print(f"✅ Standard-Option '{name}' hinzugefügt")
                    else:
                        debug_print(f"ℹ️ Option '{name}' existiert bereits")
                
                connection.commit()
            
            connection.close()
            return True, "Standarddaten erfolgreich initialisiert"
            
        except Exception as e:
            return False, f"Fehler beim Initialisieren der Standarddaten: {str(e)}"
    
    def get_option(self, name: str) -> Optional[str]:
        """
        Holt eine Option aus der Datenbank
        
        Args:
            name: Name der Option
            
        Returns:
            Optional[str]: Wert der Option oder None
        """
        try:
            password = self.db_manager.get_password()
            if not password:
                return None
            
            connection = pymysql.connect(
                host=self.db_manager.config['host'],
                port=self.db_manager.config['port'],
                user=self.db_manager.config['username'],
                password=password,
                database=self.schema_name,
                charset='utf8mb4',
                connect_timeout=10
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT value FROM options WHERE name = %s", (name,))
                result = cursor.fetchone()
                
                if result:
                    return result[0]
                else:
                    return None
            
            connection.close()
            
        except Exception as e:
            debug_print(f"Fehler beim Abrufen der Option '{name}': {e}")
            return None
    
    def set_option(self, name: str, value: str) -> bool:
        """
        Setzt eine Option in der Datenbank
        
        Args:
            name: Name der Option
            value: Wert der Option
            
        Returns:
            bool: True wenn erfolgreich
        """
        try:
            password = self.db_manager.get_password()
            if not password:
                return False
            
            connection = pymysql.connect(
                host=self.db_manager.config['host'],
                port=self.db_manager.config['port'],
                user=self.db_manager.config['username'],
                password=password,
                database=self.schema_name,
                charset='utf8mb4',
                connect_timeout=10
            )
            
            with connection.cursor() as cursor:
                # Prüfe ob Option existiert
                cursor.execute("SELECT id FROM options WHERE name = %s", (name,))
                if cursor.fetchone():
                    # Update bestehende Option
                    cursor.execute("UPDATE options SET value = %s WHERE name = %s", (value, name))
                else:
                    # Erstelle neue Option
                    cursor.execute("INSERT INTO options (name, value) VALUES (%s, %s)", (name, value))
                
                connection.commit()
            
            connection.close()
            return True
            
        except Exception as e:
            debug_print(f"Fehler beim Setzen der Option '{name}': {e}")
            return False
    
    def get_all_options(self) -> Dict[str, str]:
        """
        Holt alle Optionen aus der Datenbank
        
        Returns:
            Dict[str, str]: Dictionary mit allen Optionen
        """
        try:
            password = self.db_manager.get_password()
            if not password:
                return {}
            
            connection = pymysql.connect(
                host=self.db_manager.config['host'],
                port=self.db_manager.config['port'],
                user=self.db_manager.config['username'],
                password=password,
                database=self.schema_name,
                charset='utf8mb4',
                connect_timeout=10
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT name, value FROM options")
                results = cursor.fetchall()
                
                options = {}
                for name, value in results:
                    options[name] = value
                
                return options
            
            connection.close()
            
        except Exception as e:
            debug_print(f"Fehler beim Abrufen aller Optionen: {e}")
            return {}
    
    def update_execution_stats(self, search_term: str = None) -> bool:
        """
        Aktualisiert die Ausführungsstatistiken
        
        Args:
            search_term: Suchbegriff (optional)
            
        Returns:
            bool: True wenn erfolgreich
        """
        try:
            # Aktualisiere letzte Ausführung
            self.set_option("last_execution", datetime.now().isoformat())
            
            if search_term:
                self.set_option("last_search", search_term)
            
            # Zähle Suchen heute
            today = datetime.now().strftime('%Y-%m-%d')
            last_search_date = self.get_option("last_search_date")
            
            if last_search_date != today:
                self.set_option("searches_today", "1")
                self.set_option("last_search_date", today)
            else:
                searches_today = int(self.get_option("searches_today") or "0") + 1
                self.set_option("searches_today", str(searches_today))
            
            # Gesamtanzahl Suchen
            total_searches = int(self.get_option("total_searches") or "0") + 1
            self.set_option("total_searches", str(total_searches))
            
            return True
            
        except Exception as e:
            debug_print(f"Fehler beim Aktualisieren der Ausführungsstatistiken: {e}")
            return False
    
    def get_taric_count_from_database(self) -> int:
        """
        Ermittelt die Anzahl der TARIC-Nummern aus der Hauptdatenbank
        
        Returns:
            int: Anzahl der TARIC-Nummern
        """
        try:
            password = self.db_manager.get_password()
            if not password:
                return 0
            
            connection = pymysql.connect(
                host=self.db_manager.config['host'],
                port=self.db_manager.config['port'],
                user=self.db_manager.config['username'],
                password=password,
                database=self.db_manager.config['database'],
                charset='utf8mb4',
                connect_timeout=10
            )
            
            with connection.cursor() as cursor:
                # Suche nach TARIC-Feldern in verschiedenen Tabellen
                taric_count = 0
                
                # Versuche verschiedene mögliche Tabellennamen und Feldnamen
                possible_queries = [
                    "SELECT COUNT(DISTINCT taric_code) FROM products WHERE taric_code IS NOT NULL AND taric_code != ''",
                    "SELECT COUNT(DISTINCT taric) FROM products WHERE taric IS NOT NULL AND taric != ''",
                    "SELECT COUNT(DISTINCT taric_number) FROM products WHERE taric_number IS NOT NULL AND taric_number != ''",
                    "SELECT COUNT(DISTINCT customs_code) FROM products WHERE customs_code IS NOT NULL AND customs_code != ''",
                    "SELECT COUNT(DISTINCT hs_code) FROM products WHERE hs_code IS NOT NULL AND hs_code != ''"
                ]
                
                for query in possible_queries:
                    try:
                        cursor.execute(query)
                        result = cursor.fetchone()
                        if result and result[0] > 0:
                            taric_count = result[0]
                            break
                    except:
                        continue
                
                # Aktualisiere TARIC-Anzahl in OSS-Optionen
                self.set_option("taric_count", str(taric_count))
                self.set_option("database_last_update", datetime.now().isoformat())
                
                return taric_count
            
            connection.close()
            
        except Exception as e:
            debug_print(f"Fehler beim Ermitteln der TARIC-Anzahl: {e}")
            return 0
