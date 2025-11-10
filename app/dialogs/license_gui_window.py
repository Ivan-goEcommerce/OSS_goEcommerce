"""
License GUI Window für OSS goEcommerce
Zeigt Lizenzstatus und ermöglicht Lizenz-Eingabe
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QMessageBox,
                               QProgressBar, QFrame)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont

from app.services.license_service import LicenseService
from app.core.debug_manager import debug_print
from app.dialogs.license_dialog import LicenseDialog


class LicenseCheckThread(QThread):
    """Worker-Thread für Lizenzprüfung über Endpoint"""
    finished = Signal(bool, dict, str)  # success, response_data, message
    valid_to_received = Signal(str)  # valid_to date
    
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
            
            # Extrahiere "valid to" aus response_data wenn vorhanden
            if success and isinstance(response_data, dict):
                valid_to = response_data.get('valid_to') or response_data.get('validTo') or response_data.get('valid_to_date')
                if valid_to:
                    self.valid_to_received.emit(str(valid_to))
            
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
        self.valid_to_date = None  # Speichere valid_to Datum
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
        self.enter_license_button.clicked.connect(self._open_license_dialog_and_close)
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
        
        # Starte automatische Lizenzprüfung
        QTimer.singleShot(1000, self.start_license_check)
    
    def start_license_check(self):
        """Startet die automatische Lizenzprüfung"""
        debug_print("INFO: Starte automatische Lizenzprüfung...")
        
        # Prüfe ob Lizenzdaten vorhanden sind
        if not self.license_service.has_license():
            # Keine Lizenzdaten gefunden - schließe Fenster und zeige LicenseDialog
            debug_print("WARNUNG: Keine Lizenzdaten gefunden - schließe Fenster und öffne LicenseDialog")
            self.progress_bar.setVisible(False)
            self.status_label.setText("❌ Keine Lizenzdaten gefunden")
            self.status_label.setStyleSheet("color: #ff4444; text-align: center;")
            
            # Schließe dieses Fenster und öffne LicenseDialog
            QTimer.singleShot(500, self._open_license_dialog_and_close)
            return
        
        # Prüfe vorhandene Lizenz über Endpoint
        QTimer.singleShot(500, self.check_existing_license)
    
    def check_existing_license(self):
        """Prüft vorhandene Lizenz über Endpoint"""
        debug_print("INFO: Prüfe vorhandene Lizenz über Endpoint...")
        
        # Erstelle Worker-Thread für HTTP-Request
        self.check_thread = LicenseCheckThread(self.license_service)
        self.check_thread.finished.connect(self.on_license_check_finished)
        self.check_thread.valid_to_received.connect(self.on_valid_to_received)
        self.check_thread.start()
    
    def on_valid_to_received(self, valid_to: str):
        """Wird aufgerufen wenn valid_to vom Server empfangen wurde"""
        # Speichere valid_to für späteren Zugriff
        self.valid_to_date = valid_to
        debug_print(f"DEBUG: valid_to empfangen: {valid_to}")
    
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
            
            # Extrahiere valid_to aus response_data (falls noch nicht über Signal empfangen)
            if isinstance(response_data, dict):
                valid_to = response_data.get('valid_to') or response_data.get('validTo') or response_data.get('valid_to_date')
                if valid_to:
                    self.valid_to_date = str(valid_to)
                    debug_print(f"DEBUG: valid_to aus response_data extrahiert: {valid_to}")
            
            # Schließe Dialog nach kurzer Zeit
            QTimer.singleShot(1500, self.accept)
        else:
            # Lizenzprüfung fehlgeschlagen - zeige Fehlerfenster und öffne dann LicenseDialog
            debug_print(f"FEHLER: Lizenzprüfung fehlgeschlagen - {message}")
            debug_print(f"Response: {response_data}")
            
            # Zeige Fehlerfenster
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("❌ Lizenzprüfung fehlgeschlagen")
            msg_box.setText(f"Die Lizenzprüfung war nicht erfolgreich:\n\n{message}\n\n"
                          "Bitte geben Sie neue Lizenzdaten ein.")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setStandardButtons(QMessageBox.Ok)
            
            # Nach OK: Schließe dieses Fenster und öffne LicenseDialog
            msg_box.finished.connect(lambda result: self._open_license_dialog_and_close())
            msg_box.exec()
    
    def _open_license_dialog_and_close(self):
        """Schließt dieses Fenster und öffnet LicenseDialog - nach erfolgreichem Speichern wird neue Prüfung gestartet"""
        # Öffne LicenseDialog im Hauptfenster (NICHT schließen, damit wir das Ergebnis zurückgeben können)
        parent = self.parent()
        if parent:
            license_dialog = LicenseDialog(parent)
            dialog_result = license_dialog.exec()
            
            # Wenn LicenseDialog erfolgreich war (neue Daten gespeichert und geprüft)
            # dann prüfe nochmal mit den neuen Daten
            if dialog_result == QDialog.Accepted:
                debug_print("LicenseDialog erfolgreich - starte neue Prüfung mit gespeicherten Daten")
                # Prüfe nochmal mit den gespeicherten Daten
                QTimer.singleShot(500, self._recheck_license_after_save)
            else:
                # LicenseDialog abgebrochen oder fehlgeschlagen - schließe dieses Fenster
                debug_print("LicenseDialog abgebrochen - schließe LicenseGUIWindow")
                self.reject()
    
    def _recheck_license_after_save(self):
        """Prüft Lizenz erneut nach erfolgreichem Speichern neuer Daten"""
        debug_print("INFO: Prüfe Lizenz erneut nach erfolgreichem Speichern...")
        
        # Zeige Progress Bar
        self.progress_bar.setVisible(True)
        self.status_label.setText("🔄 Prüfe neue Lizenzdaten...")
        self.status_label.setStyleSheet("color: #ff8c00; text-align: center;")
        
        # Prüfe vorhandene Lizenz über Endpoint
        self.check_thread = LicenseCheckThread(self.license_service)
        self.check_thread.finished.connect(self.on_license_check_finished)
        self.check_thread.start()
