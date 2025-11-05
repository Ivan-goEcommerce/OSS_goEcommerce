"""
UI-Komponenten für OSS goEcommerce
Wiederverwendbare UI-Elemente und Styling
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QTextEdit, QFrame, 
                               QProgressBar, QGroupBox, QTabWidget)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class StyledGroupBox(QGroupBox):
    """Gruppe mit einheitlichem Styling"""
    
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setStyleSheet("""
            QGroupBox {
                background-color: #2a2a2a;
                border: 2px solid #ff8c00;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: #ff8c00;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)


class StyledButton(QPushButton):
    """Button mit einheitlichem Styling"""
    
    def __init__(self, text="", parent=None, button_type="primary"):
        super().__init__(text, parent)
        
        if button_type == "primary":
            self.setStyleSheet("""
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
        elif button_type == "secondary":
            self.setStyleSheet("""
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


class StyledTextEdit(QTextEdit):
    """TextEdit mit einheitlichem Styling"""
    
    def __init__(self, placeholder_text="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder_text)
        self.setFont(QFont("Courier New", 10))
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                border: 2px solid #ff8c00;
                border-radius: 8px;
                padding: 10px;
                color: #ff8c00;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
            QTextEdit:focus {
                border-color: #ffaa00;
            }
        """)


class StyledLineEdit(QLineEdit):
    """LineEdit mit einheitlichem Styling"""
    
    def __init__(self, placeholder_text="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder_text)
        self.setStyleSheet("""
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


class StatusLabel(QLabel):
    """Status-Label mit einheitlichem Styling"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QLabel {
                color: #ff8c00;
                font-size: 12px;
                padding: 5px 10px;
                background-color: #1a1a1a;
                border-radius: 15px;
                border: 1px solid #ff8c00;
            }
        """)


class SearchResultsWidget(QWidget):
    """Widget für die Anzeige von Suchergebnissen"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Richtet die Benutzeroberfläche ein"""
        layout = QVBoxLayout(self)
        
        # Ergebnisse-Gruppe
        results_group = StyledGroupBox("Suchergebnisse")
        results_layout = QVBoxLayout(results_group)
        
        # Ergebnisse Text
        self.results_text = StyledTextEdit("Suchergebnisse werden hier angezeigt...")
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
    
    def set_results(self, results):
        """Setzt die Suchergebnisse"""
        print(f"DEBUG: set_results aufgerufen mit: {results}")
        print(f"DEBUG: results type: {type(results)}")
        
        if isinstance(results, list) and results:
            print(f"DEBUG: Erste Ergebnis-Struktur: {results[0]}")
            formatted_result = self.format_search_results(results)
            self.results_text.setPlainText(formatted_result)
        elif isinstance(results, dict):
            print(f"DEBUG: Einzelnes Ergebnis als Dictionary: {results}")
            formatted_result = self.format_search_results([results])
            self.results_text.setPlainText(formatted_result)
        else:
            print(f"DEBUG: Unerwartetes Format in set_results: {type(results)}")
            self.results_text.setPlainText(f"Unerwartetes Ergebnis-Format:\n{results}")
    
    def format_search_results(self, results):
        """Formatiert die Suchergebnisse für die Anzeige"""
        if not results:
            return "Keine Ergebnisse gefunden."
        
        formatted = "=== TARIC-SUCHE ERGEBNISSE ===\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"Ergebnis {i}:\n"
            
            # Verschiedene Feldnamen unterstützen
            taric_code = result.get('taric_code') or result.get('code') or result.get('taric_list', 'N/A')
            oss_id = result.get('oss_combination_id') or result.get('oss_id') or result.get('combination_id', 'N/A')
            
            formatted += f"TARIC-Code: {taric_code}\n"
            formatted += f"OSS-Kombination ID: {oss_id}\n"
            
            # Länder-Steuersätze (verschiedene Formate unterstützen)
            tax_rates = result.get('tax_rates') or result.get('country_tax_rates') or result.get('rates')
            if tax_rates:
                formatted += "Länder-Steuersätze:\n"
                for country, rate in tax_rates.items():
                    if rate is not None:
                        country_name = result.get('country_names', {}).get(country, country)
                        formatted += f"  {country_name}: {rate}%\n"
            
            # Zusätzliche Felder
            if result.get('description'):
                formatted += f"Beschreibung: {result['description']}\n"
            if result.get('date'):
                formatted += f"Datum: {result['date']}\n"
            if result.get('status'):
                formatted += f"Status: {result['status']}\n"
            
            # Fehler oder Demo-Info
            if result.get('error'):
                formatted += f"Fehler: {result['error']}\n"
            if result.get('demo_info'):
                formatted += f"Demo-Info: {result['demo_info']}\n"
            
            # Raw JSON für Debugging (falls gewünscht)
            if result.get('debug') or result.get('raw_data'):
                formatted += f"Raw Data: {result}\n"
            
            formatted += "\n" + "="*50 + "\n\n"
        
        return formatted
