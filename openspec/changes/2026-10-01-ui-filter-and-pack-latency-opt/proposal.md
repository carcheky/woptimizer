# Propuesta OpenSpec: Optimización de Latencia en Filtro de Búsqueda y Lectura de Packs (TASK-040)

- **Change ID**: `2026-10-01-ui-filter-and-pack-latency-opt`
- **Área**: Rendimiento & Latencia (Ciclo #30)
- **Agente responsable**: `openspec-dev`
- **Estado**: Propuesto

---

## 1. Contexto y Justificación
Durante el uso de woptimizer con listas grandes de procesos activos (300+ ejecutables) en `ProcessManagerView`, la filtración de la búsqueda al escribir en la caja de texto vuelve a formatear y ordenar todas las filas de UI.
Asimismo, `PackService.get_all_packs()` realiza copias profundas `model_copy(deep=True)` continuas para evitar mutaciones directas sobre el estado persistido.
Optimizar la velocidad de filtrado de búsqueda y el rendimiento de consulta de packs reducirá el tiempo de respuesta visual de la UI de ~15-20 ms a < 2 ms.

## 2. Objetivos
1. **Filtro Pre-tokenizado en `ProcessManagerView`**:
   - Pre-computar cadenas de búsqueda en minúsculas para comparaciones `O(1)` / instantáneas en `_on_search_changed`.
   - Evitar recreación redundante de listas de procesos cuando el término de búsqueda no cambia o se borra.
2. **Caché Eficiente de Packs en `PackService`**:
   - Evitar `deep_copy` innecesarios en lecturas de solo consulta cuando el objeto no ha sido modificado, e invalidar la caché inmediatamente en operaciones de mutación (`save`, `create`, `delete`, `set_favorite`).
3. **Pruebas de Benchmark Headless en `run_tests.py`**:
   - Añadir tests discriminantes comprobando la latencia de filtrado (< 2 ms) e invalidación de caché de packs.

## 3. Invariantes
- **Imputabilidad y Thread Safety**: Ninguna mutación accidental del pack en memoria debe contaminar el estado persistido (`DEFAULT_GAMING_PACK` u otros perfiles).
- **Separación de Capas**: `ProcessManagerView` no accede a `psutil` ni a disco en el hilo principal.
