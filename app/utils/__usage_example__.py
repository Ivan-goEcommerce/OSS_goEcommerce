"""
Beispiel für die Verwendung der CryptoUtils-Klasse in der App

Dieses Modul zeigt, wie Sie verschlüsselte SQL-Daten von der n8n API entschlüsseln können.
"""

from app.utils import CryptoUtils


def decrypt_sql_from_n8n_api(api_response: dict) -> str:
    """
    Beispiel-Funktion: Entschlüsselt SQL aus n8n API Response
    
    Args:
        api_response: Dictionary mit verschlüsselten Daten von der n8n API
            Format: {
                "iv": "base64-kodierter IV",
                "encrypted": "base64-kodierter verschlüsselter SQL"
            }
    
    Returns:
        str: Entschlüsselter SQL-String
    """
    try:
        # Entschlüssele die Daten
        decrypted_sql = CryptoUtils.decrypt_sql_from_api(api_response)
        
        if decrypted_sql:
            print(f"✅ SQL erfolgreich entschlüsselt")
            print(f"SQL: {decrypted_sql}")
            return decrypted_sql
        else:
            print("❌ Entschlüsselung fehlgeschlagen")
            return None
            
    except Exception as e:
        print(f"❌ Fehler beim Entschlüsseln: {e}")
        return None


def example_usage_with_requests():
    """
    Beispiel: Verwendung mit requests-Library für API-Calls
    """
    import requests
    
    # API-URL (Beispiel)
    api_url = "https://your-api.com/encrypted-sql"
    
    try:
        # Hole verschlüsselte SQL von API
        response = requests.post(api_url, json={"key": "value"})
        response_data = response.json()
        
        # Entschlüssele
        if "iv" in response_data and "encrypted" in response_data:
            decrypted_sql = CryptoUtils.decrypt_text(
                response_data["encrypted"],
                response_data["iv"],
                "geh31m"
            )
            
            if decrypted_sql:
                print(f"✅ Entschlüsselter SQL: {decrypted_sql}")
                return decrypted_sql
        
        return None
        
    except Exception as e:
        print(f"❌ Fehler beim API-Call: {e}")
        return None


def example_usage_in_monitoring_manager():
    """
    Beispiel: Verwendung im Monitoring Manager
    """
    from app.managers import MonitoringManager
    
    # Initialisiere Monitoring Manager
    # monitoring_manager = MonitoringManager(db_manager, n8n_manager)
    
    # Hole verschlüsselte SQL von API
    api_response = {
        "iv": "brfQ8uEjEuMC67+O7IzipA==",
        "encrypted": "IhrVerschlüsselterSQLString"
    }
    
    # Entschlüssele
    decrypted_sql = CryptoUtils.decrypt_sql_from_api(api_response)
    
    if decrypted_sql:
        # SQL ausführen
        # result = db_manager.execute_sql(decrypted_sql)
        pass


# Beispiel-Konfiguration
# Fügen Sie dies zu Ihren .env oder Config hinzu:
"""
# Verschlüsselungs-Einstellungen
DECRYPTION_KEY=geh31m
DECRYPTION_ENABLED=true

# API-Endpunkte für verschlüsselte SQL
SQL_ENCRYPTION_API=https://your-api.com/encrypted-sql
"""

