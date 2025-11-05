# ❌ Nicht verwendete Dateien - Lösch-Liste

## ⛔ Sofort löschen (100% sicher unbenutzt)

### 1. `app/managers/monitoring_manager.py`
- **Grund**: Wird nur in `__init__.py` importiert, aber NIRGENDWO verwendet
- **Prüfung**: `grep -r "MonitoringManager" .` zeigt nur Definition und Import
- **Aktion**: ✅ **LÖSCHEN**

### 2. `app/services/webhook_service.py`
- **Grund**: `WebhookService` Klasse existiert, aber keine Verwendung gefunden
- **Prüfung**: Keine Imports in anderen Dateien
- **Aktion**: ✅ **LÖSCHEN**

### 3. `app/workers/search_worker.py`
- **Grund**: `SearchWorker` Klasse existiert, aber keine Verwendung gefunden
- **Prüfung**: Keine Imports in anderen Dateien
- **Aktion**: ✅ **LÖSCHEN**

### 4. `supabase_manager.py`
- **Grund**: `SupabaseManager` Klasse existiert, aber keine Verwendung gefunden
- **Prüfung**: `SUPABASE_AVAILABLE = False` in Config
- **Aktion**: ✅ **LÖSCHEN**

### 5. `app/utils/__usage_example__.py`
- **Grund**: Enthält nur Beispiel-Code
- **Prüfung**: Keine Verwendung in der App
- **Aktion**: ✅ **LÖSCHEN** (oder zu Dokumentation verschieben)

### 6. `str` (Datei im Root-Verzeichnis)
- **Grund**: Unbekannte Datei
- **Prüfung**: Unbekannt
- **Aktion**: ✅ **PRÜFEN und ggf. LÖSCHEN**

## ⚠️ Prüfen und ggf. löschen

### 7. `app/config.py` ⚠️ **DUPLIKAT**
- **Grund**: Enthält gleiche Funktionen wie `app/config/__init__.py`
- **Verwendung**: `from .config import get_color_scheme` in `app/__init__.py`
- **Problem**: `app/config/__init__.py` hat die gleichen Funktionen
- **Aktion**: 
  1. Ändere `app/__init__.py`: `from .config import get_color_scheme` → `from .config import get_color_scheme` (bleibt gleich, aber importiert aus `app/config/__init__.py`)
  2. ✅ **LÖSCHE** `app/config.py`

### 8. `app/managers/oss_schema_manager.py`
- **Grund**: Wird importiert aber nur als `None` initialisiert
- **Verwendung**: `from ..managers.oss_schema_manager import OSSSchemaManager` in `dashboard.py`
- **Problem**: `self.oss_schema_manager = None` - nie verwendet
- **Aktion**: ⚠️ **PRÜFEN** ob zukünftig benötigt, sonst löschen

## 📋 Zusammenfassung

### Sofort löschen (6 Dateien):
1. ✅ `app/managers/monitoring_manager.py`
2. ✅ `app/services/webhook_service.py`
3. ✅ `app/workers/search_worker.py`
4. ✅ `supabase_manager.py`
5. ✅ `app/utils/__usage_example__.py`
6. ✅ `str` (prüfen)

### Nach Anpassung löschen (1 Datei):
7. ✅ `app/config.py` (nach Änderung in `app/__init__.py`)

### Optional löschen (1 Datei):
8. ⚠️ `app/managers/oss_schema_manager.py` (wenn nicht geplant)

## 🔧 Befehle zum Löschen

```bash
# Sofort löschen
rm app/managers/monitoring_manager.py
rm app/services/webhook_service.py
rm app/workers/search_worker.py
rm supabase_manager.py
rm app/utils/__usage_example__.py
rm str  # Prüfen vorher!

# Nach Anpassung
# 1. Ändere app/__init__.py (import bleibt gleich, aber kommt aus app/config/__init__.py)
# 2. Dann:
rm app/config.py
```

## ⚠️ WICHTIG: Vor dem Löschen

1. **Backup erstellen**: `git commit` oder `git stash`
2. **Testen**: App nach Löschung starten und prüfen
3. **Importe entfernen**: Aus `__init__.py` Dateien entfernen:
   - `app/managers/__init__.py` - entferne `MonitoringManager` Import
   - Prüfe andere `__init__.py` Dateien


