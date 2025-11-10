"""
License Dialog für OSS goEcommerce
Dialog für Lizenz-Eingabe
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFormLayout, QMessageBox,
                               QProgressBar)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from app.services.license_service import LicenseService
from app.core.debug_manager import debug_print


class LicenseCheckThread(QThread):
    """Worker-Thread für Lizenzprüfung VOR dem Speichern"""
    finished = Signal(bool, dict, str)  # success, response_data, message
    
    def __init__(self, license_service, license_number, email):
        super().__init__()
        self.license_service = license_service
        self.license_number = license_number
        self.email = email
    
    def run(self):
        """Führt die Lizenzprüfung mit temporären Daten aus (ohne zu speichern)"""
        try:
            # Temporär speichern für Prüfung
            old_license, old_email = self.license_service.load_license()
            
            # Speichere temporär die neuen Daten
            self.license_service.save_license(self.license_number, self.email)
            
            # Prüfe über Endpoint
            success, response_data, message = self.license_service.check_license_via_endpoint()
            
            # Stelle alte Daten wieder her, falls Prüfung fehlgeschlagen
            if not success:
                if old_license and old_email:
                    self.license_service.save_license(old_license, old_email)
                else:
                    # Keine alten Daten vorhanden - lösche die neuen
                    self.license_service.clear_license()
            
            self.finished.emit(success, response_data, message)
        except Exception as e:
            # Bei Fehler: Stelle alte Daten wieder her
            try:
                old_license, old_email = self.license_service.load_license()
                if old_license and old_email:
                    self.license_service.save_license(old_license, old_email)
                else:
                    self.license_service.clear_license()
            except:
                pass
            self.finished.emit(False, {}, f"Fehler: {str(e)}")


class LicenseDialog(QDialog):
    """Dialog für Lizenz-Eingabe"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 Lizenz eingeben")
        self.setFixedSize(400, 350)
        self.setModal(True)
        
        # License Service für Speicherung
        self.license_service = LicenseService()
        self.check_thread = None
        
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
        
        # E-Mail (oben)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-Mail eingeben...")
        form_layout.addRow("E-Mail:", self.email_input)
        
        # Lizenznummer (unten)
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("Lizenznummer eingeben...")
        form_layout.addRow("Lizenznummer:", self.license_input)
        
        layout.addLayout(form_layout)
        
        # Progress Bar (versteckt bis zur Prüfung)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Unbestimmter Fortschritt
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status Label (versteckt bis zur Prüfung)
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
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
        """Prüft die Lizenz VOR dem Speichern - speichert nur bei erfolgreicher Prüfung"""
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
        
        # Zeige Progress Bar und Status
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        self.status_label.setText("🔄 Prüfe Lizenz über Server...")
        self.status_label.setStyleSheet("color: #ff8c00;")
        
        # Deaktiviere Buttons während Prüfung
        for button in self.findChildren(QPushButton):
            button.setEnabled(False)
        
        # WICHTIG: Prüfe ZUERST mit den neuen Daten (ohne dauerhaft zu speichern)
        # Starte automatische Lizenzprüfung mit temporären Daten
        self.check_thread = LicenseCheckThread(
            self.license_service, 
            license_number=license_number, 
            email=email
        )
        self.check_thread.finished.connect(self.on_license_check_finished)
        self.check_thread.start()
    
    def on_license_check_finished(self, success, response_data, message):
        """Wird aufgerufen wenn Lizenzprüfung VOR dem Speichern abgeschlossen ist"""
        # Verstecke Progress Bar
        self.progress_bar.setVisible(False)
        
        # Aktiviere Buttons wieder
        for button in self.findChildren(QPushButton):
            button.setEnabled(True)
        
        if success:
            # Lizenzprüfung erfolgreich - Daten sind bereits gespeichert (im Thread)
            self.status_label.setText("✅ Lizenz erfolgreich geprüft und gespeichert!")
            self.status_label.setStyleSheet("color: #00ff00;")
            debug_print(f"OK: Lizenzprüfung erfolgreich - {message}")
            
            QMessageBox.information(
                self, 
                "Erfolg", 
                f"Lizenzdaten wurden erfolgreich geprüft und gespeichert!\n\n"
                f"Lizenznummer: {self.license_input.text().strip()}\n"
                f"E-Mail: {self.email_input.text().strip()}\n\n"
                f"Status: {message}"
            )
            
            # Schließe diesen Dialog - das LicenseGUIWindow wird automatisch eine neue Prüfung starten
            self.accept()
        else:
            # Lizenzprüfung fehlgeschlagen - Daten wurden NICHT gespeichert (Thread hat alte Daten wiederhergestellt)
            self.status_label.setText("❌ Lizenzprüfung fehlgeschlagen")
            self.status_label.setStyleSheet("color: #ff4444;")
            debug_print(f"FEHLER: Lizenzprüfung fehlgeschlagen - {message}")
            
            QMessageBox.critical(
                self, 
                "Lizenzprüfung fehlgeschlagen", 
                f"Die Lizenzprüfung war nicht erfolgreich:\n\n{message}\n\n"
                "Bitte überprüfen Sie Ihre Lizenzdaten und versuchen Sie es erneut.\n\n"
                "Die Daten wurden NICHT gespeichert."
            )

