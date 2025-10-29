"""
WebHook Dialog für OSS goEcommerce
Dialog für WebHook-Einstellungen
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFormLayout, QComboBox, 
                               QMessageBox, QGroupBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class WebHookDialog(QDialog):
    """Dialog für WebHook-Einstellungen"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔗 WebHook einrichten")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Richtet die Benutzeroberfläche ein"""
        layout = QVBoxLayout(self)
        
        # WebHook-Auswahl
        webhook_group = QGroupBox("WebHook auswählen")
        webhook_layout = QVBoxLayout(webhook_group)
        
        # WebHook-Auswahlliste
        self.webhook_combo = QComboBox()
        self.webhook_combo.addItems([
            "n8n TARIC-Suche (Produktion)",
            "n8n TARIC-Suche (Test)", 
            "REST API Test",
            "Custom WebHook",
            "Test WebHook"
        ])
        self.webhook_combo.currentTextChanged.connect(self.on_webhook_selected)
        webhook_layout.addWidget(self.webhook_combo)
        
        layout.addWidget(webhook_group)
        
        # Formular
        form_layout = QFormLayout()
        
        # WebHook URL
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://agentic.go-ecommerce.de/webhook-test/v1/users/tarics")
        form_layout.addRow("WebHook URL:", self.url_input)
        
        # WebHook Typ
        self.type_combo = QComboBox()
        self.type_combo.addItems(["n8n Workflow", "REST API", "Custom WebHook", "Test WebHook"])
        self.type_combo.setCurrentText("n8n Workflow")
        form_layout.addRow("Typ:", self.type_combo)
        
        # Lizenznummer
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("123456")
        form_layout.addRow("Lizenznummer:", self.license_input)
        
        # E-Mail
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("ivan.levshyn@go-ecommerce.de")
        form_layout.addRow("E-Mail:", self.email_input)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Aktiv", "Inaktiv", "Test"])
        self.status_combo.setCurrentText("Aktiv")
        form_layout.addRow("Status:", self.status_combo)
        
        layout.addLayout(form_layout)
        
        # Status
        self.status_label = QLabel("Status: Nicht getestet")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.test_button = QPushButton("🧪 Testen")
        self.test_button.clicked.connect(self.test_webhook)
        button_layout.addWidget(self.test_button)
        
        save_button = QPushButton("💾 Speichern")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("❌ Abbrechen")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Initiale Auswahl setzen
        self.on_webhook_selected(self.webhook_combo.currentText())
    
    def on_webhook_selected(self, webhook_name):
        """Behandelt die WebHook-Auswahl"""
        webhook_configs = {
            "n8n TARIC-Suche (Produktion)": {
                "url": "https://agentic.go-ecommerce.de/webhook/v1/users/tarics",
                "type": "n8n Workflow",
                "license": "123456",
                "email": "ivan.levshyn@go-ecommerce.de",
                "status": "Aktiv"
            },
            "n8n TARIC-Suche (Test)": {
                "url": "https://agentic.go-ecommerce.de/webhook-test/v1/users/tarics",
                "type": "n8n Workflow", 
                "license": "123456",
                "email": "ivan.levshyn@go-ecommerce.de",
                "status": "Test"
            },
            "REST API Test": {
                "url": "https://api.example.com/webhook",
                "type": "REST API",
                "license": "abc123def456",
                "email": "test@example.com",
                "status": "Test"
            },
            "Custom WebHook": {
                "url": "https://custom.example.com/hook",
                "type": "Custom WebHook",
                "license": "xyz789uvw012",
                "email": "custom@example.com",
                "status": "Inaktiv"
            },
            "Test WebHook": {
                "url": "https://test.example.com/webhook",
                "type": "Test WebHook",
                "license": "test123",
                "email": "test@example.com",
                "status": "Test"
            }
        }
        
        config = webhook_configs.get(webhook_name, {})
        if config:
            self.url_input.setText(config.get("url", ""))
            self.type_combo.setCurrentText(config.get("type", "n8n Workflow"))
            self.license_input.setText(config.get("license", ""))
            self.email_input.setText(config.get("email", ""))
            self.status_combo.setCurrentText(config.get("status", "Aktiv"))
    
    def test_webhook(self):
        """Testet den WebHook"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie eine WebHook URL ein!")
            return
        
        QMessageBox.information(self, "WebHook Test", f"WebHook Test würde für URL durchgeführt werden:\n{url}")
