"""
App-Initialisierung für OSS goEcommerce
Hauptmodul für die Anwendung
"""

import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QPalette, QColor

from .ui.dashboard import DashboardWindow
from .config import get_color_scheme
from .core.debug_manager import get_debug_manager
from .core.error_handler import install_global_exception_handler, install_qt_exception_handler


def setup_application():
    """Richtet die Anwendung ein"""
    # Installiere globalen Exception Handler (MUSS vor QApplication sein)
    install_global_exception_handler()
    
    app = QApplication(sys.argv)
    
    # Installiere Qt-spezifischen Exception Handler
    install_qt_exception_handler(app)
    
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
    
    # Frage vor Programmstart, ob Debug aktiviert werden soll
    debug_manager = get_debug_manager()
    
    # Zeige Dialog für Debug-Aktivierung (nur wenn nicht bereits durch Umgebungsvariable gesetzt)
    import os
    debug_from_env = os.getenv('OSS_DEBUG', '').lower()
    if not debug_from_env in ('1', 'true', 'yes', 'on'):
        # Erstelle temporäres unsichtbares Fenster für den Dialog
        msg_box = QMessageBox()
        msg_box.setWindowTitle("🔍 Debug-Modus")
        msg_box.setText("Möchten Sie den Debug-Modus aktivieren?")
        msg_box.setInformativeText(
            "Bei aktiviertem Debug-Modus werden:\n"
            "• Debug-Informationen in der Console angezeigt\n"
            "• Debug-Info-Fenster eingeblendet"
        )
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        
        # Setze Farbschema für den Dialog
        palette = app.palette()
        msg_box.setPalette(palette)
        
        # Zeige Dialog
        result = msg_box.exec()
        
        if result == QMessageBox.Yes:
            debug_manager.enable()
        else:
            debug_manager.disable()
    else:
        # Debug wurde bereits durch Umgebungsvariable aktiviert
        debug_manager.enable()
    
    # Aktualisiere alle Logger basierend auf Debug-Status
    from app.core.logging_config import update_all_loggers_for_debug
    update_all_loggers_for_debug()
    
    window = DashboardWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
