#!/usr/bin/env python3
"""
Synchronisiert JTL-Produktdaten mit n8n Webhook
Führt SQL-Abfrage aus und sendet Ergebnisse an n8n
"""

import sys
import json
import os
from pathlib import Path

# Füge app-Verzeichnis zum Python-Pfad hinzu für Imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from jtl_database_manager import JTLDatabaseManager
from n8n_workflow_manager import N8nWorkflowManager

# Import LicenseService für Keyring-Zugriff
try:
    from app.services.license_service import LicenseService
    LICENSE_SERVICE_AVAILABLE = True
except ImportError:
    LICENSE_SERVICE_AVAILABLE = False
    print("WARNUNG: LicenseService nicht verfügbar - verwende Standard-Werte")


def sync_products_to_n8n(
    n8n_webhook_url: str = "https://agentic.go-ecommerce.de/webhook/post_customer_product",
    license_number: str = None,
    email: str = None
):
    """
    Synchronisiert Produktdaten von JTL-Datenbank zu n8n Webhook
    
    Args:
        n8n_webhook_url: URL des n8n Webhooks
        license_number: Lizenznummer für n8n (optional, wird aus Keyring geladen falls nicht angegeben)
        email: Email für n8n (optional, wird aus Keyring geladen falls nicht angegeben)
    """
    # Lade Lizenzdaten aus Keyring falls nicht angegeben
    if license_number is None or email is None:
        if LICENSE_SERVICE_AVAILABLE:
            print("🔑 Lade Lizenzdaten aus Keyring...")
            license_service = LicenseService()
            loaded_license, loaded_email = license_service.load_license()
            
            if loaded_license and loaded_email:
                if license_number is None:
                    license_number = loaded_license
                if email is None:
                    email = loaded_email
                print(f"   ✓ Lizenzdaten geladen: {loaded_license[:4]}..., {loaded_email[:3]}...")
            else:
                print("   ⚠️ Keine Lizenzdaten im Keyring gefunden!")
                print("   Verwende Standard-Werte (können falsch sein)")
                if license_number is None:
                    license_number = "123456"
                if email is None:
                    email = "ivan.levshyn@go-ecommerce.de"
        else:
            print("   ⚠️ LicenseService nicht verfügbar - verwende Standard-Werte")
            if license_number is None:
                license_number = "123456"
            if email is None:
                email = "ivan.levshyn@go-ecommerce.de"
    print("=" * 60)
    print("🚀 JTL zu n8n Produkt-Synchronisation")
    print("=" * 60)
    print()
    
    # Schritt 1: Initialisiere JTL Database Manager
    print("📊 Schritt 1: Verbindung zur JTL-Datenbank...")
    jtl_manager = JTLDatabaseManager()
    
    # Prüfe ob Credentials vorhanden sind
    if not jtl_manager.has_saved_credentials():
        print("❌ Keine gespeicherten JTL-Credentials gefunden!")
        print("   Bitte führen Sie zuerst den JTL-Dialog aus, um Credentials zu speichern.")
        return False
    
    print(f"   ✓ Verbindung hergestellt")
    print(f"   Server: {jtl_manager.config['server']}")
    print(f"   Datenbank: {jtl_manager.config['database']}")
    print()
    
    # Schritt 2: Hole Produktdaten von JTL
    print("📤 Schritt 2: Lade Produktdaten von JTL-Datenbank...")
    success, message, products = jtl_manager.get_products_with_taric_info()
    
    if not success or not products:
        print(f"❌ Fehler beim Laden der Produktdaten: {message}")
        return False
    
    print(f"   ✓ {message}")
    print(f"   ✓ Anzahl Produkte: {len(products)}")
    print()
    
    # Zeige ein Beispiel-Produkt
    if products:
        print("   Beispiel-Produkt:")
        example = products[0]
        for key, value in example.items():
            print(f"      {key}: {value}")
    print()
    
    # Schritt 3: Sende Daten an n8n
    print("📤 Schritt 3: Sende Daten an n8n Webhook...")
    n8n_manager = N8nWorkflowManager(
        workflow_url=None,
        license_number=license_number,
        email=email
    )
    
    success_send, response_message = n8n_manager.send_products_to_webhook(
        products, 
        webhook_url=n8n_webhook_url
    )
    
    if not success_send:
        print(f"❌ Fehler beim Senden der Daten: {response_message}")
        return False
    
    print(f"   ✓ {response_message}")
    print()
    
    # Schritt 4: Zusammenfassung
    print("=" * 60)
    print("✅ Synchronisation erfolgreich abgeschlossen!")
    print("=" * 60)
    print(f"   📦 Produkte gesendet: {len(products)}")
    print(f"   🎯 n8n Webhook: {n8n_webhook_url}")
    print()
    
    return True


def main():
    """Hauptfunktion"""
    try:
        # Zeige Hilfe wenn --help angefordert wird
        if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
            print("JTL zu n8n Produkt-Synchronisation")
            print()
            print("Verwendung:")
            print("  python sync_jtl_to_n8n.py [webhook_url] [license_number] [email]")
            print()
            print("Parameter:")
            print("  webhook_url     URL des n8n Webhooks (optional)")
            print("                  Standard: https://agentic.go-ecommerce.de/webhook-test/post_customer_product")
            print("  license_number  Lizenznummer für n8n (optional)")
            print("  email           Email für n8n (optional)")
            print()
            print("Beispiele:")
            print("  python sync_jtl_to_n8n.py")
            print("  python sync_jtl_to_n8n.py https://agentic.go-ecommerce.de/webhook-test/post_customer_product")
            print("  python sync_jtl_to_n8n.py <webhook_url> 123456 ivan.levshyn@go-ecommerce.de")
            return
        
        # Optionale Parameter parsen
        webhook_url = sys.argv[1] if len(sys.argv) > 1 else None
        license_number = sys.argv[2] if len(sys.argv) > 2 else None  # None = aus Keyring laden
        email = sys.argv[3] if len(sys.argv) > 3 else None  # None = aus Keyring laden
        
        # Synchronisation durchführen
        success = sync_products_to_n8n(
            n8n_webhook_url=webhook_url,
            license_number=license_number,
            email=email
        )
        
        # Exit Code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print()
        print("⚠️ Synchronisation durch Benutzer abgebrochen")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ Unerwarteter Fehler: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

