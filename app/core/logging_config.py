"""
Logging-Konfiguration für OSS goEcommerce
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def get_logger(name: str) -> logging.Logger:
    """
    Erstellt einen konfigurierten Logger.
    
    Args:
        name: Name des Loggers (normalerweise __name__)
        
    Returns:
        Konfigurierter Logger
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        # Logger wurde bereits konfiguriert
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Formatter für Logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

