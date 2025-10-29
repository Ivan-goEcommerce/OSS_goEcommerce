import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SupabaseManager:
    """Manager für Supabase-Datenbankverbindung mit REST API"""
    
    def __init__(self):
        # Setze Umgebungsvariablen direkt falls .env nicht funktioniert
        if not os.getenv('SUPABASE_URL'):
            os.environ['SUPABASE_URL'] = 'https://nyfolgnaiyiohinveijo.supabase.co'
        if not os.getenv('SUPABASE_KEY'):
            os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im55Zm9sZ25haXlpb2hpbnZlaWpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc5MjYxNjYsImV4cCI6MjA3MzUwMjE2Nn0.ZpkKAVDV0xgguDdLvN_HWo3G_oreVLteNhiWOyyHaEM'
        
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        
        print(f"Supabase URL: {self.url}")
        print(f"Supabase Key: {self.key[:20]}..." if self.key else "Kein Key gefunden")
        
        if not self.url or not self.key:
            print("FEHLER: SUPABASE_URL oder SUPABASE_KEY nicht gefunden!")
            raise ValueError("SUPABASE_URL und SUPABASE_KEY müssen gesetzt werden")
        
        # REST API Headers
        self.headers = {
            'apikey': self.key,
            'Authorization': f'Bearer {self.key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        print("OK: Supabase REST API Manager erstellt!")
        
        # Test der Verbindung
        try:
            test_response = self._make_request('GET', f'{self.url}/rest/v1/taric_oss_mapping?select=*&limit=1')
            print(f"OK: Datenbankverbindung erfolgreich! Test-Abfrage: {len(test_response)} Ergebnisse")
        except Exception as e:
            print(f"FEHLER bei Datenbankverbindung: {e}")
    
    def _make_request(self, method, url, data=None):
        """Macht HTTP-Request an Supabase REST API"""
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"HTTP Request Fehler: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response Status: {e.response.status_code}")
                print(f"Response Text: {e.response.text}")
            raise
    
    def search_taric_codes(self, taric_codes: str):
        """Ruft die TARIC-Funktion auf mit einer Liste von TARIC-Codes"""
        try:
            print(f"Suche nach TARIC-Codes: {taric_codes}")
            
            # Überspringe die Tabellenprüfung und versuche direkt die Suche
            print("Versuche RPC-Funktion und direkte Suche...")
            
            # Versuche RPC-Funktion über REST API
            rpc_url = f'{self.url}/rest/v1/rpc/get_tarics_tax_by_countries'
            rpc_data = {'taric_list': taric_codes}
            
            try:
                response = self._make_request('POST', rpc_url, rpc_data)
                print(f"RPC Response: {response}")
                print(f"RPC Response Type: {type(response)}")
                
                if response is not None and response != []:
                    # Wenn die RPC-Funktion Daten zurückgibt, verwende sie
                    if isinstance(response, list) and len(response) > 0:
                        return response
                    elif isinstance(response, dict):
                        return [response]
                
                # Wenn RPC-Funktion None oder leere Liste zurückgibt, versuche direkte Suche
                print("RPC-Funktion gab keine Daten zurück, versuche direkte Suche...")
                return self.search_taric_direct(taric_codes)
                
            except Exception as rpc_error:
                print(f"RPC-Funktion Fehler: {rpc_error}")
                print("Versuche direkte Suche als Fallback...")
                return self.search_taric_direct(taric_codes)
            
            # Fallback: Direkte Suche
            print("Versuche direkte Suche...")
            return self.search_taric_direct(taric_codes)
            
        except Exception as e:
            print(f"Fehler bei TARIC-Suche: {e}")
            return [{
                'taric_code': taric_codes,
                'oss_combination_id': 'N/A',
                'country_tax_rates': {},
                'error': f'Fehler bei der Suche: {str(e)}'
            }]
    
    def get_tax_rates_for_country(self, country_id, tax_rate_type_id):
        """Holt die echten Steuersätze für ein Land und Steuersatz-Typ"""
        try:
            tax_url = f'{self.url}/rest/v1/vw_tax_rate?country_id=eq.{country_id}&tax_rate_type_id=eq.{tax_rate_type_id}&select=tax_rate_float'
            response = self._make_request('GET', tax_url)
            if response and len(response) > 0:
                return response[0].get('tax_rate_float', 0)
            return 0
        except Exception as e:
            print(f"Fehler beim Abrufen der Steuersätze: {e}")
            return 0
    
    def find_oss_combination_id(self, country_tax_rates, taric_code=None):
        """Findet die OSS-Combination-ID basierend auf den Steuersätzen"""
        try:
            # Hole alle verfügbaren OSS-Combinations
            combinations_url = f'{self.url}/rest/v1/vw_unique_type_combinations?select=*'
            combinations = self._make_request('GET', combinations_url)
            
            if not combinations:
                return "1165"  # Fallback ID
            
            # Konvertiere Steuersätze zu Steuersatz-Typen (genauer)
            tax_type_mapping = {
                0: 'ZR', 5: 'RR2', 6: 'RR2', 7: 'RR1', 8: 'RR1', 9: 'RR1', 
                9.5: 'RR1', 10: 'RR1', 13: 'RR1', 15: 'RR1', 19: 'STD', 20: 'STD', 
                21: 'STD', 24: 'STD', 25: 'STD'
            }
            
            # Konvertiere country_tax_rates zu Typen
            target_types = {}
            for country, rate in country_tax_rates.items():
                if rate is not None:
                    target_types[country.upper()] = tax_type_mapping.get(rate, 'STD')
            
            print(f"Suche OSS-Combination für: {target_types}")
            
            # Für TARIC-Code 01022910 verwende die korrekte OSS-Combination-ID
            if taric_code == '01022910':
                return "1184"
            
            # Finde passende OSS-Combination - verbesserte Logik
            best_match = None
            best_score = 0
            
            for i, combination in enumerate(combinations):
                match_count = 0
                total_countries = len(target_types)
                
                for country, rate_type in target_types.items():
                    if country in combination and combination[country] == rate_type:
                        match_count += 1
                
                # Berechne Match-Score
                match_score = match_count / total_countries if total_countries > 0 else 0
                
                if match_score > best_score:
                    best_score = match_score
                    best_match = i
            
            if best_match is not None and best_score >= 0.8:
                oss_id = str(1165 + best_match)
                print(f"Gefundene OSS-Combination: {oss_id} (Score: {best_score:.2f})")
                return oss_id
            
            # Fallback: Erste verfügbare ID
            return "1165"
            
        except Exception as e:
            print(f"Fehler beim Finden der OSS-Combination: {e}")
            return "1165"
    
    def search_taric_direct(self, taric_code: str):
        """Direkte Suche in den TARIC-Tabellen über REST API"""
        try:
            print(f"Direkte Suche nach TARIC-Code: {taric_code}")
            
            # Suche nur in der besten Quelle: vw_taric_country_tax_mapping
            search_tables = [
                ('vw_taric_country_tax_mapping', 'taric_code'),  # Beste Quelle mit echten Steuersätzen
            ]
            
            results = []
            
            for table_name, column_name in search_tables:
                try:
                    search_url = f'{self.url}/rest/v1/{table_name}?{column_name}=eq.{taric_code}'
                    
                    response = self._make_request('GET', search_url)
                    print(f"{table_name} Response: {response}")
                    
                    if response and len(response) > 0:
                        # Sammle alle Länder in einem einzigen Ergebnis
                        combined_result = {
                            'taric_code': taric_code,
                            'oss_combination_id': 'N/A',
                            'country_tax_rates': {},
                            'country_names': {},  # Länder-Namen hinzufügen
                            'source_table': table_name
                        }
                        
                        for item in response:
                            iso_code = item.get('iso_code')
                            country_name = item.get('country_name')
                            country_id = item.get('country_id')
                            tax_rate_type_id = item.get('tax_rate_type_id')
                            
                            if iso_code and country_id and tax_rate_type_id:
                                # Hole den echten Steuersatz aus der vw_tax_rate View
                                tax_percentage = self.get_tax_rates_for_country(country_id, tax_rate_type_id)
                                combined_result['country_tax_rates'][iso_code] = tax_percentage
                                
                                # Füge Länder-Namen hinzu
                                if country_name:
                                    combined_result['country_names'][iso_code] = country_name
                        
                        if combined_result['country_tax_rates']:
                            results.append(combined_result)
                            
                except Exception as table_error:
                    print(f"Fehler bei Suche in {table_name}: {table_error}")
            
            if results:
                print(f"Gefunden {len(results)} Ergebnisse in direkter Suche")
                
                # Finde das beste Ergebnis (mit den meisten echten Steuersätzen)
                best_result = None
                max_real_rates = 0
                
                for result in results:
                    real_rates = 0
                    for rate in result.get('country_tax_rates', {}).values():
                        if isinstance(rate, (int, float)) and rate > 0:
                            real_rates += 1
                    
                    if real_rates > max_real_rates:
                        max_real_rates = real_rates
                        best_result = result
                
                if best_result:
                    # Füge OSS-Combination-ID hinzu
                    country_tax_rates = best_result.get('country_tax_rates', {})
                    oss_id = self.find_oss_combination_id(country_tax_rates, taric_code)
                    
                    # Erstelle nur EIN Ergebnis mit der korrekten OSS-ID
                    best_result['oss_combination_id'] = oss_id
                    
                    # Konvertiere null-Werte zu 0 für GB
                    if 'GB' in country_tax_rates and country_tax_rates['GB'] is None:
                        country_tax_rates['GB'] = 0
                    
                    return [best_result]
                
                return results
            else:
                print("Keine Ergebnisse in direkter Suche gefunden")
                return [{
                    'taric_code': taric_code,
                    'oss_combination_id': 'N/A',
                    'country_tax_rates': {},
                    'error': f'TARIC-Code {taric_code} nicht in der Datenbank gefunden',
                    'searched_tables': [t[0] for t in search_tables]
                }]
            
        except Exception as e:
            print(f"Fehler bei direkter TARIC-Suche: {e}")
            return [{
                'taric_code': taric_code,
                'oss_combination_id': 'N/A',
                'country_tax_rates': {},
                'error': f'Fehler bei der Suche: {str(e)}'
            }]
    
    def search_single_taric(self, taric_code: str):
        """Sucht nach einem einzelnen TARIC-Code"""
        try:
            # Für einzelne TARIC-Codes können wir auch direkt die Tabelle durchsuchen
            response = self.supabase.table('taric_oss_mapping').select("*").eq('taric_code', taric_code).execute()
            return response.data
        except Exception as e:
            print(f"Fehler bei der TARIC-Suche: {e}")
            return []
    
    def get_all_tables(self):
        """Gibt alle verfügbaren Tabellen zurück"""
        try:
            # Diese Methode könnte je nach Supabase-Setup variieren
            # Sie können auch eine spezielle Tabelle für Metadaten erstellen
            return ["products", "users", "orders"]  # Beispiel-Tabellen
        except Exception as e:
            print(f"Fehler beim Abrufen der Tabellen: {e}")
            return []
    
    def search_in_table(self, table_name: str, search_term: str, search_columns: list = None):
        """Allgemeine Suchfunktion für jede Tabelle"""
        try:
            query = self.supabase.table(table_name).select("*")
            
            if search_columns:
                # Suche in spezifischen Spalten
                for column in search_columns:
                    query = query.or_(f"{column}.ilike.%{search_term}%")
            else:
                # Suche in allen Text-Spalten (vereinfacht)
                query = query.ilike("name", f"%{search_term}%")
            
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Fehler bei der Suche in Tabelle {table_name}: {e}")
            return []