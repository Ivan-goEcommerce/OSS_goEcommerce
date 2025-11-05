"""
Go OSS Dashboard - Neue Hauptansicht
Entspricht dem Design aus dem Foto
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QFrame, QGridLayout, QMessageBox, QDialog, QProgressDialog)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPainter, QColor

from ..managers.license_manager import LicenseManager
from ..managers.oss_schema_manager import OSSSchemaManager
from ..dialogs import JTLConnectionDialog, LicenseDialog, LicenseGUIWindow
from ..workers.sync_worker import JTLToN8nSyncWorker


class DashboardWindow(QMainWindow):
    """Hauptfenster mit Dashboard-Ansicht wie im Foto"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Go OSS - Dashboard")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Managers
        self.license_manager = LicenseManager()
        self.oss_schema_manager = None
        
        # Daten für die Cards
        self.taric_total_count = 0
        self.articles_with_taric = 0
        self.articles_without_taric = 0
        self.license_status = "Aktiv"
        self.license_expiry = "12/2026"
        self.last_sync_date = "24.04.2024, 10:32"
        self.app_version = "1.0.0"
        
        # Label-Referenzen (werden in setup_data_cards gesetzt)
        self.taric_total_label = None
        self.articles_with_label = None
        self.articles_without_label = None
        self.license_status_label = None
        self.license_expiry_label = None
        
        # Status-Indikatoren
        self.license_status_indicator = None  # Grüner/roter Punkt für Lizenz
        self.db_status_indicator = None  # Grüner/roter Punkt für DB
        self.license_valid = False
        self.db_connected = False
        
        # Sync Worker
        self.sync_worker = None
        
        # Dark Theme Style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QLabel {
                color: #b0b0b0;
            }
            QPushButton {
                background-color: #ff8c00;
                color: #000000;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ffaa00;
            }
            QPushButton:pressed {
                background-color: #ff6600;
            }
        """)
        
        # App zunächst sperren bis Lizenz geprüft ist
        self.setEnabled(False)
        
        self.setup_ui()
        
        # SOFORT Lizenzprüfung beim Start (blockiert App)
        QTimer.singleShot(500, self.check_license_on_startup)
    
    def setup_ui(self):
        """Erstellt die UI-Struktur wie im Foto"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header (mit Fenstersteuerung und Einstellungen)
        self.setup_header(main_layout)
        
        # Hauptbereich
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(30)
        
        # App-Titel und Navigation
        self.setup_app_title(content_layout)
        
        # Daten-Cards
        self.setup_data_cards(content_layout)
        
        # Action Button
        self.setup_action_button(content_layout)
        
        # Footer
        self.footer_label = self.setup_footer(content_layout)
        
        main_layout.addWidget(content_widget)
    
    def setup_header(self, parent_layout):
        """Header mit Fenstersteuerung und Titel"""
        header_frame = QFrame()
        header_frame.setFixedHeight(40)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-bottom: 1px solid #333333;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 5, 15, 5)
        header_layout.setSpacing(10)
        
        # Fenstersteuerung (drei kleine Kreise)
        window_controls = QHBoxLayout()
        window_controls.setSpacing(8)
        for i in range(3):
            circle = QLabel()
            circle.setFixedSize(12, 12)
            circle.setStyleSheet("""
                QLabel {
                    background-color: #666666;
                    border-radius: 6px;
                }
            """)
            window_controls.addWidget(circle)
        
        header_layout.addLayout(window_controls)
        
        # Einstellungs-Icon
        settings_label = QLabel("⚙")
        settings_label.setStyleSheet("""
            QLabel {
                color: #b0b0b0;
                font-size: 16px;
            }
        """)
        header_layout.addWidget(settings_label)
        
        # Titel (zentriert)
        title_label = QLabel("Go OSS - Dashboard")
        title_label.setStyleSheet("""
            QLabel {
                color: #b0b0b0;
                font-size: 14px;
            }
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        parent_layout.addWidget(header_frame)
    
    def create_logo_widget(self):
        """Erstellt das Go OSS Logo Widget"""
        logo_frame = QFrame()
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(10)
        
        # Blauer Quadrat-Icon mit "Go" Text
        icon_container = QFrame()
        icon_container.setFixedSize(50, 50)
        icon_container.setStyleSheet("""
            QFrame {
                background-color: #4169e1;
                border-radius: 8px;
            }
        """)
        
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignCenter)
        
        go_label = QLabel("Go")
        go_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        go_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(go_label)
        
        # "OSS" Text daneben
        oss_label = QLabel("OSS")
        oss_label.setFont(QFont("Arial", 24, QFont.Bold))
        oss_label.setStyleSheet("color: #ffffff;")
        
        logo_layout.addWidget(icon_container)
        logo_layout.addWidget(oss_label)
        
        return logo_frame
    
    def setup_app_title(self, parent_layout):
        """App-Titel mit Logo und Buttons"""
        title_frame = QFrame()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(20)
        
        # Links: Go OSS Logo
        logo_widget = self.create_logo_widget()
        title_layout.addWidget(logo_widget)
        title_layout.addStretch()
        
        # Status-Indikatoren
        status_layout = QHBoxLayout()
        status_layout.setSpacing(15)
        
        # Lizenz-Status-Indikator
        license_frame = QFrame()
        license_frame_layout = QHBoxLayout(license_frame)
        license_frame_layout.setContentsMargins(5, 5, 5, 5)
        license_frame_layout.setSpacing(8)
        
        self.license_status_indicator = QLabel()
        self.license_status_indicator.setFixedSize(10, 10)
        self.license_status_indicator.setStyleSheet("""
            QLabel {
                background-color: #ff0000;
                border-radius: 5px;
            }
        """)
        license_frame_layout.addWidget(self.license_status_indicator)
        
        license_text = QLabel("Lizenz: Invalid")
        license_text.setObjectName("license_text")
        license_text.setStyleSheet("color: #ff0000; font-size: 11px;")
        license_frame_layout.addWidget(license_text)
        self.license_text_label = license_text
        
        status_layout.addWidget(license_frame)
        
        # DB-Status-Indikator
        db_frame = QFrame()
        db_frame_layout = QHBoxLayout(db_frame)
        db_frame_layout.setContentsMargins(5, 5, 5, 5)
        db_frame_layout.setSpacing(8)
        
        self.db_status_indicator = QLabel()
        self.db_status_indicator.setFixedSize(10, 10)
        self.db_status_indicator.setStyleSheet("""
            QLabel {
                background-color: #ff0000;
                border-radius: 5px;
            }
        """)
        db_frame_layout.addWidget(self.db_status_indicator)
        
        db_text = QLabel("DB: Not Connected")
        db_text.setObjectName("db_text")
        db_text.setStyleSheet("color: #ff0000; font-size: 11px;")
        db_frame_layout.addWidget(db_text)
        self.db_text_label = db_text
        
        status_layout.addWidget(db_frame)
        
        # Buttons
        btn_lizenz = QPushButton("Lizenz prüfen")
        btn_lizenz.clicked.connect(self.show_license_dialog)
        btn_lizenz.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #b0b0b0;
                border: 1px solid #555555;
            }
            QPushButton:hover {
                background-color: #444444;
            }
        """)
        
        btn_db = QPushButton("DB Credentials")
        btn_db.clicked.connect(self.show_db_credentials_dialog)
        btn_db.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #b0b0b0;
                border: 1px solid #555555;
            }
            QPushButton:hover {
                background-color: #444444;
            }
        """)
        
        status_layout.addWidget(btn_lizenz)
        status_layout.addWidget(btn_db)
        
        title_layout.addLayout(status_layout)
        
        parent_layout.addWidget(title_frame)
    
    def setup_data_cards(self, parent_layout):
        """4 Daten-Cards in 2x2 Grid"""
        cards_grid = QGridLayout()
        cards_grid.setSpacing(20)
        
        # Card 1: Gesamtanzahl Taric-Nummern
        card1 = self.create_data_card("Gesamtanzahl Taric-Nummern", "2 543")
        cards_grid.addWidget(card1, 0, 0)
        # Finde das value_label
        for widget in card1.findChildren(QLabel):
            if widget.objectName() == "value_label":
                self.taric_total_label = widget
                break
        
        # Card 2: Artikel mit Taric
        card2 = self.create_data_card("Artikel mit Taric", "2 122")
        cards_grid.addWidget(card2, 0, 1)
        # Finde das value_label
        for widget in card2.findChildren(QLabel):
            if widget.objectName() == "value_label":
                self.articles_with_label = widget
                break
        
        # Card 3: Artikel ohne Taric
        card3 = self.create_data_card("Artikel ohne Taric", "421")
        cards_grid.addWidget(card3, 1, 0)
        # Finde das value_label
        for widget in card3.findChildren(QLabel):
            if widget.objectName() == "value_label":
                self.articles_without_label = widget
                break
        
        # Card 4: Lizenzstatus
        card4 = self.create_license_card()
        cards_grid.addWidget(card4, 1, 1)
        # Finde die Labels
        for widget in card4.findChildren(QLabel):
            if widget.objectName() == "status_label":
                self.license_status_label = widget
            elif widget.objectName() == "expiry_label":
                self.license_expiry_label = widget
        
        parent_layout.addLayout(cards_grid)
    
    def create_data_card(self, title, value):
        """Erstellt eine Daten-Card"""
        card_frame = QFrame()
        card_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        card_frame.setMinimumHeight(150)
        
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)
        
        # Titel
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #b0b0b0;
                font-size: 14px;
            }
        """)
        card_layout.addWidget(title_label)
        
        # Wert
        value_label = QLabel(value)
        value_label.setObjectName("value_label")
        value_label.setFont(QFont("Arial", 32, QFont.Bold))
        value_label.setStyleSheet("""
            QLabel {
                color: #b0b0b0;
            }
        """)
        card_layout.addWidget(value_label)
        card_layout.addStretch()
        
        return card_frame
    
    def create_license_card(self):
        """Erstellt die Lizenzstatus-Card"""
        card_frame = QFrame()
        card_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        card_frame.setMinimumHeight(150)
        
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)
        
        # Titel
        title_label = QLabel("Lizenzstatus")
        title_label.setStyleSheet("""
            QLabel {
                color: #b0b0b0;
                font-size: 14px;
            }
        """)
        card_layout.addWidget(title_label)
        
        # Status mit grünem Punkt
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        
        # Grüner Punkt
        green_dot = QLabel()
        green_dot.setFixedSize(12, 12)
        green_dot.setStyleSheet("""
            QLabel {
                background-color: #00ff00;
                border-radius: 6px;
            }
        """)
        status_layout.addWidget(green_dot)
        
        # Status-Text
        status_label = QLabel("Aktiv")
        status_label.setObjectName("status_label")
        status_label.setFont(QFont("Arial", 32, QFont.Bold))
        status_label.setStyleSheet("color: #b0b0b0;")
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        
        card_layout.addLayout(status_layout)
        
        # Ablaufdatum
        expiry_label = QLabel("bis 12/2026")
        expiry_label.setObjectName("expiry_label")
        expiry_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
            }
        """)
        card_layout.addWidget(expiry_label)
        card_layout.addStretch()
        
        return card_frame
    
    def setup_action_button(self, parent_layout):
        """Großer Action-Button"""
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)
        
        action_button = QPushButton("OSS-Abgleich starten")
        action_button.setMinimumSize(400, 60)
        action_button.setFont(QFont("Arial", 16, QFont.Bold))
        action_button.setStyleSheet("""
            QPushButton {
                background-color: #ff8c00;
                color: #000000;
                border: none;
                border-radius: 10px;
                padding: 15px 40px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #ffaa00;
            }
            QPushButton:pressed {
                background-color: #ff6600;
            }
        """)
        action_button.clicked.connect(self.start_oss_sync)
        button_layout.addWidget(action_button)
        
        parent_layout.addLayout(button_layout)
    
    def setup_footer(self, parent_layout):
        """Footer mit Version und letztem Abgleich"""
        footer_label = QLabel(f"Version {self.app_version} • Letzter Abgleich: {self.last_sync_date}")
        footer_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                padding: 10px;
            }
        """)
        footer_label.setAlignment(Qt.AlignCenter)
        parent_layout.addWidget(footer_label)
        return footer_label
    
    def check_license_on_startup(self):
        """Prüft Lizenz beim Start - BLOCKIERT APP bis erfolgreich"""
        print("INFO: Starte Lizenzprüfung beim Start...")
        
        # Zeige Lizenz-GUI-Fenster (blockierend)
        license_window = LicenseGUIWindow(self)
        result = license_window.exec()
        
        if result == QDialog.Accepted:
            # Lizenzprüfung erfolgreich - App freigeben
            self.license_valid = True
            self.setEnabled(True)
            self.update_license_status(True)
            print("OK: Lizenzprüfung erfolgreich - App freigegeben")
            
            # Starte DB-Verbindungstest
            QTimer.singleShot(1000, self.check_database_connection)
            
            # Lade Statistiken
            QTimer.singleShot(2000, self.load_database_stats)
        else:
            # Lizenzprüfung fehlgeschlagen - App beenden
            print("FEHLER: Lizenzprüfung fehlgeschlagen - App wird beendet")
            QMessageBox.critical(
                self,
                "Lizenzfehler",
                "Die Lizenzprüfung war nicht erfolgreich.\n\nDie Anwendung wird jetzt beendet."
            )
            self.close()
    
    def check_database_connection(self):
        """Prüft DB-Verbindung und aktualisiert Status"""
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from jtl_database_manager import JTLDatabaseManager
            
            db_manager = JTLDatabaseManager()
            
            if db_manager.has_saved_credentials():
                success, message = db_manager.test_connection()
                
                if success:
                    self.db_connected = True
                    self.update_db_status(True)
                    print("OK: DB-Verbindung erfolgreich")
                else:
                    self.db_connected = False
                    self.update_db_status(False)
                    print(f"FEHLER: DB-Verbindung fehlgeschlagen: {message}")
            else:
                self.db_connected = False
                self.update_db_status(False)
                print("WARNUNG: Keine DB-Credentials konfiguriert")
                
        except Exception as e:
            print(f"FEHLER beim DB-Verbindungstest: {e}")
            self.db_connected = False
            self.update_db_status(False)
    
    def update_license_status(self, is_valid):
        """Aktualisiert den Lizenz-Status-Indikator"""
        self.license_valid = is_valid
        
        if self.license_status_indicator:
            color = "#00ff00" if is_valid else "#ff0000"
            self.license_status_indicator.setStyleSheet(f"""
                QLabel {{
                    background-color: {color};
                    border-radius: 5px;
                }}
            """)
        
        if self.license_text_label:
            text = "Lizenz: Valid" if is_valid else "Lizenz: Invalid"
            color = "#00ff00" if is_valid else "#ff0000"
            self.license_text_label.setText(text)
            self.license_text_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        
        if self.license_status_label:
            self.license_status_label.setText("Aktiv" if is_valid else "Inaktiv")
        
        if is_valid and self.license_expiry_label:
            self.license_expiry_label.setText(f"bis {self.license_expiry}")
    
    def update_db_status(self, is_connected):
        """Aktualisiert den DB-Status-Indikator"""
        self.db_connected = is_connected
        
        if self.db_status_indicator:
            color = "#00ff00" if is_connected else "#ff0000"
            self.db_status_indicator.setStyleSheet(f"""
                QLabel {{
                    background-color: {color};
                    border-radius: 5px;
                }}
            """)
        
        if self.db_text_label:
            text = "DB: Connected" if is_connected else "DB: Not Connected"
            color = "#00ff00" if is_connected else "#ff0000"
            self.db_text_label.setText(text)
            self.db_text_label.setStyleSheet(f"color: {color}; font-size: 11px;")
    
    def load_database_stats(self):
        """Lädt Datenbankstatistiken aus JTL-Datenbank"""
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from jtl_database_manager import JTLDatabaseManager
            
            db_manager = JTLDatabaseManager()
            
            if not db_manager.has_saved_credentials():
                # Keine Credentials - zeige Platzhalter
                if self.taric_total_label:
                    self.taric_total_label.setText("--")
                if self.articles_with_label:
                    self.articles_with_label.setText("--")
                if self.articles_without_label:
                    self.articles_without_label.setText("--")
                return
            
            success, message = db_manager.test_connection()
            
            if not success:
                # Verbindung fehlgeschlagen - zeige Platzhalter
                if self.taric_total_label:
                    self.taric_total_label.setText("--")
                if self.articles_with_label:
                    self.articles_with_label.setText("--")
                if self.articles_without_label:
                    self.articles_without_label.setText("--")
                return
            
            # Hole Gesamtanzahl Taric-Nummern (eindeutige TARIC-Codes)
            success, message, taric_count = db_manager.get_article_count_with_ctaric()
            if success and taric_count is not None:
                self.taric_total_count = taric_count
                if self.taric_total_label:
                    formatted = f"{taric_count:,}".replace(",", " ")
                    self.taric_total_label.setText(formatted)
            
            # Hole Artikel mit Taric (Artikel, die ein ctaric-Feld haben und nicht leer/null)
            sql_with_taric = """
                SELECT COUNT(*) as count
                FROM tArtikel
                WHERE LEN(LTRIM(RTRIM(ISNULL(ctaric, '')))) > 0
            """
            success, message, results = db_manager.execute_jtl_query(sql_with_taric)
            if success and results:
                count = results[0][0] if results else 0
                self.articles_with_taric = count
                if self.articles_with_label:
                    formatted = f"{count:,}".replace(",", " ")
                    self.articles_with_label.setText(formatted)
            
            # Hole Artikel ohne Taric
            sql_without_taric = """
                SELECT COUNT(*) as count
                FROM tArtikel
                WHERE LEN(LTRIM(RTRIM(ISNULL(ctaric, '')))) = 0 OR ctaric IS NULL
            """
            success, message, results = db_manager.execute_jtl_query(sql_without_taric)
            if success and results:
                count = results[0][0] if results else 0
                self.articles_without_taric = count
                if self.articles_without_label:
                    formatted = f"{count:,}".replace(",", " ")
                    self.articles_without_label.setText(formatted)
                    
        except Exception as e:
            print(f"Fehler beim Laden der Statistiken: {e}")
            # Bei Fehler zeige Platzhalter
            if self.taric_total_label:
                self.taric_total_label.setText("--")
            if self.articles_with_label:
                self.articles_with_label.setText("--")
            if self.articles_without_label:
                self.articles_without_label.setText("--")
    
    def show_license_dialog(self):
        """Zeigt Lizenz-Dialog"""
        dialog = LicenseDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # Nach erfolgreichem Dialog Lizenz-Status aktualisieren
            self.update_license_status(True)
            self.license_valid = True
    
    def show_db_credentials_dialog(self):
        """Zeigt DB Credentials Dialog"""
        dialog = JTLConnectionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # Nach erfolgreichem Dialog DB-Status prüfen
            QTimer.singleShot(500, self.check_database_connection)
            QTimer.singleShot(1000, self.load_database_stats)
    
    def start_oss_sync(self):
        """Startet OSS-Abgleich"""
        # Prüfe ob bereits ein Worker läuft
        if self.sync_worker and self.sync_worker.isRunning():
            QMessageBox.warning(
                self,
                "Synchronisation läuft",
                "Eine Synchronisation läuft bereits. Bitte warten Sie, bis diese abgeschlossen ist."
            )
            return
        
        # Prüfe DB-Verbindung
        if not self.db_connected:
            reply = QMessageBox.question(
                self,
                "Keine DB-Verbindung",
                "Keine Datenbankverbindung vorhanden.\n\nMöchten Sie trotzdem fortfahren?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # Zeige Bestätigungsdialog
        reply = QMessageBox.question(
            self,
            "OSS-Abgleich starten?",
            "Möchten Sie den OSS-Abgleich starten?\n\n"
            "Diese Aktion synchronisiert die JTL-Datenbank mit n8n und kann einige Minuten dauern.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.start_sync_worker()
    
    def start_sync_worker(self):
        """Startet den Synchronisations-Worker"""
        # Erstelle Worker
        self.sync_worker = JTLToN8nSyncWorker()
        
        # Erstelle Progress-Dialog
        self.progress_dialog = QProgressDialog("OSS-Abgleich wird durchgeführt...", "Abbrechen", 0, 0, self)
        self.progress_dialog.setWindowTitle("OSS-Abgleich")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setCancelButton(None)  # Deaktiviere Abbrechen-Button
        
        # Verbinde Signale
        self.sync_worker.progress.connect(self.on_sync_progress)
        self.sync_worker.finished.connect(self.on_sync_finished)
        
        # Starte Worker
        self.sync_worker.start()
        self.progress_dialog.show()
        
        print("INFO: OSS-Abgleich Worker gestartet")
    
    def on_sync_progress(self, message):
        """Behandelt Progress-Updates vom Worker"""
        print(f"Progress: {message}")
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setLabelText(message)
    
    def on_sync_finished(self, success, message, product_count):
        """Behandelt das Ende der Synchronisation"""
        # Schließe Progress-Dialog
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # Aktualisiere letzten Abgleich
        from datetime import datetime
        self.last_sync_date = datetime.now().strftime("%d.%m.%Y, %H:%M")
        
        # Aktualisiere Footer
        if hasattr(self, 'footer_label') and self.footer_label:
            self.footer_label.setText(f"Version {self.app_version} • Letzter Abgleich: {self.last_sync_date}")
        
        # Zeige Ergebnis-Dialog
        if success:
            QMessageBox.information(
                self,
                "OSS-Abgleich erfolgreich",
                f"✅ {message}\n\n{product_count} Produkte wurden synchronisiert."
            )
            
            # Aktualisiere Statistiken nach Sync
            QTimer.singleShot(500, self.load_database_stats)
        else:
            QMessageBox.critical(
                self,
                "OSS-Abgleich fehlgeschlagen",
                f"❌ {message}"
            )
        
        # Cleanup Worker
        if self.sync_worker:
            self.sync_worker.deleteLater()
            self.sync_worker = None
        
        print(f"OSS-Abgleich beendet: success={success}, message={message}")
