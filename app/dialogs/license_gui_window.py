"""
License GUI Window für OSS goEcommerce
Zeigt Lizenzstatus und ermöglicht Lizenz-Eingabe
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFormLayout, QMessageBox,
                               QProgressBar, QFrame)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont


class LicenseGUIWindow(QDialog):
    """GUI-Fenster für Lizenz-Management"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 OSS goEcommerce - Lizenzprüfung")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        self.license_valid = False
        self.setup_ui()
    
    def setup_ui(self):
        """Richtet die Benutzeroberfläche ein"""
        layout = QVBoxLayout(self)
        
        # Titel
        title_label = QLabel("OSS goEcommerce")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #ff8c00; text-align: center; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Lizenzprüfung")
        subtitle_label.setFont(QFont("Arial", 14))
        subtitle_label.setStyleSheet("color: #ff8c00; text-align: center; margin-bottom: 30px;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Status-Frame
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 2px solid #ff8c00;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)
        
        # Status-Label
        self.status_label = QLabel("🔄 Prüfe Lizenz...")
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setStyleSheet("color: #ff8c00; text-align: center;")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Unbestimmter Fortschritt
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ff8c00;
                border-radius: 8px;
                text-align: center;
                background-color: #1a1a1a;
                color: #ff8c00;
            }
            QProgressBar::chunk {
                background-color: #ff8c00;
                border-radius: 6px;
            }
        """)
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(status_frame)
        
        # Lizenz-Formular (versteckt bis benötigt)
        self.license_form = QFrame()
        self.license_form.setVisible(False)
        form_layout = QVBoxLayout(self.license_form)
        
        form_title = QLabel("Lizenz eingeben:")
        form_title.setFont(QFont("Arial", 12, QFont.Bold))
        form_title.setStyleSheet("color: #ff8c00; margin-bottom: 10px;")
        form_layout.addWidget(form_title)
        
        # Formular
        input_layout = QFormLayout()
        
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("Lizenznummer eingeben...")
        self.license_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                border: 2px solid #ff8c00;
                border-radius: 8px;
                padding: 8px;
                color: #ff8c00;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #ffaa00;
            }
        """)
        input_layout.addRow("Lizenznummer:", self.license_input)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-Mail eingeben...")
        self.email_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                border: 2px solid #ff8c00;
                border-radius: 8px;
                padding: 8px;
                color: #ff8c00;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #ffaa00;
            }
        """)
        input_layout.addRow("E-Mail:", self.email_input)
        
        form_layout.addLayout(input_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.verify_button = QPushButton("🔍 Lizenz prüfen")
        self.verify_button.clicked.connect(self.verify_license)
        self.verify_button.setStyleSheet("""
            QPushButton {
                background-color: #ff8c00;
                color: #000000;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffaa00;
            }
            QPushButton:pressed {
                background-color: #ff6600;
            }
        """)
        button_layout.addWidget(self.verify_button)
        
        self.cancel_button = QPushButton("❌ Beenden")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #ff8c00;
                border: 2px solid #ff8c00;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #ff8c00;
                color: #000000;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        form_layout.addLayout(button_layout)
        
        layout.addWidget(self.license_form)
        
        # Starte automatische Lizenzprüfung
        QTimer.singleShot(1000, self.start_license_check)
    
    def start_license_check(self):
        """Startet die automatische Lizenzprüfung"""
        print("INFO: Starte automatische Lizenzprüfung...")
        
        # Simuliere Lizenzprüfung
        QTimer.singleShot(2000, self.check_existing_license)
    
    def check_existing_license(self):
        """Prüft vorhandene Lizenz"""
        print("INFO: Prüfe vorhandene Lizenz...")
        
        # Simuliere Lizenzprüfung
        import time
        time.sleep(1)
        
        # Simuliere erfolgreiche Lizenzprüfung
        self.progress_bar.setVisible(False)
        self.status_label.setText("✅ Lizenz gültig!")
        self.status_label.setStyleSheet("color: #00ff00; text-align: center;")
        
        print("OK: Lizenzprüfung erfolgreich")
        
        # Schließe Dialog nach kurzer Zeit
        QTimer.singleShot(1500, self.accept)
    
    def verify_license(self):
        """Prüft eingegebene Lizenz"""
        license_number = self.license_input.text().strip()
        email = self.email_input.text().strip()
        
        if not license_number or not email:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie Lizenznummer und E-Mail ein!")
            return
        
        # Simuliere Lizenzprüfung
        self.verify_button.setEnabled(False)
        self.verify_button.setText("🔄 Prüfe...")
        
        QTimer.singleShot(2000, lambda: self.finish_license_check(license_number, email))
    
    def finish_license_check(self, license_number, email):
        """Beendet die Lizenzprüfung"""
        # Simuliere erfolgreiche Prüfung
        self.status_label.setText("✅ Lizenz erfolgreich geprüft!")
        self.status_label.setStyleSheet("color: #00ff00; text-align: center;")
        
        print(f"OK: Lizenz erfolgreich geprüft: {license_number}")
        
        # Schließe Dialog
        QTimer.singleShot(1000, self.accept)
