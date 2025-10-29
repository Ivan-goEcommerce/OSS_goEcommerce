"""
App-Initialisierung für OSS goEcommerce
Hauptmodul für die Anwendung
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

from .ui.dashboard import DashboardWindow
from .config import get_color_scheme


def setup_application():
    """Richtet die Anwendung ein"""
    app = QApplication(sys.argv)
    
    # Setze das Orange-Schwarz Farbschema
    palette = QPalette()
    color_scheme = get_color_scheme()
    
    palette.setColor(QPalette.Window, QColor(color_scheme["window"]))
    palette.setColor(QPalette.WindowText, QColor(color_scheme["window_text"]))
    palette.setColor(QPalette.Base, QColor(color_scheme["base"]))
    palette.setColor(QPalette.AlternateBase, QColor(color_scheme["alternate_base"]))
    palette.setColor(QPalette.ToolTipBase, QColor(color_scheme["tooltip_base"]))
    palette.setColor(QPalette.ToolTipText, QColor(color_scheme["tooltip_text"]))
    palette.setColor(QPalette.Text, QColor(color_scheme["text"]))
    palette.setColor(QPalette.Button, QColor(color_scheme["button"]))
    palette.setColor(QPalette.ButtonText, QColor(color_scheme["button_text"]))
    palette.setColor(QPalette.BrightText, QColor(color_scheme["bright_text"]))
    palette.setColor(QPalette.Link, QColor(color_scheme["link"]))
    palette.setColor(QPalette.Highlight, QColor(color_scheme["highlight"]))
    palette.setColor(QPalette.HighlightedText, QColor(color_scheme["highlighted_text"]))
    
    app.setPalette(palette)
    
    return app


def main():
    """Hauptfunktion der Anwendung"""
    app = setup_application()
    
    window = DashboardWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
