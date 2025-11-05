"""
Decrypt Dialog für OSS goEcommerce
UI-Fenster für Entschlüsselung von n8n-Format Daten
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QTextEdit, QFormLayout, 
                               QMessageBox, QFrame, QComboBox, QCheckBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from app.services.decrypt_service import DecryptService
from app.services.database_service import DatabaseService
import json


class DecryptWorker(QThread):
    """Worker-Thread für Entschlüsselung"""
    finished = Signal(bool, str, str)  # success, result, error_message
    
    def __init__(self, decrypt_service, encrypted_data, iv=None, password=None, mode="text"):
        super().__init__()
        self.decrypt_service = decrypt_service
        self.encrypted_data = encrypted_data
        self.iv = iv
        self.password = password
        self.mode = mode  # "text" or "n8n_format"
    
    def run(self):
        """Führt die Entschlüsselung aus"""
        try:
            if self.mode == "text":
                # Einfache Text-Entschlüsselung
                if not self.encrypted_data or not self.iv:
                    self.finished.emit(False, "", "Verschlüsselte Daten und IV müssen eingegeben werden")
                    return
                
                result = self.decrypt_service.decrypt_text(
                    self.encrypted_data,
                    self.iv,
                    self.password
                )
                
                if result:
                    self.finished.emit(True, result, "")
                else:
                    self.finished.emit(False, "", "Entschlüsselung fehlgeschlagen - ungültige Daten oder falsches Passwort")
            
            elif self.mode == "n8n_format":
                # n8n-Format Entschlüsselung
                try:
                    items = json.loads(self.encrypted_data)
                    if not isinstance(items, list):
                        self.finished.emit(False, "", "Daten müssen eine JSON-Liste sein")
                        return
                    
                    result = self.decrypt_service.decrypt_from_n8n_format(
                        items,
                        self.password
                    )
                    self.finished.emit(True, result, "")
                except json.JSONDecodeError as e:
                    self.finished.emit(False, "", f"Ungültiges JSON-Format: {str(e)}")
                except Exception as e:
                    self.finished.emit(False, "", f"Fehler: {str(e)}")
            
        except Exception as e:
            self.finished.emit(False, "", f"Unerwarteter Fehler: {str(e)}")


class ExecuteSQLWorker(QThread):
    """Worker-Thread für SQL-Ausführung"""
    finished = Signal(bool, str, object)  # success, message, results
    
    def __init__(self, database_service, sql_query):
        super().__init__()
        self.database_service = database_service
        self.sql_query = sql_query
    
    def run(self):
        """Führt die SQL-Abfrage aus"""
        try:
            success, message, results = self.database_service.execute_query(self.sql_query)
            self.finished.emit(success, message, results)
        except Exception as e:
            self.finished.emit(False, f"Fehler: {str(e)}", None)


class DecryptDialog(QDialog):
    """Dialog für Entschlüsselung"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔓 OSS goEcommerce - Entschlüsselung")
        self.setMinimumSize(700, 600)
        self.setModal(True)
        
        self.decrypt_service = DecryptService()
        self.database_service = DatabaseService()
        self.decrypt_worker = None
        self.sql_worker = None
        self.last_decrypted_text = ""  # Speichert zuletzt entschlüsselten Text
        
        self.setup_ui()
    
    def setup_ui(self):
        """Richtet die Benutzeroberfläche ein"""
        layout = QVBoxLayout(self)
        
        # Titel
        title_label = QLabel("Daten entschlüsseln")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #ff8c00; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Modus-Auswahl
        mode_frame = QFrame()
        mode_layout = QVBoxLayout(mode_frame)
        
        mode_label = QLabel("Entschlüsselungs-Modus:")
        mode_label.setStyleSheet("color: #ff8c00; font-weight: bold;")
        mode_layout.addWidget(mode_label)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Text entschlüsseln (AES-256-CBC)", "n8n-Format entschlüsseln"])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        self.mode_combo.setStyleSheet("""
            QComboBox {
                background-color: #2a2a2a;
                color: #ff8c00;
                border: 2px solid #ff8c00;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        mode_layout.addWidget(self.mode_combo)
        
        layout.addWidget(mode_frame)
        
        # Formular
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        form_layout = QVBoxLayout(form_frame)
        
        # Passwort
        password_layout = QHBoxLayout()
        password_label = QLabel("Passwort (optional):")
        password_label.setStyleSheet("color: #ff8c00;")
        password_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Standard: geh31m")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: #ff8c00;
                border: 2px solid #ff8c00;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        password_layout.addWidget(self.password_input)
        form_layout.addLayout(password_layout)
        
        # IV (nur für Text-Modus)
        self.iv_frame = QFrame()
        self.iv_layout = QVBoxLayout(self.iv_frame)
        
        iv_label = QLabel("IV (Initialisierungsvektor) - Base64:")
        iv_label.setStyleSheet("color: #ff8c00;")
        self.iv_layout.addWidget(iv_label)
        
        self.iv_input = QLineEdit()
        self.iv_input.setPlaceholderText("Base64-kodierter IV...")
        self.iv_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: #ff8c00;
                border: 2px solid #ff8c00;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        self.iv_layout.addWidget(self.iv_input)
        form_layout.addWidget(self.iv_frame)
        
        # Eingabe
        data_label = QLabel("Verschlüsselte Daten:")
        data_label.setStyleSheet("color: #ff8c00; margin-top: 10px;")
        form_layout.addWidget(data_label)
        
        self.data_input = QTextEdit()
        self.data_input.setPlaceholderText("Hier verschlüsselte Daten eingeben (Base64 oder JSON)...")
        self.data_input.setMinimumHeight(150)
        self.data_input.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #ff8c00;
                border: 2px solid #ff8c00;
                border-radius: 8px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        form_layout.addWidget(self.data_input)
        
        layout.addWidget(form_frame)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.decrypt_button = QPushButton("🔓 Entschlüsseln")
        self.decrypt_button.clicked.connect(self.decrypt_data)
        self.decrypt_button.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #666666;
            }
        """)
        button_layout.addWidget(self.decrypt_button)
        
        # SQL ausführen Button
        self.execute_sql_button = QPushButton("⚙️ SQL ausführen")
        self.execute_sql_button.clicked.connect(self.execute_sql)
        self.execute_sql_button.setEnabled(False)  # Erst nach erfolgreicher Entschlüsselung aktivieren
        self.execute_sql_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #ff8c00;
                border: 2px solid #ff8c00;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff8c00;
                color: #000000;
            }
            QPushButton:disabled {
                background-color: #1a1a1a;
                color: #666666;
                border-color: #666666;
            }
        """)
        button_layout.addWidget(self.execute_sql_button)
        
        clear_button = QPushButton("🗑️ Leeren")
        clear_button.clicked.connect(self.clear_inputs)
        clear_button.setStyleSheet("""
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
        button_layout.addWidget(clear_button)
        
        close_button = QPushButton("❌ Schließen")
        close_button.clicked.connect(self.reject)
        close_button.setStyleSheet("""
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
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        # Ergebnis
        result_frame = QFrame()
        result_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        result_layout = QVBoxLayout(result_frame)
        
        result_title = QLabel("Entschlüsseltes Ergebnis:")
        result_title.setStyleSheet("color: #ff8c00; font-weight: bold;")
        result_layout.addWidget(result_title)
        
        self.result_output = QTextEdit()
        self.result_output.setPlaceholderText("Entschlüsselte Daten werden hier angezeigt...")
        self.result_output.setMinimumHeight(150)
        self.result_output.setReadOnly(True)
        self.result_output.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                border: 2px solid #ff8c00;
                border-radius: 8px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        result_layout.addWidget(self.result_output)
        
        layout.addWidget(result_frame)
        
        # Initialisiere UI für aktuellen Modus
        self.on_mode_changed()
    
    def on_mode_changed(self):
        """Wird aufgerufen wenn Modus geändert wird"""
        mode = self.mode_combo.currentIndex()
        
        if mode == 0:  # Text-Modus
            self.iv_frame.setVisible(True)
            self.data_input.setPlaceholderText("Verschlüsselte Daten (Base64) eingeben...")
        else:  # n8n-Format
            self.iv_frame.setVisible(False)
            self.data_input.setPlaceholderText("JSON-Array mit n8n-Items eingeben (z.B. von n8n API)...")
    
    def decrypt_data(self):
        """Führt die Entschlüsselung aus"""
        # Deaktiviere Button während Entschlüsselung
        self.decrypt_button.setEnabled(False)
        self.decrypt_button.setText("🔄 Entschlüssele...")
        self.result_output.clear()
        self.result_output.setPlaceholderText("Entschlüsselung läuft...")
        
        # Hole Eingabedaten
        encrypted_data = self.data_input.toPlainText().strip()
        password = self.password_input.text().strip() or None
        mode = self.mode_combo.currentIndex()
        
        iv = None
        if mode == 0:  # Text-Modus
            iv = self.iv_input.text().strip()
            if not encrypted_data or not iv:
                QMessageBox.warning(self, "Fehler", "Bitte geben Sie verschlüsselte Daten und IV ein!")
                self.decrypt_button.setEnabled(True)
                self.decrypt_button.setText("🔓 Entschlüsseln")
                return
        else:  # n8n-Format
            if not encrypted_data:
                QMessageBox.warning(self, "Fehler", "Bitte geben Sie JSON-Daten ein!")
                self.decrypt_button.setEnabled(True)
                self.decrypt_button.setText("🔓 Entschlüsseln")
                return
        
        # Starte Worker-Thread
        self.decrypt_worker = DecryptWorker(
            self.decrypt_service,
            encrypted_data,
            iv=iv if mode == 0 else None,
            password=password,
            mode="text" if mode == 0 else "n8n_format"
        )
        self.decrypt_worker.finished.connect(self.on_decrypt_finished)
        self.decrypt_worker.start()
    
    def on_decrypt_finished(self, success, result, error_message):
        """Wird aufgerufen wenn Entschlüsselung abgeschlossen ist"""
        self.decrypt_button.setEnabled(True)
        self.decrypt_button.setText("🔓 Entschlüsseln")
        
        if success:
            self.last_decrypted_text = result  # Speichere entschlüsselten Text für SQL-Ausführung
            self.result_output.setPlainText(result)
            self.result_output.setStyleSheet("""
                QTextEdit {
                    background-color: #1a1a1a;
                    color: #00ff00;
                    border: 2px solid #00ff00;
                    border-radius: 8px;
                    padding: 8px;
                    font-family: 'Courier New', monospace;
                    font-size: 11px;
                }
            """)
            # Aktiviere SQL-Button wenn Text erfolgreich entschlüsselt wurde
            self.execute_sql_button.setEnabled(True)
        else:
            self.last_decrypted_text = ""  # Keine Daten zum Ausführen
            self.result_output.setPlainText(f"❌ Fehler: {error_message}")
            self.result_output.setStyleSheet("""
                QTextEdit {
                    background-color: #1a1a1a;
                    color: #ff4444;
                    border: 2px solid #ff4444;
                    border-radius: 8px;
                    padding: 8px;
                    font-family: 'Courier New', monospace;
                    font-size: 11px;
                }
            """)
            # Deaktiviere SQL-Button bei Fehler
            self.execute_sql_button.setEnabled(False)
    
    def execute_sql(self):
        """Führt entschlüsselten SQL-Befehl aus"""
        if not self.last_decrypted_text:
            QMessageBox.warning(self, "Keine Daten", "Keine entschlüsselten Daten vorhanden zum Ausführen!")
            return
        
        # Bereite SQL-Query für Ausführung vor
        sql_query = self._prepare_sql_for_execution(self.last_decrypted_text)
        
        if not sql_query:
            QMessageBox.warning(self, "Keine Daten", "Entschlüsselte Daten sind leer oder konnten nicht als SQL formatiert werden!")
            return
        
        # Zeige Bestätigungsdialog
        reply = QMessageBox.question(
            self,
            "SQL ausführen?",
            f"Wollen Sie folgenden SQL-Befehl ausführen?\n\n{sql_query[:200]}{'...' if len(sql_query) > 200 else ''}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Prüfe DB-Verbindung
        if not self.database_service.has_saved_credentials():
            QMessageBox.warning(
                self,
                "Keine DB-Verbindung",
                "Keine Datenbank-Credentials gefunden.\n\nBitte konfigurieren Sie zuerst die DB-Verbindung über 'DB Credentials'."
            )
            return
        
        # Teste Verbindung
        success, message = self.database_service.test_connection()
        if not success:
            # Spezielle Meldung für Authentifizierungsfehler
            if "18456" in message or "Authentifizierungsfehler" in message:
                QMessageBox.warning(
                    self,
                    "Authentifizierungsfehler",
                    f"❌ SQL Server Authentifizierung fehlgeschlagen (Fehler 18456):\n\n{message}\n\n"
                    "Mögliche Lösungen:\n"
                    "1. Öffnen Sie 'DB Credentials' im Dashboard\n"
                    "2. Geben Sie das korrekte Passwort ein\n"
                    "3. Stellen Sie sicher, dass der Benutzername 'sa' korrekt ist\n"
                    "4. Prüfen Sie, ob SQL Server Authentifizierung aktiviert ist"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Verbindungsfehler",
                    f"Kann nicht zur Datenbank verbinden:\n\n{message}\n\nBitte prüfen Sie die DB-Einstellungen."
                )
            return
        
        # Deaktiviere Button während Ausführung
        self.execute_sql_button.setEnabled(False)
        self.execute_sql_button.setText("🔄 Führe SQL aus...")
        
        # Starte Worker-Thread
        self.sql_worker = ExecuteSQLWorker(self.database_service, sql_query)
        self.sql_worker.finished.connect(self.on_sql_finished)
        self.sql_worker.start()
    
    def on_sql_finished(self, success, message, results):
        """Wird aufgerufen wenn SQL-Ausführung abgeschlossen ist"""
        self.execute_sql_button.setEnabled(True)
        self.execute_sql_button.setText("⚙️ SQL ausführen")
        
        if success:
            # Zeige Erfolgsmeldung mit Details
            if results is None:
                # INSERT/UPDATE/DELETE - rowcount wurde zurückgegeben
                result_text = f"✅ SQL erfolgreich ausgeführt!\n\n{message}"
            elif isinstance(results, list):
                # SELECT - Ergebnisse zurückgegeben
                result_count = len(results)
                result_text = f"✅ SQL erfolgreich ausgeführt!\n\n{message}\n\nGefundene Zeilen: {result_count}"
                
                # Zeige erste 10 Ergebnisse als Vorschau
                if result_count > 0:
                    preview_lines = []
                    for i, row in enumerate(results[:10]):
                        if hasattr(row, '__iter__'):
                            preview_lines.append(f"Zeile {i+1}: {str(row)}")
                        else:
                            preview_lines.append(f"Zeile {i+1}: {row}")
                    
                    if result_count > 10:
                        preview_lines.append(f"... und {result_count - 10} weitere Zeilen")
                    
                    result_text += "\n\nVorschau:\n" + "\n".join(preview_lines)
            else:
                # Andere Art von Ergebnis
                result_text = f"✅ SQL erfolgreich ausgeführt!\n\n{message}\n\nErgebnis: {results}"
            
            QMessageBox.information(self, "SQL erfolgreich", result_text)
        else:
            # Spezielle Meldung für Authentifizierungsfehler
            if "18456" in message or "Authentifizierungsfehler" in message:
                QMessageBox.critical(
                    self,
                    "Authentifizierungsfehler",
                    f"❌ SQL Server Authentifizierung fehlgeschlagen (Fehler 18456):\n\n{message}\n\n"
                    "Bitte prüfen Sie die DB-Credentials über 'DB Credentials' im Dashboard."
                )
            else:
                QMessageBox.critical(
                    self,
                    "SQL-Fehler",
                    f"❌ SQL-Ausführung fehlgeschlagen:\n\n{message}"
                )
    
    def _prepare_sql_for_execution(self, decrypted_text: str) -> str:
        """
        Bereitet entschlüsselte Daten für SQL-Ausführung vor.
        Verwendet die format_sql_for_execution Methode aus DecryptService.
        
        Args:
            decrypted_text: Roher entschlüsselter Text (sollte bereits SQL sein)
            
        Returns:
            Bereinigter SQL-Query-String, bereit für Ausführung
        """
        # Verwende die format_sql_for_execution Methode aus DecryptService
        # und korrigiere dann die Trigger-Struktur
        formatted_sql = self.decrypt_service.format_sql_for_execution(decrypted_text)
        corrected_sql = self.decrypt_service.fix_trigger_structure(formatted_sql)
        return corrected_sql
    
    def clear_inputs(self):
        """Löscht alle Eingaben"""
        self.data_input.clear()
        self.iv_input.clear()
        self.password_input.clear()
        self.result_output.clear()
        self.last_decrypted_text = ""  # Zurücksetzen
        self.execute_sql_button.setEnabled(False)  # Deaktiviere SQL-Button
        self.result_output.setPlaceholderText("Entschlüsselte Daten werden hier angezeigt...")
        self.result_output.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                border: 2px solid #ff8c00;
                border-radius: 8px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """)

