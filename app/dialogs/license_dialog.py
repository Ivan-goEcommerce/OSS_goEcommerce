"""
License Dialog für OSS goEcommerce
Dialog für Lizenz-Eingabe
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFormLayout, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.services.license_service import LicenseService


class LicenseDialog(QDialog):
    """Dialog für Lizenz-Eingabe"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 Lizenz eingeben")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        # License Service für Speicherung
        self.license_service = LicenseService()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Richtet die Benutzeroberfläche ein"""
        layout = QVBoxLayout(self)
        
        # Titel
        title_label = QLabel("Lizenz-Informationen eingeben")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # Formular
        form_layout = QFormLayout()
        
        # Lizenznummer
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("Lizenznummer eingeben...")
        form_layout.addRow("Lizenznummer:", self.license_input)
        
        # E-Mail
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-Mail eingeben...")
        form_layout.addRow("E-Mail:", self.email_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("💾 Speichern")
        save_button.clicked.connect(self.save_license)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("❌ Abbrechen")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def save_license(self):
        """Speichert die Lizenz im Keyring"""
        license_number = self.license_input.text().strip()
        email = self.email_input.text().strip()
        
        # Validierung
        if not license_number or not email:
            QMessageBox.warning(
                self, 
                "Fehler", 
                "Bitte geben Sie sowohl Lizenznummer als auch E-Mail ein!"
            )
            return
        
        # Speichere im Keyring über LicenseService
        success = self.license_service.save_license(license_number, email)
        
        if success:
            QMessageBox.information(
                self, 
                "Erfolg", 
                f"Lizenzdaten wurden erfolgreich gespeichert:\n\n"
                f"Lizenznummer: {license_number}\n"
                f"E-Mail: {email}"
            )
            self.accept()
        else:
            QMessageBox.critical(
                self, 
                "Fehler", 
                "Fehler beim Speichern der Lizenzdaten im Keyring.\n\n"
                "Bitte versuchen Sie es erneut oder kontaktieren Sie den Support."
            )
