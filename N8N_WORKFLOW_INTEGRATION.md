# n8n Workflow Integration für OSS goEcommerce

## 🎯 Wie Sie Ihren n8n Workflow verbinden können

### 1. n8n Workflow Manager verwenden

Der `n8n_workflow_manager.py` ist bereits erstellt und kann direkt verwendet werden:

```python
from n8n_workflow_manager import N8nWorkflowManager

# n8n Workflow Manager initialisieren
manager = N8nWorkflowManager(
    workflow_url="https://ihr-n8n-instance.com/webhook/taric-search",
    license_number="123456",
    email="ivan.levshyn@go-ecommerce.de"
)

# TARIC-Suche über n8n Workflow
success, results, message = manager.search_taric_codes("01022910")

if success:
    print(f"Suchergebnisse: {results}")
else:
    print(f"Fehler: {message}")
```

### 2. Headers mit Lizenzdaten

Der Manager fügt automatisch die Lizenzdaten in die HTTP-Headers ein:

```http
POST https://ihr-n8n-instance.com/webhook/taric-search
Content-Type: application/json
User-Agent: OSS-goEcommerce/1.0.0
X-License-Number: 123456
X-License-Email: ivan.levshyn@go-ecommerce.de
X-App-Version: 1.0.0
X-Timestamp: 2025-10-14T10:30:00.000000

{
  "search_term": "01022910",
  "search_type": "taric",
  "license_number": "123456",
  "email": "ivan.levshyn@go-ecommerce.de",
  "timestamp": "2025-10-14T10:30:00.000000",
  "request_id": "req_20251014_103000"
}
```

### 3. n8n Workflow in Ihrer App integrieren

Sie können den n8n Workflow direkt in Ihre bestehende App integrieren:

```python
# In Ihrer oss.py - SearchWorker erweitern
def perform_search_with_n8n(self):
    """Suche mit n8n Workflow durchführen"""
    search_text = self.search_input.text().strip()
    
    if not search_text:
        return
    
    # n8n Workflow Manager verwenden
    n8n_manager = N8nWorkflowManager(
        workflow_url="https://ihr-n8n-instance.com/webhook/taric-search",
        license_number="123456",
        email="ivan.levshyn@go-ecommerce.de"
    )
    
    # Suche über n8n Workflow
    success, results, message = n8n_manager.search_taric_codes(search_text)
    
    if success:
        # Ergebnisse anzeigen
        self.show_results(results)
    else:
        # Fehler anzeigen oder Fallback zu Supabase
        QMessageBox.warning(self, "n8n Fehler", f"n8n Workflow Fehler: {message}")
```

### 4. n8n Workflow-Konfiguration

#### Workflow URL
```
https://ihr-n8n-instance.com/webhook/taric-search
```

#### Erwartete Request-Struktur
```json
{
  "search_term": "01022910",
  "search_type": "taric",
  "license_number": "123456",
  "email": "ivan.levshyn@go-ecommerce.de",
  "timestamp": "2025-10-14T10:30:00.000000",
  "request_id": "req_20251014_103000"
}
```

#### Erwartete Response-Struktur
```json
{
  "success": true,
  "message": "Suche erfolgreich",
  "data": [
    {
      "taric_code": "01022910",
      "oss_combination_id": "12345",
      "country_tax_rates": {
        "DE": 19.0,
        "FR": 20.0,
        "IT": 22.0
      },
      "country_names": {
        "DE": "Deutschland",
        "FR": "Frankreich", 
        "IT": "Italien"
      }
    }
  ]
}
```

### 5. Test-Verbindung

```python
# Verbindung testen
manager = N8nWorkflowManager(
    workflow_url="https://ihr-n8n-instance.com/webhook/taric-search",
    license_number="123456",
    email="ivan.levshyn@go-ecommerce.de"
)

success, message = manager.test_workflow_connection()

if success:
    print(f"n8n Workflow-Verbindung OK: {message}")
else:
    print(f"n8n Workflow-Verbindung Fehler: {message}")
```

### 6. Fallback-Strategie

Die App unterstützt automatisches Fallback:

1. **n8n Workflow** (Priorität 1)
2. **Supabase** (Priorität 2) 
3. **Demo-Modus** (Priorität 3)

```python
# SearchWorker mit n8n-Unterstützung
search_worker = SearchWorker(
    search_text="01022910",
    table_name="taric",
    use_database=True,
    use_n8n=True,
    n8n_config={
        'workflow_url': 'https://ihr-n8n-instance.com/webhook/taric-search',
        'license_number': '123456',
        'email': 'ivan.levshyn@go-ecommerce.de'
    }
)
```

### 7. Lizenzdaten aktualisieren

```python
# Lizenzdaten zur Laufzeit aktualisieren
manager.update_license_data("789012", "neue@email.de")

# Headers werden automatisch aktualisiert:
# X-License-Number: 789012
# X-License-Email: neue@email.de
```

## ✅ Bereits implementiert

- ✅ n8n Workflow Manager (`n8n_workflow_manager.py`)
- ✅ Lizenzdaten in HTTP-Headers
- ✅ Automatisches Fallback-System
- ✅ Integration in SearchWorker
- ✅ Test-Funktionen
- ✅ Fehlerbehandlung

## 🚀 Sofort einsatzbereit

Sie können Ihren n8n Workflow jetzt direkt verwenden:

1. **Workflow URL** in `n8n_workflow_manager.py` anpassen
2. **Lizenzdaten** konfigurieren
3. **SearchWorker** mit `use_n8n=True` verwenden
4. **Ergebnisse** werden automatisch angezeigt

**Ihr n8n Workflow ist bereit für die Integration!** 🎉
