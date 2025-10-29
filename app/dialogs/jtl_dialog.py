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
        
        # Passwort
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Passwort eingeben...")
        form_layout.addRow("Passwort:", self.password_input)
        
        # ODBC Driver
        self.driver_combo = QComboBox()
        self.driver_combo.addItems([
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 13 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server"
        ])
        self.driver_combo.setCurrentText("ODBC Driver 17 for SQL Server")
        form_layout.addRow("ODBC Driver:", self.driver_combo)
        
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
            driver = self.driver_combo.currentText()
            
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
                QMessageBox.critical(self, "Fehler", f"Verbindung fehlgeschlagen!\n\n{message}")
                
        except Exception as e:
            self.status_label.setText("Status: ❌ Fehler beim Testen")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Testen der Verbindung:\n\n{str(e)}")
    
    def accept(self):
        """Speichert die Konfiguration und schließt den Dialog"""
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
            driver = self.driver_combo.currentText()
            
            if not all([server, database, username, password]):
                QMessageBox.warning(self, "Fehler", "Bitte füllen Sie alle Felder aus!")
                return
            
            # Speichere Konfiguration
            db_manager = JTLDatabaseManager()
            
            # Speichere Konfiguration
            config_saved = db_manager.save_config(
                server=server,
                username=username,
                database=database,
                driver=driver
            )
            
            # Speichere Passwort
            password_saved = db_manager.save_password(password)
            
            if config_saved and password_saved:
                QMessageBox.information(self, "Erfolg", "Konfiguration erfolgreich gespeichert!")
                super().accept()
            else:
                QMessageBox.critical(self, "Fehler", "Fehler beim Speichern der Konfiguration!")
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern:\n\n{str(e)}")
