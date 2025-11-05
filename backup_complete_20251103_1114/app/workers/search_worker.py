"""
Search Worker für OSS goEcommerce
Worker Thread für Suchoperationen mit n8n Workflow
"""

from PySide6.QtCore import QThread, Signal


class SearchWorker(QThread):
    """Worker thread for search operations"""
    result_ready = Signal(object)  # Kann sowohl Liste als auch String sein
    error_occurred = Signal(str)
    
    def __init__(self, search_taric, table_name="products", use_n8n=True, n8n_config=None):
        super().__init__()
        self.search_taric = search_taric
        self.table_name = table_name
        self.use_n8n = use_n8n
        self.n8n_config = n8n_config or {}
        self.n8n_manager = None
        
        if use_n8n:
            try:
                from n8n_workflow_manager import N8nWorkflowManager
                print("Erstelle n8n Workflow-Manager...")
                workflow_url = self.n8n_config.get('workflow_url')
                license_number = self.n8n_config.get('license_number', '123456')
                email = self.n8n_config.get('email', 'ivan.levshyn@go-ecommerce.de')
                
                if not workflow_url:
                    print("FEHLER: Keine n8n Workflow URL in der Konfiguration gefunden!")
                    self.error_occurred.emit("Keine n8n Workflow URL konfiguriert!")
                    return
                
                self.n8n_manager = N8nWorkflowManager(workflow_url, license_number, email)
                print("OK: n8n Workflow-Manager erfolgreich erstellt!")
                print(f"   Workflow URL: {workflow_url}")
                print(f"   Lizenznummer: {license_number}")
                print(f"   E-Mail: {email}")
            except ImportError as e:
                print(f"FEHLER: n8n Workflow Manager nicht verfügbar: {e}")
                self.error_occurred.emit(f"n8n Workflow Manager nicht verfügbar: {e}")
            except Exception as e:
                print(f"FEHLER: n8n Workflow-Verbindung fehlgeschlagen: {str(e)}")
                self.error_occurred.emit(f"n8n Workflow-Verbindung fehlgeschlagen: {str(e)}")
        else:
            print(f"FEHLER: n8n nicht verfügbar. Verwende n8n: {use_n8n}")
    
    def run(self):
        """Führt die Suchoperation aus"""
        import time
        time.sleep(0.5)  # Simuliere Verarbeitungszeit
        
        if self.use_n8n and self.n8n_manager:
            try:
                print(f"DEBUG: Führe n8n Workflow für TARIC-Suche aus: {self.search_taric}")
                success, results, message = self.n8n_manager.search_taric_codes(self.search_taric)
                
                print(f"DEBUG: n8n Workflow Response - Success: {success}")
                print(f"DEBUG: n8n Workflow Response - Message: {message}")
                print(f"DEBUG: n8n Workflow Response - Results Type: {type(results)}")
                print(f"DEBUG: n8n Workflow Response - Results: {results}")
                
                if success:
                    if results:
                        print(f"DEBUG: n8n Workflow erfolgreich - Ergebnisse: {len(results) if results else 0} Einträge")
                        # Stelle sicher, dass results eine Liste ist
                        if not isinstance(results, list):
                            results = [results]
                        self.result_ready.emit(results)
                    else:
                        print("DEBUG: n8n Workflow erfolgreich aber keine Ergebnisse")
                        self.result_ready.emit([])
                else:
                    print(f"DEBUG: n8n Workflow Fehler: {message}")
                    self.error_occurred.emit(f"n8n Workflow Fehler: {message}")
            except Exception as e:
                print(f"DEBUG: Exception in n8n Workflow: {str(e)}")
                print(f"DEBUG: Exception Type: {type(e)}")
                import traceback
                traceback.print_exc()
                self.error_occurred.emit(f"n8n Workflow Fehler: {str(e)}")
        else:
            # Fallback für lokale Suche (falls implementiert)
            print(f"DEBUG: Lokale Suche für TARIC-Code: {self.search_taric}")
            self.error_occurred.emit("Lokale Suche noch nicht implementiert")
