# Propuesta OpenSpec: Expansión de la Base de Procesos - Ciclo 29 (TASK-039)

- **Change ID**: `2026-10-01-process-db-expansion-c29`
- **Área**: Base de Datos & Procesos (Ciclo #29)
- **Agente responsable**: `process-db-updater`
- **Estado**: Implementado

---

## 1. Contexto y Justificación
La base de datos local `assets/process_db.json` contaba con 81 procesos catalogados desde el Ciclo #23.
Durante el escaneo continuo de procesos en el entorno host de Windows en el Ciclo #29, se identificaron nuevos ejecutables reales de servicios de juegos Xbox (GameInput, Xbox Gaming Services), sincronización de la nube (OneDrive/Office helpers, Adobe Collab Sync), superposiciones de navegadores (Edge Game Assist) y utilidades de automatización (HASS Agent).

## 2. Objetivos
1. Escanear los procesos vivos del sistema host con `psutil` y clasificarlos contra `SYSTEM_PROTECTED_PROCESSES` y `assets/process_db.json`.
2. Registrar 8 nuevos procesos reales en `assets/process_db.json` con descripciones precisas en español, prioridades y categorías canónicas de `config.py`.
3. Mantener el 100% de cumplimiento con `test_process_db_schema_integrity` y `test_category_emoji_alignment` en `run_tests.py` (89 procesos catalogados).

## 3. Procesos Añadidos (+8)
- `gamingservices`: 🟡 Launchers Gaming | low | Servicios centrales de la tienda Xbox y juegos en Windows.
- `gamingservicesnet`: 🟡 Launchers Gaming | low | Servicio de red auxiliar para juegos y tienda Xbox.
- `adobecollabsync`: 🟢 Productividad | medium | Sincronizador en segundo plano de documentos colaborativos de Adobe.
- `filecoauth`: 🟢 Sincronización | medium | Servicio de coautoría y sincronización de Microsoft Office.
- `filesynchelper`: 🟢 Sincronización | medium | Asistente auxiliar de sincronización de archivos de OneDrive.
- `edgegameassist`: 🟢 Navegadores | low | Asistente u overlay flotante de juegos integrado en Microsoft Edge.
- `hass.agent`: 🟢 Productividad | low | Agente de integración local para domótica con Home Assistant.
- `gameinputredistservice`: 🟡 Launchers Gaming | low | Servicio redistribuible de entrada de mandos Microsoft GameInput.

## 4. Invariantes
- **Blindaje anti-brick**: 0 solapamientos con `SYSTEM_PROTECTED_PROCESSES` (34 procesos de sistema protegidos).
- **Canonicidad**: Categorías estrictamente alineadas con `PROCESS_CATEGORIES` en `config.py`.
- **Suite de pruebas**: `test_process_db_schema_integrity` valida las 89 entradas.
