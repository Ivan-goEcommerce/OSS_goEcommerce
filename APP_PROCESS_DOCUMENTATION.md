# OSS goEcommerce - Komplette Prozess-Dokumentation

## 📋 Inhaltsverzeichnis
1. [App-Start und Initialisierung](#app-start)
2. [Hauptprozess-Flow](#hauptprozess)
3. [OSS-Abgleich Prozess](#oss-abgleich)
4. [Verwendete Dateien](#verwendete-dateien)
5. [Nicht verwendete Dateien](#nicht-verwendete-dateien)

---

## 🚀 App-Start und Initialisierung {#app-start}

### 1. Entry Point
```
main.py
  └─> app/__init__.py::main()
      └─> DashboardWindow (app/ui/dashboard.py)
```

### 2. Start-Ablauf
1. **main.py** wird ausgeführt
2. **app/__init__.py::main()** wird aufgerufen
3. **QApplication** wird initialisiert
4. **Farbschema** wird geladen (Orange-Schwarz)
5. **Debug-Modus** Dialog wird angezeigt (optional)
6. **DashboardWindow** wird erstellt und angezeigt
7. **Lizenzprüfung** wird automatisch gestartet (blockiert App bis erfolgreich)

### 3. Lizenzprüfung beim Start
- **Dialog**: `LicenseGUIWindow` (app/dialogs/license_gui_window.py)
- **Service**: `LicenseService` → `LicenseManager`
- **Speicherung**: Windows Keyring
- **Bei Erfolg**: App wird freigegeben
- **Bei Fehler**: App wird beendet

---

## 📊 Hauptprozess-Flow {#hauptprozess}

### Dashboard Window (app/ui/dashboard.py)
Das Dashboard ist die zentrale Steuerung der App:

```
DashboardWindow
├─> Lizenz-Status (oben rechts)
├─> Datenbank-Status (oben rechts)
├─> TARIC-Suche (Button)
├─> OSS-Abgleich (Button) ⭐ Hauptfunktion
├─> Trigger-Update (Button)
├─> DB Credentials (Button)
└─> Statistiken (Cards)
```

### Verfügbare Aktionen:

1. **TARIC-Suche**
   - Öffnet Dialog für TARIC-Code-Eingabe
   - Verwendet: `WorkflowService` → `N8nWorkflowManager`
   - Endpoint: `taric_search` (GET)

2. **OSS-Abgleich** ⭐ (Hauptprozess - siehe unten)

3. **Trigger-Update**
   - Worker: `TriggerFetchWorker`
   - Service: `TriggerEndpointService`
   - Endpoint: `trigger_get_products` (GET)

4. **DB Credentials**
   - Dialog: `JTLConnectionDialog`
   - Service: `DatabaseService`

---

## 🔄 OSS-Abgleich Prozess {#oss-abgleich}

### Übersicht
Der OSS-Abgleich ist der **Hauptprozess** der App. Er orchestriert:
1. Produkte senden → n8n Webhook
2. Steuersätze holen → API Endpoint
3. SQL ausführen → Datenbank

### Detaillierter Ablauf

```
User klickt "OSS-Abgleich" Button
  │
  ├─> DashboardWindow.start_sync_worker()
  │   └─> OSSStartWorker (QThread)
  │       │
  │       ├─> 1. Initialisierung
  │       │   ├─> DatabaseService (DB-Verbindung)
  │       │   ├─> WorkflowService (n8n Integration)
  │       │   └─> OSSStart (Parent-Klasse)
  │       │       ├─> Lädt Lizenz aus Keyring (MUSS vorhanden sein!)
  │       │       ├─> DecryptService (für Entschlüsselung)
  │       │       └─> Session mit Headers (License, Email)
  │       │
  │       ├─> 2. run_oss_reconciliation()
  │       │   │
  │       │   ├─> Schritt 1: Produkte senden
  │       │   │   ├─> db_service.get_products_with_taric_info()
  │       │   │   │   └─> JTLDatabaseManager (holt Produkte aus DB)
  │       │   │   │
  │       │   │   └─> send_products()
  │       │   │       ├─> Endpoint: webhook_post_customer_product (POST)
  │       │   │       ├─> Format: {"products": [...], "count": N, "timestamp": ...}
  │       │   │       └─> WorkflowService.send_products_to_webhook()
  │       │   │           └─> N8nWorkflowManager.send_products_to_webhook()
  │       │   │
  │       │   ├─> Schritt 2: Steuersätze holen
  │       │   │   └─> get_tax_rates()
  │       │   │       ├─> Endpoint: tax_rates (GET)
  │       │   │       │   └─> https://agentic.go-ecommerce.de/webhook/v1/tax-rates
  │       │   │       │
  │       │   │       ├─> 2.1: Hole verschlüsselte Daten (n8n-Format)
  │       │   │       │   └─> Response: Liste von verschlüsselten Items
  │       │   │       │
  │       │   │       ├─> 2.2: Entschlüsselung
  │       │   │       │   └─> DecryptService.decrypt_from_n8n_format()
  │       │   │       │       └─> decrypt_utils.decrypt_data()
  │       │   │       │
  │       │   │       ├─> 2.3: SQL formatieren
  │       │   │       │   └─> DecryptService.format_sql_for_execution()
  │       │   │       │       ├─> Entfernt BOM (Byte Order Mark)
  │       │   │       │       └─> Entfernt Control Characters
  │       │   │       │
  │       │   │       └─> 2.4: Callback für entschlüsseltes SQL
  │       │   │           └─> decrypted_sql_ready Signal
  │       │   │               └─> Dashboard zeigt SQL-Dialog (optional)
  │       │   │
  │       │   └─> Schritt 3: SQL ausführen
  │       │       └─> execute_tax_rates_sql()
  │       │           ├─> fix_trigger_structure() (korrigiert Trigger-Syntax)
  │       │           ├─> db_service.test_connection()
  │       │           └─> db_service.execute_query()
  │       │               └─> Führt SQL in JTL-Datenbank aus
  │       │
  │       └─> 3. Ergebnisse zurückgeben
  │           └─> Dashboard zeigt Erfolg/Fehler
```

### Endpunkte beim OSS-Abgleich

1. **POST** `webhook_post_customer_product`
   - URL: `https://agentic.go-ecommerce.de/webhook/post_customer_product`
   - Body: `{"products": [...], "count": N, "timestamp": ...}`
   - Zweck: Sendet Produktdaten an n8n

2. **GET** `tax_rates`
   - URL: `https://agentic.go-ecommerce.de/webhook/v1/tax-rates`
   - Response: Verschlüsselte Steuersätze (n8n-Format)
   - Zweck: Holt aktuelle Steuersätze

### Datenfluss

```
JTL-Datenbank
  │
  ├─> Produkte (mit TARIC)
  │   └─> n8n Webhook (POST)
  │
  └─> Steuersätze (SQL)
      └─> API (GET) → Entschlüsselung → SQL → JTL-Datenbank
```

---

## ✅ Verwendete Dateien {#verwendete-dateien}

### Core Files
- ✅ `main.py` - Entry Point
- ✅ `app/__init__.py` - App Initialisierung
- ✅ `app/config/__init__.py` - Config-Funktionen
- ✅ `app/config/endpoints.py` - Endpoint-Konfiguration (Single Point of Truth)
- ✅ `app/core/logging_config.py` - Logging
- ✅ `app/core/debug_manager.py` - Debug-Management

### UI
- ✅ `app/ui/dashboard.py` - Hauptfenster
- ✅ `app/ui/components/__init__.py` - UI-Komponenten (StyledGroupBox, etc.)

### Managers
- ✅ `app/managers/oss_start.py` - **Hauptklasse für OSS-Abgleich**
- ✅ `app/managers/license_manager.py` - Lizenz-Verwaltung
- ✅ `app/managers/oss_schema_manager.py` - OSS-Schema (wird initialisiert, aber aktuell nicht aktiv genutzt)
- ⚠️ `app/managers/monitoring_manager.py` - **NICHT VERWENDET** (siehe unten)

### Services
- ✅ `app/services/database_service.py` - Datenbank-Service
- ✅ `app/services/decrypt_service.py` - Entschlüsselung
- ✅ `app/services/license_service.py` - Lizenz-Service (Wrapper)
- ✅ `app/services/workflow_service.py` - n8n Workflow-Service
- ✅ `app/services/trigger_endpoint_service.py` - Trigger-Endpoint-Service
- ❌ `app/services/webhook_service.py` - **NICHT VERWENDET** (siehe unten)

### Workers (QThread)
- ✅ `app/workers/oss_start_worker.py` - Worker für OSS-Abgleich
- ✅ `app/workers/sync_worker.py` - Worker für Sync (JTL → n8n)
- ✅ `app/workers/trigger_fetch_worker.py` - Worker für Trigger-Update
- ❌ `app/workers/search_worker.py` - **NICHT VERWENDET** (siehe unten)

### Dialogs
- ✅ `app/dialogs/jtl_dialog.py` - JTL-Datenbank Dialog
- ✅ `app/dialogs/license_dialog.py` - Lizenz-Dialog
- ✅ `app/dialogs/license_gui_window.py` - Lizenz-GUI (beim Start)
- ✅ `app/dialogs/decrypt_dialog.py` - Entschlüsselungs-Dialog

### Utils
- ✅ `app/utils/decrypt_utils.py` - Entschlüsselungs-Hilfsfunktionen
- ❌ `app/utils/__usage_example__.py` - **NUR BEISPIELE** (siehe unten)

### Externe Manager
- ✅ `n8n_workflow_manager.py` - n8n Workflow-Integration
- ✅ `jtl_database_manager.py` - JTL-Datenbank-Manager

### Standalone Scripts
- ⚠️ `sync_jtl_to_n8n.py` - Standalone-Script (kann manuell ausgeführt werden)

---

## ❌ Nicht verwendete Dateien {#nicht-verwendete-dateien}

### ⛔ Völlig unbenutzt (kann gelöscht werden)

1. **`app/managers/monitoring_manager.py`**
   - Wird nur in `app/managers/__init__.py` importiert
   - Wird in `app/utils/__usage_example__.py` als Beispiel erwähnt
   - **NIRGENDWO** in der aktiven App verwendet
   - **Status**: ❌ Kann gelöscht werden

2. **`app/services/webhook_service.py`**
   - Enthält `WebhookService` Klasse
   - **KEINE** Verwendung in der App gefunden
   - **Status**: ❌ Kann gelöscht werden

3. **`app/workers/search_worker.py`**
   - Enthält `SearchWorker` Klasse
   - **KEINE** Verwendung in der App gefunden
   - **Status**: ❌ Kann gelöscht werden

4. **`supabase_manager.py`**
   - Enthält `SupabaseManager` Klasse
   - **KEINE** Verwendung in der App gefunden
   - **Status**: ❌ Kann gelöscht werden

5. **`app/utils/__usage_example__.py`**
   - Enthält nur Beispiel-Code
   - **KEINE** Verwendung in der App
   - **Status**: ❌ Kann gelöscht werden (oder zu Dokumentation verschieben)

6. **`str`** (Datei im Root)
   - Unbekannte Datei
   - **Status**: ❌ Prüfen und ggf. löschen

### ⚠️ Teilweise verwendet (optional löschen)

1. **`app/managers/oss_schema_manager.py`**
   - Wird in `dashboard.py` importiert
   - Wird aber nur als `None` initialisiert: `self.oss_schema_manager = None`
   - **Status**: ⚠️ Wird nicht aktiv genutzt, aber Import vorhanden

2. **`app/config.py`** ⚠️ **DUPLIKAT**
   - Enthält gleiche Funktionen wie `app/config/__init__.py`
   - Wird verwendet: `from .config import get_color_scheme` in `app/__init__.py`
   - **ABER**: `app/config/__init__.py` hat die gleichen Funktionen
   - **Status**: ⚠️ **Kann gelöscht werden** - `app/config/__init__.py` ersetzt es vollständig

3. **`sync_jtl_to_n8n.py`**
   - Standalone-Script
   - Kann manuell ausgeführt werden
   - **Status**: ⚠️ Optional behalten für manuelle Syncs

---

## 📝 Zusammenfassung

### Hauptprozess: OSS-Abgleich
1. **Produkte senden** → POST `webhook_post_customer_product`
2. **Steuersätze holen** → GET `tax_rates` → Entschlüsselung
3. **SQL ausführen** → Datenbank-Update

### Wichtige Klassen
- `OSSStart` - Orchestriert den gesamten OSS-Abgleich
- `OSSStartWorker` - Background-Thread für OSS-Abgleich
- `DashboardWindow` - Hauptfenster mit UI
- `DecryptService` - Entschlüsselung von n8n-Daten
- `DatabaseService` - Datenbank-Zugriff
- `WorkflowService` - n8n-Integration

### Endpunkte (Single Point of Truth)
- Alle Endpunkte in `app/config/endpoints.py`
- `EndpointConfig.get_endpoint("key")` - Zugriff auf Endpunkte

---

## 🔍 Empfehlungen

1. **Löschen**: `monitoring_manager.py`, `webhook_service.py`, `search_worker.py`, `supabase_manager.py`, `__usage_example__.py`
2. **Prüfen**: `oss_schema_manager.py` (wird importiert aber nicht genutzt)
3. **Behalten**: `sync_jtl_to_n8n.py` (für manuelle Syncs nützlich)

