# Propuesta OpenSpec: Expansión y Actualización de la Base de Procesos (TASK-032)

- **Change ID**: `2026-09-30-process-db-expansion`
- **Área**: Base de Datos & Procesos (Ciclo #23)
- **Agente responsable**: `process-db-updater`
- **Estado**: Propuesto

---

## 1. Contexto y Justificación
La base de datos local `assets/process_db.json` contiene actualmente 73 procesos clasificados con su nivel de seguridad y recomendación de cierre.
La última actualización de la base ocurrió en el Ciclo #13 (hace 9 ciclos).
Durante las sesiones de uso y pruebas de woptimizer en sistemas Windows reales, nuevos procesos de fondo, servicios de telemetría, utilidades OEM y aplicaciones habituales pueden estar en ejecución sin metadatos conocidos, mostrándose como `⚪ Otros` o `Sin descripción`.

## 2. Objetivos
1. Escanear los procesos vivos del sistema mediante `psutil` en el entorno Windows host.
2. Cruzar los nombres de ejecutables con las 73 entradas de `assets/process_db.json`.
3. Filtrar de forma irrenunciable cualquier proceso perteneciente al núcleo del sistema operativo o hardware (`SYSTEM_PROTECTED_PROCESSES` en `process_service.py:33-48`). Ningún proceso crítico del sistema puede ser catalogado como cerrable.
4. Identificar bloatware real, herramientas secundarias y launchers no registrados.
5. Asignar categorías canónicas de `config.py` con exactitud de caracteres Unicode y emojis.
6. Actualizar `assets/process_db.json` preservando la sintaxis JSON válida y documentando las decisiones de inclusión y descarte.

## 3. Invariantes
- **Blindaje anti-brick**: Cero procesos de sistema registrados como cerrables. Cero solapamientos con `SYSTEM_PROTECTED_PROCESSES`.
- **Canonicidad de categorías**: Usar estrictamente las categorías de `config.CATEGORY_ORDER`.
- **Integridad de servicios**: Cero modificaciones en `src/woptimizer/` durante la actualización de datos.
