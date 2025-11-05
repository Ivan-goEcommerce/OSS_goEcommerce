"""
Zentraler Debug-Manager für OSS goEcommerce
Steuert die Anzeige von Debug-Informationen (Console-Outputs und Info-Fenster)
"""

import sys
from typing import Optional
from PySide6.QtWidgets import QMessageBox, QWidget


class DebugManager:
    """
    Zentrale Klasse zur Verwaltung des Debug-Modus.
    
    Kontrolliert:
    - Console-Ausgaben (print, logging)
    - Info-Fenster (QMessageBox)
    """
    
    _instance: Optional['DebugManager'] = None
    
    def __new__(cls):
        """Singleton-Pattern: Stelle sicher, dass nur eine Instanz existiert"""
        if cls._instance is None:
            cls._instance = super(DebugManager, cls).__new__(cls)
            cls._instance._debug_enabled = False
        return cls._instance
    
    def __init__(self):
        """Initialisiert den Debug-Manager"""
        # Initialisierung erfolgt bereits in __new__
        pass
    
    def is_enabled(self) -> bool:
        """
        Prüft ob Debug-Modus aktiviert ist.
        
        Returns:
            True wenn Debug aktiviert ist, sonst False
        """
        return self._debug_enabled
    
    def enable(self):
        """Aktiviert den Debug-Modus"""
        self._debug_enabled = True
    
    def disable(self):
        """Deaktiviert den Debug-Modus"""
        self._debug_enabled = False
    
    def set_debug(self, enabled: bool):
        """
        Setzt den Debug-Modus.
        
        Args:
            enabled: True um Debug zu aktivieren, False um zu deaktivieren
        """
        self._debug_enabled = bool(enabled)
    
    def debug_print(self, *args, **kwargs):
        """
        Ersetzt print() - gibt nur aus wenn Debug aktiviert ist.
        
        Args:
            *args: Argumente die an print() weitergegeben werden
            **kwargs: Keyword-Argumente die an print() weitergegeben werden
        """
        if self._debug_enabled:
            print(*args, **kwargs)
    
    def debug_info(self, message: str, parent: Optional[QWidget] = None):
        """
        Zeigt Info-Fenster nur wenn Debug aktiviert ist.
        
        Args:
            message: Die anzuzeigende Nachricht
            parent: Optionales Parent-Widget für das Fenster
        """
        if self._debug_enabled:
            msg_box = QMessageBox(parent)
            msg_box.setWindowTitle("🔍 Debug Info")
            msg_box.setText(message)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
    
    def debug_warning(self, message: str, parent: Optional[QWidget] = None):
        """
        Zeigt Warnung nur wenn Debug aktiviert ist.
        
        Args:
            message: Die anzuzeigende Warnung
            parent: Optionales Parent-Widget für das Fenster
        """
        if self._debug_enabled:
            msg_box = QMessageBox(parent)
            msg_box.setWindowTitle("🔍 Debug Warning")
            msg_box.setText(message)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
    
    def debug_error(self, message: str, parent: Optional[QWidget] = None):
        """
        Zeigt Fehler nur wenn Debug aktiviert ist.
        
        Args:
            message: Die anzuzeigende Fehlermeldung
            parent: Optionales Parent-Widget für das Fenster
        """
        if self._debug_enabled:
            msg_box = QMessageBox(parent)
            msg_box.setWindowTitle("🔍 Debug Error")
            msg_box.setText(message)
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()


# Globale Instanz für einfachen Zugriff
_debug_manager = DebugManager()


def get_debug_manager() -> DebugManager:
    """
    Gibt die globale Debug-Manager-Instanz zurück.
    
    Returns:
        Die DebugManager-Instanz
    """
    return _debug_manager


def is_debug_enabled() -> bool:
    """
    Prüft ob Debug-Modus aktiviert ist.
    
    Returns:
        True wenn Debug aktiviert ist, sonst False
    """
    return _debug_manager.is_enabled()


def debug_print(*args, **kwargs):
    """
    Zentrale Debug-Print-Funktion.
    Gibt nur aus wenn Debug aktiviert ist.
    
    Args:
        *args: Argumente die an print() weitergegeben werden
        **kwargs: Keyword-Argumente die an print() weitergegeben werden
    """
    _debug_manager.debug_print(*args, **kwargs)


def debug_info(message: str, parent=None):
    """
    Zentrale Debug-Info-Funktion.
    Zeigt Info-Fenster nur wenn Debug aktiviert ist.
    
    Args:
        message: Die anzuzeigende Nachricht
        parent: Optionales Parent-Widget für das Fenster
    """
    _debug_manager.debug_info(message, parent)


def debug_warning(message: str, parent=None):
    """
    Zentrale Debug-Warning-Funktion.
    Zeigt Warnung nur wenn Debug aktiviert ist.
    
    Args:
        message: Die anzuzeigende Warnung
        parent: Optionales Parent-Widget für das Fenster
    """
    _debug_manager.debug_warning(message, parent)


def debug_error(message: str, parent=None):
    """
    Zentrale Debug-Error-Funktion.
    Zeigt Fehler nur wenn Debug aktiviert ist.
    
    Args:
        message: Die anzuzeigende Fehlermeldung
        parent: Optionales Parent-Widget für das Fenster
    """
    _debug_manager.debug_error(message, parent)

