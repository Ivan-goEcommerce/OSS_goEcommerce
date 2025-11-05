"""
Services-Module für OSS goEcommerce
Externe Service-Integrationen (Database, API, etc.)
"""

from .database_service import DatabaseService

# Backward compatibility aliases
JTLDatabaseManager = DatabaseService  # Alias for backward compatibility

__all__ = ['DatabaseService', 'JTLDatabaseManager']

