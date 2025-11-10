"""
JTL Connection Dialog für OSS goEcommerce
Dialog für JTL-Verbindungseinstellungen
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFormLayout, QComboBox, 
                               QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class JTLConnectionDialog(QDialog):
    """Dialog für JTL-Verbindungseinstellungen"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔗 JTL-Verbindung einrichten")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        self.setup_ui()
        self.load_saved_config()  # Lade gespeicherte Konfiguration beim Öffnen
    
    def setup_ui(self):
        """Richtet die Benutzeroberfläche ein"""
        layout = QVBoxLayout(self)
        
        # Formular
        form_layout = QFormLayout()
        
        # Server
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText(".\\JTLWAWI")
        self.server_input.setText(".\\JTLWAWI")
        form_layout.addRow("Server:", self.server_input)
        
        # Datenbank
        self.database_input = QLineEdit()
        self.database_input.setPlaceholderText("eazybusiness")
        self.database_input.setText("eazybusiness")
        form_layout.addRow("Datenbank:", self.database_input)
        
        # Benutzername
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("sa")
        self.username_input.setText("sa")
        form_layout.addRow("Benutzername:", self.username_input)
        
        # Passwort mit Anzeige-Button
        password_layout = QHBoxLayout()
        password_layout.setSpacing(5)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Passwort eingeben...")
        password_layout.addWidget(self.password_input)
        
        # Button zum Anzeigen/Verstecken des Passworts
        self.password_toggle_button = QPushButton("👁️")
        self.password_toggle_button.setFixedWidth(45)
        self.password_toggle_button.setFixedHeight(30)
        self.password_toggle_button.setToolTip("Passwort anzeigen/verstecken")
        self.password_toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                color: #ffffff;
                border: 1px solid #666666;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #555555;
                border: 1px solid #777777;
            }
            QPushButton:pressed {
                background-color: #333333;
            }
        """)
        self.password_toggle_button.clicked.connect(self.toggle_password_visibility)
        password_layout.addWidget(self.password_toggle_button)
        
        form_layout.addRow("Passwort:", password_layout)
        
        # Driver ist fest auf py-mssql gesetzt (keine Auswahl möglich)
        # Kein UI-Element nötig, da immer py-mssql verwendet wird
        
        layout.addLayout(form_layout)
        
        # Status
        self.status_label = QLabel("Status: Nicht verbunden")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.test_button = QPushButton("🧪 Testen")
        self.test_button.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_button)
        
        save_button = QPushButton("💾 Speichern")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("❌ Abbrechen")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def toggle_password_visibility(self):
        """Wechselt zwischen Passwort-Modus und Klartext-Modus"""
        if self.password_input.echoMode() == QLineEdit.Password:
            # Zeige Passwort in Klartext
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.password_toggle_button.setText("🙈")
            self.password_toggle_button.setToolTip("Passwort verstecken")
        else:
            # Verstecke Passwort
            self.password_input.setEchoMode(QLineEdit.Password)
            self.password_toggle_button.setText("👁️")
            self.password_toggle_button.setToolTip("Passwort anzeigen")
    
    def load_saved_config(self):
        """Lädt die gespeicherte Konfiguration und füllt die Felder"""
        try:
            # Importiere JTL Database Manager
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from jtl_database_manager import JTLDatabaseManager
            
            db_manager = JTLDatabaseManager()
            config = db_manager.config
            
            # Fülle Felder mit gespeicherten Werten
            if config.get('server'):
                self.server_input.setText(config['server'])
            if config.get('database'):
                self.database_input.setText(config['database'])
            if config.get('username'):
                self.username_input.setText(config['username'])
            # Driver ist immer py-mssql (keine Auswahl nötig)
            
            # Lade Passwort aus Keyring
            try:
                saved_password = db_manager.get_password()
                if saved_password:
                    self.password_input.setText(saved_password)
            except Exception as e:
                # Passwort konnte nicht geladen werden (z.B. Keyring nicht verfügbar)
                # Das Passwort-Feld bleibt leer
                pass
            
            # Aktualisiere Status
            if db_manager.has_saved_credentials():
                self.status_label.setText("Status: Gespeicherte Konfiguration geladen")
            else:
                self.status_label.setText("Status: Keine gespeicherte Konfiguration")
                
        except Exception as e:
            # Bei Fehler: Standardwerte beibehalten
            self.status_label.setText(f"Status: Fehler beim Laden der Konfiguration: {str(e)}")
    
    def test_connection(self):
        """Testet die JTL-Verbindung"""
        try:
            # Importiere JTL Database Manager
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from jtl_database_manager import JTLDatabaseManager
            
            # Hole Eingabewerte
            server = self.server_input.text().strip()
            database = self.database_input.text().strip()
            username = self.username_input.text().strip()
            password = self.password_input.text().strip()
            driver = "py-mssql"  # Immer py-mssql Driver verwenden
            
            if not all([server, database, username, password]):
                QMessageBox.warning(self, "Fehler", "Bitte füllen Sie alle Felder aus!")
                return
            
            # Teste Verbindung
            db_manager = JTLDatabaseManager()
            success, message = db_manager.test_connection(
                server=server,
                username=username,
                password=password,
                database=database,
                driver=driver
            )
            
            if success:
                self.status_label.setText("Status: ✅ Verbindung erfolgreich")
                QMessageBox.information(self, "Erfolg", f"Verbindung erfolgreich!\n\n{message}")
            else:
                self.status_label.setText("Status: ❌ Verbindung fehlgeschlagen")
                # Zeige Fehlermeldung mit aktueller Konfiguration
                config_info = f"\n\nAktuelle Konfiguration:\n"
                config_info += f"Server: {server}\n"
                config_info += f"Datenbank: {database}\n"
                config_info += f"Benutzername: {username}\n"
                config_info += f"Driver: {driver}"
                QMessageBox.critical(
                    self, 
                    "Fehler", 
                    f"Verbindung fehlgeschlagen!\n\n{message}{config_info}"
                )
                
        except Exception as e:
            self.status_label.setText("Status: ❌ Fehler beim Testen")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Testen der Verbindung:\n\n{str(e)}")
    
    def accept(self):
        """Speichert die Konfiguration und schließt den Dialog - PRÜFT VORHER VERBINDUNG"""
        try:
            # Importiere JTL Database Manager
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from jtl_database_manager import JTLDatabaseManager
            
            # Hole Eingabewerte
            server = self.server_input.text().strip()
            database = self.database_input.text().strip()
            username = self.username_input.text().strip()
            password = self.password_input.text().strip()
            driver = "py-mssql"  # Immer py-mssql Driver verwenden
            
            if not all([server, database, username, password]):
                QMessageBox.warning(self, "Fehler", "Bitte füllen Sie alle Felder aus!")
                return
            
            # WICHTIG: Prüfe Verbindung VOR dem Speichern
            db_manager = JTLDatabaseManager()
            success, message = db_manager.test_connection(
                server=server,
                username=username,
                password=password,
                database=database,
                driver=driver
            )
            
            if not success:
                # Verbindung fehlgeschlagen - zeige Fehler mit aktueller Konfiguration und speichere NICHT
                self.status_label.setText("Status: ❌ Verbindung fehlgeschlagen")
                config_info = f"\n\nAktuelle Konfiguration:\n"
                config_info += f"Server: {server}\n"
                config_info += f"Datenbank: {database}\n"
                config_info += f"Benutzername: {username}\n"
                config_info += f"Driver: py-mssql"
                QMessageBox.critical(
                    self, 
                    "Verbindung fehlgeschlagen", 
                    f"Die Verbindung konnte nicht hergestellt werden:\n\n{message}\n\n"
                    f"{config_info}\n\n"
                    "Bitte überprüfen Sie Ihre Eingaben und versuchen Sie es erneut.\n\n"
                    "Die Daten wurden NICHT gespeichert."
                )
                return
            
            # Verbindung erfolgreich - jetzt speichern
            # Speichere Konfiguration (immer mit py-mssql Driver)
            config_saved = db_manager.save_config(
                server=server,
                username=username,
                database=database,
                driver="py-mssql"
            )
            
            # Speichere Passwort
            password_saved = db_manager.save_password(password)
            
            if config_saved and password_saved:
                self.status_label.setText("Status: ✅ Verbindung erfolgreich und gespeichert")
                QMessageBox.information(
                    self, 
                    "Erfolg", 
                    f"Verbindung erfolgreich getestet und Konfiguration gespeichert!\n\n{message}"
                )
                super().accept()
            else:
                QMessageBox.critical(self, "Fehler", "Fehler beim Speichern der Konfiguration!")
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern:\n\n{str(e)}")
