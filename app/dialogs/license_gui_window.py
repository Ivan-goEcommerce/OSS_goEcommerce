"""
License GUI Window für OSS goEcommerce
Zeigt Lizenzstatus und ermöglicht Lizenz-Eingabe
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFormLayout, QMessageBox,
                               QProgressBar, QFrame)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont

from app.services.license_service import LicenseService
from app.core.debug_manager import debug_print


class LicenseCheckThread(QThread):
    """Worker-Thread für Lizenzprüfung über Endpoint"""
    finished = Signal(bool, dict, str)  # success, response_data, message
    
    def __init__(self, license_service, license_number=None, email=None):
        super().__init__()
        self.license_service = license_service
        self.license_number = license_number
        self.email = email
        self.check_new_license = license_number is not None and email is not None
    
    def run(self):
        """Führt die Lizenzprüfung aus"""
        try:
            if self.check_new_license:
                # Speichere neue Lizenzdaten zuerst
                self.license_service.save_license(self.license_number, self.email)
            
            # Prüfe über Endpoint
            success, response_data, message = self.license_service.check_license_via_endpoint()
            self.finished.emit(success, response_data, message)
        except Exception as e:
            self.finished.emit(False, {}, f"Fehler: {str(e)}")


class LicenseGUIWindow(QDialog):
    """GUI-Fenster für Lizenz-Management"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 OSS goEcommerce - Lizenzprüfung")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        self.license_valid = False
        self.license_service = LicenseService()
        self.check_thread = None
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
        
        # Error-Buttons-Frame (nur für Fehler bei automatischer Prüfung)
        self.error_buttons_frame = QFrame()
        self.error_buttons_frame.setVisible(False)
        error_buttons_layout = QHBoxLayout(self.error_buttons_frame)
        error_buttons_layout.setContentsMargins(0, 15, 0, 0)
        error_buttons_layout.setSpacing(10)
        
        self.enter_license_button = QPushButton("🔑 Lizenz eingeben")
        self.enter_license_button.clicked.connect(self.show_license_form_on_error)
        self.enter_license_button.setStyleSheet("""
            QPushButton {
                background-color: #ff8c00;
                color: #000000;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffaa00;
            }
            QPushButton:pressed {
                background-color: #ff6600;
            }
        """)
        
        self.close_button = QPushButton("❌ Beenden")
        self.close_button.clicked.connect(self.reject)
        self.close_button.setStyleSheet("""
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
        error_buttons_layout.addStretch()
        error_buttons_layout.addWidget(self.enter_license_button)
        error_buttons_layout.addWidget(self.close_button)
        error_buttons_layout.addStretch()
        
        layout.addWidget(self.error_buttons_frame)
        
        # Lizenz-Formular (versteckt bis benötigt - nur wenn KEINE Lizenzdaten vorhanden)
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
        debug_print("INFO: Starte automatische Lizenzprüfung...")
        
        # Prüfe ob Lizenzdaten vorhanden sind
        if not self.license_service.has_license():
            # Keine Lizenzdaten gefunden - zeige Eingabeformular
            debug_print("WARNUNG: Keine Lizenzdaten gefunden - zeige Eingabeformular")
            self.progress_bar.setVisible(False)
            self.status_label.setText("❌ Keine Lizenzdaten gefunden")
            self.status_label.setStyleSheet("color: #ff4444; text-align: center;")
            self.license_form.setVisible(True)
            return
        
        # Prüfe vorhandene Lizenz über Endpoint
        QTimer.singleShot(500, self.check_existing_license)
    
    def check_existing_license(self):
        """Prüft vorhandene Lizenz über Endpoint"""
        debug_print("INFO: Prüfe vorhandene Lizenz über Endpoint...")
        
        # Erstelle Worker-Thread für HTTP-Request
        self.check_thread = LicenseCheckThread(self.license_service)
        self.check_thread.finished.connect(self.on_license_check_finished)
        self.check_thread.start()
    
    def on_license_check_finished(self, success, response_data, message):
        """Wird aufgerufen wenn automatische Lizenzprüfung abgeschlossen ist"""
        self.progress_bar.setVisible(False)
        
        if success:
            # Lizenzprüfung erfolgreich
            self.status_label.setText("✅ Lizenz gültig!")
            self.status_label.setStyleSheet("color: #00ff00; text-align: center;")
            debug_print(f"OK: Lizenzprüfung erfolgreich - {message}")
            debug_print(f"Response: {response_data}")
            self.license_valid = True
            
            # Schließe Dialog nach kurzer Zeit
            QTimer.singleShot(1500, self.accept)
        else:
            # Lizenzprüfung fehlgeschlagen - zeige NUR Fehlermeldung und Beenden-Button
            self.status_label.setText(f"❌ Lizenzprüfung fehlgeschlagen\n\n{message}")
            self.status_label.setStyleSheet("color: #ff4444; text-align: center;")
            debug_print(f"FEHLER: Lizenzprüfung fehlgeschlagen - {message}")
            debug_print(f"Response: {response_data}")
            
            # Zeige Buttons (Lizenz eingeben + Beenden), aber verstecke zunächst Eingabefelder
            self.error_buttons_frame.setVisible(True)
            self.license_form.setVisible(False)
    
    def show_license_form_on_error(self):
        """Zeigt Eingabeformular wenn User auf 'Lizenz eingeben' klickt"""
        # Verstecke Fehler-Buttons
        self.error_buttons_frame.setVisible(False)
        # Zeige Eingabeformular
        self.license_form.setVisible(True)
        # Aktualisiere Status-Label
        self.status_label.setText("Bitte geben Sie neue Lizenzdaten ein:")
        self.status_label.setStyleSheet("color: #ff8c00; text-align: center;")
    
    def verify_license(self):
        """Prüft eingegebene Lizenz über Endpoint"""
        license_number = self.license_input.text().strip()
        email = self.email_input.text().strip()
        
        if not license_number or not email:
            QMessageBox.warning(self, "Fehler", "Bitte geben Sie Lizenznummer und E-Mail ein!")
            return
        
        # Deaktiviere Button während Prüfung
        self.verify_button.setEnabled(False)
        self.verify_button.setText("🔄 Prüfe über Server...")
        self.status_label.setText("🔄 Prüfe Lizenz über Server...")
        self.status_label.setStyleSheet("color: #ff8c00; text-align: center;")
        self.progress_bar.setVisible(True)
        
        # Erstelle Worker-Thread für HTTP-Request
        self.check_thread = LicenseCheckThread(
            self.license_service, 
            license_number=license_number, 
            email=email
        )
        self.check_thread.finished.connect(self.finish_license_check)
        self.check_thread.start()
    
    def finish_license_check(self, success, response_data, message):
        """Beendet die Lizenzprüfung"""
        self.progress_bar.setVisible(False)
        self.verify_button.setEnabled(True)
        self.verify_button.setText("🔍 Lizenz prüfen")
        
        if success:
            # Lizenzprüfung erfolgreich
            self.status_label.setText("✅ Lizenz erfolgreich geprüft!")
            self.status_label.setStyleSheet("color: #00ff00; text-align: center;")
            debug_print(f"OK: Lizenz erfolgreich geprüft - {message}")
            debug_print(f"Response: {response_data}")
            self.license_valid = True
            
            # Schließe Dialog nach kurzer Zeit
            QTimer.singleShot(1500, self.accept)
        else:
            # Lizenzprüfung fehlgeschlagen
            self.status_label.setText(f"❌ Lizenzprüfung fehlgeschlagen\n{message}")
            self.status_label.setStyleSheet("color: #ff4444; text-align: center;")
            QMessageBox.warning(
                self, 
                "Lizenzprüfung fehlgeschlagen", 
                f"Die Lizenzprüfung war nicht erfolgreich:\n\n{message}\n\n"
                "Bitte überprüfen Sie Ihre Lizenzdaten und versuchen Sie es erneut."
            )
            debug_print(f"FEHLER: Lizenzprüfung fehlgeschlagen - {message}")
