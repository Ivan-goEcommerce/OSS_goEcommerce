"""
Logging-Konfiguration für OSS goEcommerce
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from app.core.debug_manager import get_debug_manager


def get_logger(name: str) -> logging.Logger:
    """
    Erstellt einen konfigurierten Logger.
    Console-Ausgaben werden nur im Debug-Modus angezeigt.
    Logs werden immer in Dateien geschrieben.
    
    Args:
        name: Name des Loggers (normalerweise __name__)
        
    Returns:
        Konfigurierter Logger
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        # Logger wurde bereits konfiguriert - aktualisiere nur Console Handler
        # Prüfe ob Debug aktiviert ist und aktualisiere Console Handler entsprechend
        debug_manager = get_debug_manager()
        console_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                console_handler = handler
                break
        
        if console_handler:
            # Setze Level basierend auf Debug-Status
            if debug_manager.is_enabled():
                console_handler.setLevel(logging.INFO)
            else:
                # Deaktiviere Console-Ausgaben im normalen Modus
                console_handler.setLevel(logging.CRITICAL + 1)  # Höher als höchstes Level
        elif debug_manager.is_enabled():
            # Erstelle Console Handler nur wenn Debug aktiviert ist
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Formatter für Logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler - nur wenn Debug aktiviert ist
    debug_manager = get_debug_manager()
    if debug_manager.is_enabled():
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    else:
        # Im normalen Modus: Keine Console-Ausgaben
        # Erstelle Handler mit sehr hohem Level, damit nichts ausgegeben wird
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.CRITICAL + 1)  # Höher als höchstes Level
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File Handler - immer aktiv
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def update_all_loggers_for_debug():
    """
    Aktualisiert alle bestehenden Logger basierend auf dem aktuellen Debug-Status.
    Sollte aufgerufen werden, nachdem der Debug-Status gesetzt wurde.
    """
    debug_manager = get_debug_manager()
    
    # Aktualisiere alle Logger (inklusive Root-Logger)
    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        logger = logging.getLogger(logger_name)
        
        # Finde und aktualisiere Console Handler
        for handler in logger.handlers[:]:  # Kopie der Liste für sichere Iteration
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                if debug_manager.is_enabled():
                    handler.setLevel(logging.INFO)
                else:
                    # Deaktiviere Console-Ausgaben im normalen Modus
                    handler.setLevel(logging.CRITICAL + 1)  # Höher als höchstes Level

