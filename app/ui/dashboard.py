"""
Go OSS Dashboard - Neue Hauptansicht
Entspricht dem Design aus dem Foto
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QFrame, QGridLayout, QMessageBox, QDialog, QProgressDialog)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPainter, QColor
import json
import os
from datetime import datetime
from pathlib import Path

from ..managers.license_manager import LicenseManager
from ..dialogs import JTLConnectionDialog, LicenseDialog, LicenseGUIWindow, DecryptDialog
from ..workers.sync_worker import JTLToN8nSyncWorker
from ..workers.trigger_fetch_worker import TriggerFetchWorker
from ..workers.oss_start_worker import OSSStartWorker
from ..services.trigger_endpoint_service import TriggerEndpointService
from ..core.logging_config import get_logger
from ..core.debug_manager import debug_print, debug_info

logger = get_logger(__name__)


class DashboardWindow(QMainWindow):
    """Hauptfenster mit Dashboard-Ansicht wie im Foto"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Go OSS - Dashboard")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Managers
        self.license_manager = LicenseManager()
        
        # Daten für die Cards
        self.taric_total_count = 0
        self.articles_with_taric = 0
        self.articles_without_taric = 0
        self.license_status = "Aktiv"
        self.license_expiry = "12/2026"
        self.last_sync_date = self.load_last_sync_date()  # Lade gespeichertes Datum
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
        
        # OSS-Button Referenz und Status
        self.oss_button = None
        self.trigger_successfully_created = False  # True nur wenn Trigger erfolgreich erstellt wurde
        
        # Sync Worker
        self.sync_worker = None
        
        # Service für Trigger-Update (verwendet automatisch Lizenz-Daten)
        self.trigger_endpoint_service = TriggerEndpointService()
        self.trigger_fetch_worker = None
        
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
    
    def load_last_sync_date(self) -> str:
        """
        Lädt das Datum des letzten erfolgreichen Abgleichs aus der Datei.
        
        Returns:
            str: Formatierter Datum-String (dd.mm.yyyy, HH:MM) oder "Nie" wenn kein Datum vorhanden
        """
        try:
            sync_stats_file = Path("sync_stats.json")
            if sync_stats_file.exists():
                with open(sync_stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                    last_sync = stats.get("last_sync_date")
                    if last_sync:
                        # Konvertiere ISO-Format zu deutschem Format
                        try:
                            dt = datetime.fromisoformat(last_sync)
                            return dt.strftime("%d.%m.%Y, %H:%M")
                        except (ValueError, TypeError):
                            # Falls bereits im richtigen Format, verwende es direkt
                            return last_sync
            return "Nie"
        except Exception as e:
            logger.warning(f"Fehler beim Laden des letzten Sync-Datums: {e}")
            return "Nie"
    
    def save_last_sync_date(self, sync_date: str = None):
        """
        Speichert das Datum des letzten erfolgreichen Abgleichs in einer Datei.
        
        Args:
            sync_date: Optionales Datum (wenn None, wird aktuelles Datum verwendet)
        """
        try:
            sync_stats_file = Path("sync_stats.json")
            
            # Verwende aktuelles Datum wenn keines übergeben wurde
            if sync_date is None:
                sync_date = datetime.now().isoformat()
            elif isinstance(sync_date, datetime):
                sync_date = sync_date.isoformat()
            
            # Lade bestehende Stats oder erstelle neue
            stats = {}
            if sync_stats_file.exists():
                try:
                    with open(sync_stats_file, 'r', encoding='utf-8') as f:
                        stats = json.load(f)
                except json.JSONDecodeError:
                    stats = {}
            
            # Aktualisiere letztes Sync-Datum
            stats["last_sync_date"] = sync_date
            stats["last_sync_timestamp"] = datetime.now().isoformat()
            
            # Speichere Stats
            with open(sync_stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Letztes Sync-Datum gespeichert: {sync_date}")
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern des letzten Sync-Datums: {e}", exc_info=True)
    
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
        
        # Setze gleiche Höhe für alle Zeilen
        cards_grid.setRowStretch(0, 1)
        cards_grid.setRowStretch(1, 1)
        # Setze gleiche Breite für alle Spalten
        cards_grid.setColumnStretch(0, 1)
        cards_grid.setColumnStretch(1, 1)
        
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
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
        """)
        action_button.clicked.connect(self.start_oss_sync)
        action_button.setEnabled(False)  # Standardmäßig deaktiviert
        self.oss_button = action_button  # Referenz speichern
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
        debug_print("INFO: Starte Lizenzprüfung beim Start...")
        
        # Zeige Lizenz-GUI-Fenster (blockierend)
        license_window = LicenseGUIWindow(self)
        result = license_window.exec()
        
        if result == QDialog.Accepted:
            # Lizenzprüfung erfolgreich - App freigeben
            self.license_valid = True
            self.setEnabled(True)
            
            # Extrahiere valid_to aus LicenseGUIWindow
            if hasattr(license_window, 'valid_to_date') and license_window.valid_to_date:
                # Konvertiere valid_to zu deutschem Format
                try:
                    from datetime import datetime
                    # Versuche verschiedene Datumsformate zu parsen
                    valid_to_str = license_window.valid_to_date
                    # Versuche ISO-Format oder andere Formate
                    try:
                        dt = datetime.fromisoformat(valid_to_str.replace('Z', '+00:00'))
                    except:
                        # Versuche anderes Format
                        try:
                            dt = datetime.strptime(valid_to_str, "%Y-%m-%d")
                        except:
                            # Verwende direkt wenn kein Parsing möglich
                            self.license_expiry = valid_to_str
                            dt = None
                    
                    if dt:
                        # Formatiere als MM/YYYY
                        self.license_expiry = dt.strftime("%m/%Y")
                    logger.info(f"License expiry gesetzt: {self.license_expiry}")
                except Exception as e:
                    logger.warning(f"Fehler beim Parsen von valid_to: {e}, verwende Original: {license_window.valid_to_date}")
                    self.license_expiry = license_window.valid_to_date
            else:
                logger.warning("Kein valid_to vom License-Check erhalten")
            
            self.update_license_status(True)
            debug_print("OK: Lizenzprüfung erfolgreich - App freigegeben")
            
            # Starte automatischen Trigger-Update (sofort nach Lizenzprüfung)
            QTimer.singleShot(500, self.start_trigger_update)
            
            # Starte DB-Verbindungstest
            QTimer.singleShot(1000, self.check_database_connection)
            
            # Lade Statistiken
            QTimer.singleShot(2000, self.load_database_stats)
        else:
            # Lizenzprüfung fehlgeschlagen - App beenden
            debug_print("FEHLER: Lizenzprüfung fehlgeschlagen - App wird beendet")
            QMessageBox.critical(
                self,
                "Lizenzfehler",
                "Die Lizenzprüfung war nicht erfolgreich.\n\nDie Anwendung wird jetzt beendet."
            )
            self.close()
    
    def check_database_connection(self):
        """Prüft DB-Verbindung und aktualisiert Status"""
        # Aktualisiere auch OSS-Button Status nach DB-Verbindungsprüfung
        QTimer.singleShot(100, self.update_oss_button_status)
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
                    debug_print("OK: DB-Verbindung erfolgreich")
                    debug_info(f"DB-Verbindung erfolgreich:\n{message}", self)
                else:
                    self.db_connected = False
                    self.update_db_status(False)
                    debug_print(f"FEHLER: DB-Verbindung fehlgeschlagen: {message}")
            else:
                self.db_connected = False
                self.update_db_status(False)
                debug_print("WARNUNG: Keine DB-Credentials konfiguriert")
                
        except Exception as e:
            debug_print(f"FEHLER beim DB-Verbindungstest: {e}")
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
            debug_print(f"Fehler beim Laden der Statistiken: {e}")
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
            # Nach erfolgreichem Dialog: Prüfe Lizenz erneut um valid_to zu erhalten
            from ..services.license_service import LicenseService
            license_service = LicenseService()
            success, response_data, message = license_service.check_license_via_endpoint()
            
            if success and isinstance(response_data, dict):
                # Extrahiere valid_to aus response_data
                valid_to = response_data.get('valid_to') or response_data.get('validTo') or response_data.get('valid_to_date')
                if valid_to:
                    try:
                        from datetime import datetime
                        valid_to_str = str(valid_to)
                        try:
                            dt = datetime.fromisoformat(valid_to_str.replace('Z', '+00:00'))
                        except:
                            try:
                                dt = datetime.strptime(valid_to_str, "%Y-%m-%d")
                            except:
                                self.license_expiry = valid_to_str
                                dt = None
                        
                        if dt:
                            self.license_expiry = dt.strftime("%m/%Y")
                        logger.info(f"License expiry aktualisiert: {self.license_expiry}")
                    except Exception as e:
                        logger.warning(f"Fehler beim Parsen von valid_to: {e}")
            
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
            # Prüfe OSS-Button Status nach DB-Änderung
            QTimer.singleShot(1500, self.update_oss_button_status)
    
    def update_oss_button_status(self):
        """
        Aktualisiert den Status des OSS-Buttons.
        Button wird NUR aktiviert, wenn:
        1. Beide Verbindungen (Datenbank + Endpoint) funktionieren
        2. Trigger erfolgreich erstellt wurde
        """
        if not self.oss_button:
            return
        
        # Prüfe ob Trigger erfolgreich erstellt wurde
        if not self.trigger_successfully_created:
            logger.debug("OSS-Button deaktiviert: Trigger noch nicht erfolgreich erstellt")
            self.oss_button.setEnabled(False)
            return
        
        # Prüfe Datenbank-Verbindung
        try:
            from ..services.database_service import DatabaseService
            db_service = DatabaseService()
            
            if not db_service.has_saved_credentials():
                logger.debug("OSS-Button deaktiviert: Keine DB-Credentials")
                self.oss_button.setEnabled(False)
                return
            
            db_success, db_message = db_service.test_connection()
            if not db_success:
                logger.debug(f"OSS-Button deaktiviert: DB-Verbindung fehlgeschlagen: {db_message}")
                self.oss_button.setEnabled(False)
                return
        except Exception as e:
            logger.error(f"Fehler beim Prüfen der DB-Verbindung: {e}")
            self.oss_button.setEnabled(False)
            return
        
        # Prüfe Endpoint-Verbindung
        try:
            import requests
            headers = self.trigger_endpoint_service._get_license_headers()
            test_response = requests.get(
                self.trigger_endpoint_service.url, 
                headers=headers, 
                timeout=10
            )
            if test_response.status_code != 200:
                logger.debug(f"OSS-Button deaktiviert: Endpoint-Verbindung fehlgeschlagen (HTTP {test_response.status_code})")
                self.oss_button.setEnabled(False)
                return
        except requests.exceptions.Timeout:
            logger.debug("OSS-Button deaktiviert: Endpoint-Verbindung Timeout")
            self.oss_button.setEnabled(False)
            return
        except requests.exceptions.RequestException as e:
            logger.debug(f"OSS-Button deaktiviert: Endpoint-Verbindung fehlgeschlagen: {e}")
            self.oss_button.setEnabled(False)
            return
        except Exception as e:
            logger.error(f"Fehler beim Prüfen der Endpoint-Verbindung: {e}")
            self.oss_button.setEnabled(False)
            return
        
        # BEIDE Verbindungen funktionieren UND Trigger wurde erfolgreich erstellt
        logger.info("✅ OSS-Button aktiviert: Beide Verbindungen funktionieren und Trigger wurde erfolgreich erstellt")
        self.oss_button.setEnabled(True)
    
    
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
        
        # Prüfe ob Button aktiviert ist (sollte nur aktiviert sein wenn beide Verbindungen funktionieren)
        if not self.oss_button or not self.oss_button.isEnabled():
            QMessageBox.warning(
                self,
                "OSS-Abgleich nicht möglich",
                "Der OSS-Abgleich kann nicht gestartet werden.\n\n"
                "Bitte stellen Sie sicher, dass:\n"
                "• Beide Verbindungen (Datenbank + Endpoint) funktionieren\n"
                "• Der Trigger erfolgreich erstellt wurde"
            )
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
        """Startet den OSS Start Worker (verwendet OSSStart-Klasse)"""
        # Erstelle Worker
        self.sync_worker = OSSStartWorker()
        
        # Erstelle Progress-Dialog
        self.progress_dialog = QProgressDialog("OSS-Abgleich wird durchgeführt...", "Abbrechen", 0, 5, self)
        self.progress_dialog.setWindowTitle("OSS-Abgleich")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setCancelButton(None)  # Deaktiviere Abbrechen-Button
        
        # Verbinde Signale
        self.sync_worker.progress.connect(self.on_sync_progress)
        self.sync_worker.finished.connect(self.on_sync_finished)
        self.sync_worker.decrypted_sql_ready.connect(self.on_decrypted_sql_ready)
        
        # Starte Worker
        self.sync_worker.start()
        self.progress_dialog.show()
        
        debug_print("INFO: OSS Start Worker gestartet")
    
    def on_sync_progress(self, message, step=None, total=None):
        """Behandelt Progress-Updates vom Worker"""
        debug_print(f"Progress: {message} ({step}/{total if total else '?'})")
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setLabelText(message)
            if step is not None and total is not None:
                self.progress_dialog.setMaximum(total)
                self.progress_dialog.setValue(step)
    
    def on_sync_finished(self, success, message, results):
        """Behandelt das Ende der Synchronisation"""
        # Schließe Progress-Dialog
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # Aktualisiere letzten Abgleich nur bei Erfolg
        if success:
            from datetime import datetime
            sync_datetime = datetime.now()
            self.last_sync_date = sync_datetime.strftime("%d.%m.%Y, %H:%M")
            
            # Speichere Datum persistent
            self.save_last_sync_date(sync_datetime)
            
            # Aktualisiere Footer
            if hasattr(self, 'footer_label') and self.footer_label:
                self.footer_label.setText(f"Version {self.app_version} • Letzter Abgleich: {self.last_sync_date}")
        
        # Zeige Ergebnis-Dialog
        if success:
            product_count = results.get("product_count", 0) if isinstance(results, dict) else 0
            # Zeige Erfolgsmeldung nur im Debug-Modus
            debug_info(
                f"OSS-Abgleich erfolgreich\n\n✅ {message}",
                self
            )
            
            # Aktualisiere Statistiken nach Sync
            QTimer.singleShot(500, self.load_database_stats)
        else:
            # Fehler-Dialog nur im Debug-Modus anzeigen
            from app.core.debug_manager import is_debug_enabled
            
            if is_debug_enabled():
                # Fehler-Dialog mit Möglichkeit SQL anzuzeigen
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("❌ OSS-Abgleich fehlgeschlagen")
                msg_box.setText(f"❌ {message}")
                msg_box.setIcon(QMessageBox.Critical)
                
                # Prüfe ob SQL-Statement vorhanden ist (bei SQL-Fehlern)
                sql_statement = None
                if isinstance(results, dict):
                    # Debug: Logge alle verfügbaren Keys
                    logger.debug(f"Results Keys: {list(results.keys())}")
                    logger.debug(f"sql_statement: {results.get('sql_statement')}")
                    logger.debug(f"decrypted_sql: {results.get('decrypted_sql')}")
                    
                    sql_statement = results.get("sql_statement") or results.get("decrypted_sql")
                
                if sql_statement and sql_statement.strip():
                    logger.info(f"SQL-Statement gefunden ({len(sql_statement)} Zeichen), zeige Dialog (Debug-Modus)")
                    msg_box.setInformativeText("Möchten Sie das SQL-Statement anzeigen?\n\nDas SQL kann kopiert und in SSMS getestet werden.")
                    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    msg_box.setDefaultButton(QMessageBox.Yes)  # Default auf Yes, damit es einfacher ist
                    
                    result = msg_box.exec()
                    
                    if result == QMessageBox.Yes:
                        # Zeige SQL-Daten im DecryptDialog
                        logger.info("Benutzer möchte SQL anzeigen")
                        decrypt_dialog = DecryptDialog(self)
                        decrypt_dialog.result_output.setPlainText(sql_statement)
                        decrypt_dialog.result_output.setReadOnly(True)  # Read-only für Anzeige
                        
                        # Setze Dialog-Titel für bessere Erkennbarkeit
                        decrypt_dialog.setWindowTitle("SQL-Statement (Tax Rates) - Zum Testen in SSMS kopieren")
                        
                        decrypt_dialog.exec()  # Zeige Dialog
                else:
                    # Keine SQL-Daten vorhanden
                    logger.debug(f"Kein SQL-Statement gefunden. sql_statement={sql_statement}")
                    if isinstance(results, dict):
                        logger.debug(f"Verfügbare Keys im results: {list(results.keys())}")
                    msg_box.setStandardButtons(QMessageBox.Ok)
                    msg_box.exec()
            else:
                # Im normalen Modus: Nur loggen, keine Dialoge anzeigen
                logger.info(f"OSS-Abgleich fehlgeschlagen: {message}")
                if isinstance(results, dict):
                    sql_statement = results.get("sql_statement") or results.get("decrypted_sql")
                    if sql_statement and sql_statement.strip():
                        logger.info(f"SQL-Statement vorhanden, aber Debug-Modus deaktiviert - keine Anzeige")
        
        # Cleanup Worker
        if self.sync_worker:
            self.sync_worker.deleteLater()
            self.sync_worker = None
        
        debug_print(f"OSS-Abgleich beendet: success={success}, message={message}")
    
    def on_decrypted_sql_ready(self, decrypted_sql: str):
        """Wird aufgerufen wenn SQL erfolgreich entschlüsselt wurde"""
        logger.info(f"Entschlüsseltes SQL erhalten ({len(decrypted_sql)} Zeichen)")
        
        # Zeige Dialog mit entschlüsseltem SQL nur im Debug-Modus
        from app.core.debug_manager import is_debug_enabled
        
        if is_debug_enabled():
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("✅ SQL erfolgreich entschlüsselt")
            msg_box.setText("Das SQL-Statement wurde erfolgreich entschlüsselt.\n\nMöchten Sie das SQL-Statement anzeigen?")
            msg_box.setInformativeText("Das SQL kann kopiert und in SSMS getestet werden, bevor es ausgeführt wird.")
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.Yes)
            
            result = msg_box.exec()
            
            if result == QMessageBox.Yes:
                # Zeige SQL-Daten im DecryptDialog
                logger.info("Benutzer möchte SQL anzeigen")
                decrypt_dialog = DecryptDialog(self)
                decrypt_dialog.result_output.setPlainText(decrypted_sql)
                decrypt_dialog.result_output.setReadOnly(True)  # Read-only für Anzeige
                
                # Setze Dialog-Titel für bessere Erkennbarkeit
                decrypt_dialog.setWindowTitle("SQL-Statement (Tax Rates) - Zum Testen in SSMS kopieren")
                
                decrypt_dialog.exec()  # Zeige Dialog
        else:
            # Im normalen Modus: SQL-Daten NICHT anzeigen
            logger.info("SQL entschlüsselt, aber Debug-Modus deaktiviert - keine Anzeige")
    
    def start_trigger_update(self):
        """Startet automatischen Trigger-Update beim Programmstart"""
        logger.info("Starte automatischen Trigger-Update...")
        
        # Prüfe ob Worker bereits läuft
        if self.trigger_fetch_worker and self.trigger_fetch_worker.isRunning():
            logger.warning("Trigger-Update läuft bereits")
            return
        
        # Erstelle neuen Worker (Service wird automatisch erstellt wenn None)
        self.trigger_fetch_worker = TriggerFetchWorker(
            trigger_endpoint_service=self.trigger_endpoint_service,
            password=None  # Verwendet Standard-Passwort "geh31m"
        )
        self.trigger_fetch_worker.finished.connect(self.on_trigger_update_finished)
        self.trigger_fetch_worker.start()
        
        logger.info("Trigger-Update Worker gestartet")
    
    def on_trigger_update_finished(self, success: bool, message: str, decrypted_sql: str = ""):
        """Wird aufgerufen wenn Trigger-Update abgeschlossen ist"""
        logger.info(f"Trigger-Update abgeschlossen: success={success}")
        
        # Aktualisiere Trigger-Status
        self.trigger_successfully_created = success
        
        # Aktualisiere OSS-Button Status basierend auf Ergebnis
        if success:
            # Trigger erfolgreich erstellt - prüfe beide Verbindungen und aktiviere Button
            logger.info("Trigger erfolgreich erstellt - prüfe Verbindungen für OSS-Button...")
            QTimer.singleShot(500, self.update_oss_button_status)
        else:
            # Fehler beim Trigger-Update - deaktiviere Button
            logger.warning("Trigger-Update fehlgeschlagen - OSS-Button wird deaktiviert")
            if self.oss_button:
                self.oss_button.setEnabled(False)
        
        if success:
            # Erfolgsfenster anzeigen nur im Debug-Modus
            from app.core.debug_manager import is_debug_enabled
            
            if is_debug_enabled():
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("✅ Trigger-Update erfolgreich")
                msg_box.setText(message)
                msg_box.setIcon(QMessageBox.Information)
                
                # Zeige entschlüsselte SQL-Daten wenn vorhanden
                if decrypted_sql and decrypted_sql.strip():
                    msg_box.setInformativeText("Möchten Sie die ausgeführten SQL-Daten anzeigen?")
                    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    msg_box.setDefaultButton(QMessageBox.No)
                    
                    result = msg_box.exec()
                    
                    if result == QMessageBox.Yes:
                        # Zeige SQL-Daten im DecryptDialog
                        decrypt_dialog = DecryptDialog(self)
                        # Setze entschlüsselte Daten in das Ergebnis-Feld
                        decrypt_dialog.result_output.setPlainText(decrypted_sql)
                        decrypt_dialog.result_output.setReadOnly(True)  # Read-only für Anzeige
                        decrypt_dialog.exec()  # Zeige Dialog
                else:
                    # Keine SQL-Daten vorhanden, zeige nur Erfolgsmeldung
                    msg_box.setStandardButtons(QMessageBox.Ok)
                    msg_box.exec()
            else:
                # Im normalen Modus: Keine SQL-Daten anzeigen
                if decrypted_sql and decrypted_sql.strip():
                    logger.info("SQL-Daten vorhanden, aber Debug-Modus deaktiviert - keine Anzeige")
        else:
            # Fehlerfenster anzeigen (nur bei kritischen Fehlern)
            # Bei Netzwerkfehlern oder fehlenden Credentials nicht so kritisch
            msg_box = QMessageBox(self)
            
            if "Netzwerkfehler" in message or "Timeout" in message or "Credentials" in message:
                # Zeige Warnung statt Fehler
                msg_box.setWindowTitle("⚠️ Trigger-Update nicht möglich")
                msg_box.setText(f"{message}\n\nDie App funktioniert weiterhin normal.\nSie können den Trigger manuell über 'Entschlüsselung' aktualisieren.")
                msg_box.setIcon(QMessageBox.Warning)
            else:
                # Kritischer Fehler
                msg_box.setWindowTitle("❌ Trigger-Update fehlgeschlagen")
                msg_box.setText(message)
                msg_box.setIcon(QMessageBox.Critical)
            
            # Zeige entschlüsselte SQL-Daten wenn vorhanden (auch bei Fehlern)
            if decrypted_sql and decrypted_sql.strip():
                msg_box.setInformativeText("Möchten Sie die entschlüsselten SQL-Daten anzeigen?")
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg_box.setDefaultButton(QMessageBox.No)
                
                result = msg_box.exec()
                
                if result == QMessageBox.Yes:
                    # Zeige SQL-Daten im DecryptDialog
                    decrypt_dialog = DecryptDialog(self)
                    decrypt_dialog.result_output.setPlainText(decrypted_sql)
                    decrypt_dialog.result_output.setReadOnly(True)  # Read-only für Anzeige
                    decrypt_dialog.exec()  # Zeige Dialog
            else:
                # Keine SQL-Daten vorhanden
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.exec()
        
        # Cleanup Worker
        if self.trigger_fetch_worker:
            self.trigger_fetch_worker.deleteLater()
            self.trigger_fetch_worker = None
