# n8n Workflow Implementation für OSS goEcommerce

## ✅ Implementiert - Automatische n8n Workflow-Ausführung

### 🎯 Was passiert beim Drücken des Such-Buttons:

1. **n8n Workflow wird automatisch ausgeführt**
2. **Lizenzdaten werden im Header gesendet**
3. **Fallback zu Supabase bei Fehlern**

### 🔧 So implementieren Sie Ihren n8n Workflow:

#### 1. n8n Workflow URL konfigurieren

**Option A: Konfigurationsdatei verwenden**
```python
# n8n_config.py bearbeiten:
N8N_WORKFLOW_URL = "https://ihr-n8n-instance.com/webhook/taric-search"
```

**Option B: Direkt in oss.py ändern**
```python
# In oss.py, Zeile 991:
workflow_url = 'https://ihr-n8n-instance.com/webhook/taric-search'  # Ihre URL hier
```

#### 2. Lizenzdaten konfigurieren

**Standard-Lizenzdaten:**
```python
# n8n_config.py:
DEFAULT_LICENSE_NUMBER = "123456"
DEFAULT_EMAIL = "ivan.levshyn@go-ecommerce.de"
```

**Lizenzdaten über License Check-Dialog:**
- Klicken Sie auf "License Check"
- Geben Sie Ihre Lizenzdaten ein
- Diese werden automatisch für n8n Workflow verwendet

#### 3. HTTP-Request-Format für Ihren n8n Workflow

**Request an Ihren n8n Workflow:**
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

#### 4. Erwartete Response von Ihrem n8n Workflow

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

### 🚀 Automatischer Ablauf beim Such-Button:

1. **Benutzer gibt TARIC-Code ein** (z.B. "01022910")
2. **Benutzer klickt "Suche"**
3. **App führt automatisch aus:**
   - n8n Workflow wird aufgerufen
   - Lizenzdaten werden im Header gesendet
   - Request wird an Ihre n8n-Instanz gesendet
   - Ergebnisse werden empfangen und angezeigt
4. **Bei Fehlern:** Automatischer Fallback zu Supabase

### 📊 Verfügbare Konfigurationen:

#### n8n Workflow aktivieren/deaktivieren:
```python
# n8n_config.py:
USE_N8N_WORKFLOW = True   # n8n Workflow aktivieren
USE_N8N_WORKFLOW = False  # n8n Workflow deaktivieren (nur Supabase)
```

#### Fallback-Verhalten:
```python
# Automatisches Fallback: n8n → Supabase → Demo
# Wenn n8n fehlschlägt, wird automatisch Supabase verwendet
```

### 🔍 Debug-Informationen:

Die App zeigt Debug-Informationen in der Konsole:
```
DEBUG: Verwende n8n Workflow für TARIC-Suche: 01022910
n8n Workflow Request: https://ihr-n8n-instance.com/webhook/taric-search
Request Data: {...}
Headers: {...}
```

### ✅ Status: Vollständig implementiert

- ✅ **Automatische n8n Workflow-Ausführung** beim Such-Button
- ✅ **Lizenzdaten im Header** werden automatisch gesendet
- ✅ **Konfigurierbare Workflow-URL** über n8n_config.py
- ✅ **Automatisches Fallback** zu Supabase bei Fehlern
- ✅ **License Check-Integration** für dynamische Lizenzdaten
- ✅ **Debug-Logging** für Troubleshooting

### 🎯 Nächste Schritte:

1. **Ihre n8n Workflow-URL** in `n8n_config.py` eintragen
2. **Ihren n8n Workflow** entsprechend dem Request-Format anpassen
3. **Testen** mit einem TARIC-Code (z.B. "01022910")

**Ihr n8n Workflow ist jetzt vollständig in die App integriert!** 🎉
