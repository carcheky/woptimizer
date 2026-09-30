# `docs/archive/legacy-root-data/` — datos y planes retirados de la raíz (TASK-028)

Nada de lo que hay aquí se ejecuta. Es un **registro**: ficheros que estaban en
la raíz del repositorio y que se retiraron en TASK-028 (FIX-015 y FIX-017) por
estar **muertos**, no por estar rotos. Se archivan y **no se borran**: la norma
del propietario es que nada de lo que existió se destruye sin más, así que aquí
está el contenido exacto con su historia escrita al lado.

Fecha del retiro: **2026-09-30**. Decide y audita: `architect-review`
(`openspec/changes/2026-09-30-task028-debt-cleanup/proposal.md` §6 y §8).

---

## 1. `profiles.json` (420 B) — esquema v2 muerto

**Qué es.** Un `profiles.json` del esquema legacy v2, con la raíz `profiles` y
un único preset de sistema:

```json
{"profiles": {"__system_gaming__": {"kind": "system", "label": "🚀 Preparar
 para Gaming", "keepers": ["discord"], "kill_low_chat": true,
 "factory": {…}}},
 "favorite": null}
```

**Por qué se retiró (medido, no supuesto).**

- El formato **vivo** es `{"packs": {…}}` con el modelo `Pack` de Pydantic v2
  (`docs/ai/data-models.md` §2, §3). Este fichero no tiene la clave `packs`.
- Sus claves (`__system_gaming__`, `kind`, `label`, `factory`, `kill_low_chat`)
  **no existen** en `models.py`, y **no tiene `is_gaming`**: sin ese campo el
  pack no se habría protegido nunca del borrado.
- `factory` duplicaba el preset dentro de sí mismo (esquemática de un esquema
  que ya no se usa).
- **El fichero que la app lee es otro:** `PROFILES_FILE` (`config.py`) sale de
  `_app_dir()`, que en modo desarrollo devuelve `dirname(config.py)`, o sea
  `src/woptimizer/profiles.json`. Un `grep` de `src/` no encuentra ninguna
  referencia a la raíz. Este fichero no lo abría nadie.

**Lo que NO se tocó y por qué** (FIX-011, veto explícito del arquitecto):

| Fichero | Decisión | Motivo |
|---|---|---|
| `test_profiles_task1.json` (raíz) | **Se queda** | Lo consume `verify_task1.py`: `:12` define `TEST_FILE = "test_profiles_task1.json"` y `:15` lo pasa a `PackService(data_path=TEST_FILE)`. **Está versionado**: borrarlo rompe ese script y es un cambio real de repo. *(Corrección TASK-028 iteración 2: este README decía "verificado en `verify_task1.py:12` → pasado a `PackService(data_path=.)`"; la instanciación es la línea **15** y recibe la **variable**, no un `.`.)* |
| `saved_processes.json` (raíz, 38 KB) | **Se queda** | Está en `.gitignore:8`: es estado local de **la máquina del usuario** (su historial de procesos), no un residuo del repositorio. Borrarlo sería tocarle el disco al usuario, no limpiar el repo. |

---

## 2. `inconsistencies_plan.md` (1.941 B) — plan "100% Completado" que ya no describe nada

**Qué es.** Un plan de inconsistencias redactado tras la implementación de v3 y
titulado *"Análisis Final Post-Implementación (100% Completado)"*.

**Por qué se archiva y no se borra (y por qué dejarlo en la raíz era un
problema).** El documento describe trabajo **ya hecho** y cita ficheros que ya
**no existen**:

- Habla de un `fallback.csv` con categorías de procesos. Hoy la fuente es
  `assets/process_db.json` (`docs/ai/data-models.md`, "Base de Datos de
  Procesos").
- Propone refactorizar `GamingService.should_kill_for_gaming` porque comparaba
  contra el string hardcodeado `'🟡 Chat y Comunicación'`. Eso lo cerró
  TASK-020.
- Propone "un `.gitignore` estricto" y "limpiar `build/` y `woptimizer.spec`":
  ambas cosas existen desde hace ciclos.

Es decir: **es engañoso**. En la raíz, junto a la documentación viva, se leía
como una lista de pendientes que nadie había hecho. Su valor real es el de un
**registro histórico de por qué se tomaron las decisiones** de TASK-020 y de la
introducción del `assets/process_db.json`. Para eso está aquí, con el contenido
**intacto**: no se le ha reescrito ni una línea.

---

## Cómo se restauraría algo de aquí

Nada de esto es un entregable ni un formato que el producto lea. Si algún día
hace falta el esquema v2 como referencia de una migración, está en este
directorio, con su contenido byte a byte. Si hace falta **datos**, no: este es
un fichero de 420 B con un preset de fábrica, no configuración de nadie.
