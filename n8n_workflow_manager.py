"""
n8n Workflow Integration für OSS goEcommerce
Suche über n8n Workflows mit Lizenzdaten im Header
"""

import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.config.endpoints import EndpointConfig
from app.core.debug_manager import debug_print

class N8nWorkflowManager:
    """Manager für n8n Workflow-Integration"""
    
    def __init__(self, workflow_url: str = None, license_number: str = "123456", email: str = "ivan.levshyn@go-ecommerce.de"):
        self.workflow_url = workflow_url or EndpointConfig.get_endpoint("taric_search")
        self.license_number = license_number
        self.email = email
        self.session = requests.Session()
        
        # Standard-Headers mit Lizenzdaten
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'OSS-goEcommerce/1.0.0',
            'X-License-Number': self.license_number,
            'X-License-Email': self.email,
            'X-App-Version': '1.0.0',
            'X-Timestamp': datetime.now().isoformat()
        })
    
    def search_taric_codes(self, search_taric: str) -> Tuple[bool, List[Dict], str]:
        """TARIC-Codes über n8n Workflow suchen"""
        try:
            # Bei GET-Request werden Parameter als Query-String übergeben
            from urllib.parse import urlencode
            
            params = {
                "taric_list": search_taric
            }
            
            # URL mit Query-Parametern erstellen
            request_url = f"{self.workflow_url}?{urlencode(params)}"
            
            debug_print(f"n8n Workflow Request: {request_url}")
            debug_print(f"Request Params: {params}")
            debug_print(f"Headers: {dict(self.session.headers)}")
            
            # n8n Workflow mit GET aufrufen
            response = self.session.get(
                request_url,
                timeout=30
            )
            
            if response.status_code == 200:
                result_data = response.json()
                
                debug_print(f"DEBUG: n8n Response Status: {response.status_code}")
                debug_print(f"DEBUG: n8n Response Headers: {dict(response.headers)}")
                debug_print(f"DEBUG: n8n Response Raw: {response.text}")
                debug_print(f"DEBUG: n8n Response Parsed: {json.dumps(result_data, indent=2)}")
                
                # Prüfe verschiedene Response-Formate
                if isinstance(result_data, list):
                    # Direktes Array von Ergebnissen
                    debug_print(f"DEBUG: Direktes Array mit {len(result_data)} Ergebnissen")
                    return True, result_data, 'Suche erfolgreich'
                elif isinstance(result_data, dict):
                    # Strukturierte Antwort
                    debug_print(f"DEBUG: Dictionary Response erhalten: {list(result_data.keys())}")
                    
                    # Prüfe verschiedene Erfolgs-Indikatoren
                    if result_data.get('success', False):
                        results = result_data.get('data', [])
                        message = result_data.get('message', 'Suche erfolgreich')
                        return True, results, message
                    elif 'data' in result_data and isinstance(result_data.get('data'), list):
                        # Daten direkt im 'data' Feld
                        results = result_data.get('data', [])
                        debug_print(f"DEBUG: Daten im 'data' Feld gefunden: {len(results)} Ergebnissen")
                        return True, results, 'Suche erfolgreich'
                    
                    # Prüfe ob es Steuerdaten sind (verschiedene Länder-Codes)
                    eu_countries = ['PL', 'PT', 'RO', 'SE', 'SI', 'SK', 'DE', 'FR', 'IT', 'ES', 'BE', 'BG', 'CY', 'CZ', 'DK', 'EE', 'FI', 'GB', 'GR', 'HR', 'HU', 'IE', 'LT', 'LU', 'LV', 'MT', 'NL']
                    if any(key in result_data for key in eu_countries):
                        # Steuerdaten direkt im Response gefunden
                        debug_print(f"DEBUG: Steuerdaten direkt im Response gefunden")
                        debug_print(f"DEBUG: Gefundene Länder: {[k for k in result_data.keys() if k in eu_countries]}")
                        
                        # Konvertiere zu erwartetem Format
                        formatted_result = {
                            'taric_code': search_taric,
                            'tax_rates': result_data,
                            'oss_combination_id': result_data.get('oss_combination_id', 'N/A'),
                            'description': result_data.get('description', ''),
                            'date': result_data.get('date', ''),
                            'status': result_data.get('status', 'Aktiv')
                        }
                        return True, [formatted_result], 'Suche erfolgreich'
                    
                    # Prüfe auf spezielle Felder die echte Daten enthalten könnten
                    elif 'myField' in result_data:
                        debug_print(f"DEBUG: 'myField' gefunden - prüfe Inhalt")
                        my_field_value = result_data.get('myField')
                        debug_print(f"DEBUG: myField Wert: {my_field_value}")
                        
                        # Wenn myField ein Dictionary mit Steuerdaten ist
                        if isinstance(my_field_value, dict) and any(key in my_field_value for key in eu_countries):
                            debug_print(f"DEBUG: Echte Steuerdaten in 'myField' gefunden")
                            formatted_result = {
                                'taric_code': search_taric,
                                'tax_rates': my_field_value,
                                'oss_combination_id': result_data.get('oss_combination_id', 'N/A')
                            }
                            return True, [formatted_result], 'Suche erfolgreich'
                        else:
                            return False, [], "n8n Workflow Fehler: Test-Response empfangen - Workflow muss aktiviert werden"
                    
                    # Prüfe auf andere mögliche Datenfelder
                    elif any(key in result_data for key in ['results', 'items', 'taric_data', 'response']):
                        data_key = next(key for key in ['results', 'items', 'taric_data', 'response'] if key in result_data)
                        data_value = result_data[data_key]
                        debug_print(f"DEBUG: Daten in '{data_key}' Feld gefunden: {type(data_value)}")
                        
                        if isinstance(data_value, list):
                            return True, data_value, 'Suche erfolgreich'
                        elif isinstance(data_value, dict):
                            return True, [data_value], 'Suche erfolgreich'
                    
                    # Wenn nichts anderes passt, aber es ist ein Dictionary ohne Fehler
                    elif not result_data.get('error') and not result_data.get('message', '').lower().startswith('error'):
                        debug_print(f"DEBUG: Unbekanntes Dictionary-Format, aber kein offensichtlicher Fehler")
                        debug_print(f"DEBUG: Versuche als einzelnes Ergebnis zu behandeln")
                        formatted_result = {
                            'taric_code': search_taric,
                            'raw_data': result_data,
                            'oss_combination_id': result_data.get('oss_combination_id', 'N/A')
                        }
                        return True, [formatted_result], 'Suche erfolgreich'
                    
                    else:
                        error_msg = result_data.get('error', result_data.get('message', 'Unbekannter Fehler'))
                        return False, [], f"n8n Workflow Fehler: {error_msg}"
                else:
                    # Unbekanntes Format
                    return False, [], f"n8n Workflow Fehler: Unbekanntes Response-Format"
            else:
                return False, [], f"HTTP Fehler: {response.status_code} - {response.text}"
                
        except requests.exceptions.RequestException as e:
            return False, [], f"Netzwerkfehler: {str(e)}"
        except Exception as e:
            return False, [], f"Unerwarteter Fehler: {str(e)}"
    
    def search_single_taric(self, taric_code: str) -> Tuple[bool, Dict, str]:
        """Einzelnen TARIC-Code über n8n Workflow suchen"""
        try:
            # Nur TARIC-Code im Body - Lizenzdaten sind bereits in den Headern
            request_data = {
                "taric_code": taric_code,
                "search_type": "single_taric",
                "timestamp": datetime.now().isoformat(),
                "request_id": f"single_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            debug_print(f"n8n Single TARIC Request: {self.workflow_url}")
            debug_print(f"Request Data: {json.dumps(request_data, indent=2)}")
            
            response = self.session.post(
                self.workflow_url,
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result_data = response.json()
                
                if result_data.get('success', False):
                    result = result_data.get('data', {})
                    message = result_data.get('message', 'Einzelne Suche erfolgreich')
                    return True, result, message
                else:
                    error_msg = result_data.get('error', 'Unbekannter Fehler')
                    return False, {}, f"n8n Workflow Fehler: {error_msg}"
            else:
                return False, {}, f"HTTP Fehler: {response.status_code} - {response.text}"
                
        except requests.exceptions.RequestException as e:
            return False, {}, f"Netzwerkfehler: {str(e)}"
        except Exception as e:
            return False, {}, f"Unerwarteter Fehler: {str(e)}"
    
    def test_workflow_connection(self) -> Tuple[bool, str]:
        """n8n Workflow-Verbindung testen"""
        try:
            # Nur Test-Flag im Body - Lizenzdaten sind bereits in den Headern
            test_data = {
                "test": True,
                "timestamp": datetime.now().isoformat()
            }
            
            response = self.session.post(
                self.workflow_url,
                json=test_data,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "n8n Workflow-Verbindung erfolgreich"
            else:
                return False, f"HTTP Fehler: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Verbindungsfehler: {str(e)}"
        except Exception as e:
            return False, f"Fehler: {str(e)}"
    
    def update_license_data(self, license_number: str, email: str):
        """Lizenzdaten aktualisieren"""
        self.license_number = license_number
        self.email = email
        
        # Headers aktualisieren
        self.session.headers.update({
            'X-License-Number': self.license_number,
            'X-License-Email': self.email,
            'X-Timestamp': datetime.now().isoformat()
        })
        
        debug_print(f"Lizenzdaten aktualisiert: {license_number} / {email}")
    
    def send_products_to_webhook(self, products: List[Dict], webhook_url: str = None) -> Tuple[bool, str]:
        """Sendet Produktdaten an n8n Webhook"""
        webhook_url = webhook_url or EndpointConfig.get_endpoint("webhook_post_customer_product")
        
        try:
            request_data = {
                "products": products,
                "count": len(products),
                "timestamp": datetime.now().isoformat()
            }
            
            debug_print(f"📤 Sende Produktdaten an n8n Webhook: {webhook_url}")
            debug_print(f"   Anzahl Produkte: {len(products)}")
            debug_print(f"   Request Format: {{'products': [...], 'count': {len(products)}, 'timestamp': ...}}")
            
            response = self.session.post(
                webhook_url,
                json=request_data,
                timeout=60  # Längeres Timeout für große Datenmengen
            )
            
            if response.status_code in [200, 201]:
                debug_print(f"✅ Daten erfolgreich an n8n gesendet (Status: {response.status_code})")
                return True, f"Erfolgreich: {response.status_code}"
            else:
                error_msg = f"HTTP Fehler: {response.status_code} - {response.text}"
                debug_print(f"❌ {error_msg}")
                return False, error_msg
                
        except requests.exceptions.Timeout:
            error_msg = "Timeout beim Senden der Daten"
            debug_print(f"❌ {error_msg}")
            return False, error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"Netzwerkfehler: {str(e)}"
            debug_print(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unerwarteter Fehler: {str(e)}"
            debug_print(f"❌ {error_msg}")
            return False, error_msg
    
    def get_workflow_status(self) -> Dict:
        """Workflow-Status abrufen"""
        return {
            'workflow_url': self.workflow_url,
            'license_number': self.license_number,
            'email': self.email,
            'headers': dict(self.session.headers),
            'last_request': datetime.now().isoformat()
        }

# Convenience functions
def get_n8n_manager(workflow_url: str = None, license_number: str = "123456", email: str = "ivan.levshyn@go-ecommerce.de") -> N8nWorkflowManager:
    """n8n Manager Instanz abrufen"""
    return N8nWorkflowManager(workflow_url, license_number, email)

def search_taric_via_n8n(search_taric: str, workflow_url: str = None, license_number: str = "123456", email: str = "ivan.levshyn@go-ecommerce.de") -> Tuple[bool, List[Dict], str]:
    """TARIC-Suche über n8n Workflow"""
    manager = get_n8n_manager(workflow_url, license_number, email)
    return manager.search_taric_codes(search_taric)

def test_n8n_connection(workflow_url: str = None, license_number: str = "123456", email: str = "ivan.levshyn@go-ecommerce.de") -> Tuple[bool, str]:
    """n8n-Verbindung testen"""
    manager = get_n8n_manager(workflow_url, license_number, email)
    return manager.test_workflow_connection()
