# TASK-076 — Una sola declaración de los flags de PyInstaller

> Decisión de diseño del `architect-review`, ciclo #65. **Nada de esto está implementado.**
> El encargo original ("desduplicar `force_build.py` contra `release.yml`") era
> **parcialmente falso**: esos dos ficheros ya son idénticos. La divergencia real
> estaba en los dos sitios que el encargo no miraba.

## 1. Premisas del encargo, medidas una a una

| Premisa de la `description` de TASK-076 | Veredicto | Evidencia |
|---|---|---|
| "los flags están duplicados entre `force_build.py` y `release.yml`" | **CIERTO en la forma, FALSO en el riesgo**: la copia existe, pero los dos ficheros son idénticos byte a byte | comparador sobre los tres ficheros: `force_build == release.yml` -> `True` |
| "si divergen, el binario de release difiere del compilado localmente" | **Condicional y hoy falso** entre esos dos; **VIVO en otros dos** | `build.bat:27` y `docs/ai/sandbox-rules.md:19-27` no llevan `--add-data` |
| "DEUDA DE STATUS.md (fila 120)" | **FALSA**: la seccion `## Deuda Tecnica Conocida` va de la 58 a la 88 y no tiene ninguna fila sobre flags | `STATUS.md:58-88` medido; ninguna mencion de `flag`/`onefile`/`add-data` |
| "unico fichero o especificacion `woptimizer.spec` compartida" | **IMPOSIBLE tal cual**: `woptimizer.spec` esta en `.gitignore:29` (`*.spec`), luego CI no lo tendria | `.gitignore:29`; no aparece en `git ls-files` |
| "verify_exe.py y smoke tests pasan sin discrepancias de empaquetado" | **CIERTO pero VACIO**: ninguno de los dos comprueba que el `.exe` lleve `assets/` | `grep assets\|ico\|MEIPASS` en ambos -> 0 coincidencias |

## 2. Inventario medido: hay CUATRO sitios, no dos

| # | Sitio | Fichero:linea | `--add-data` | ¿Versionado? |
|---|---|---|---|---|
| 1 | Declaracion ejecutable local | `force_build.py:11-16` | **si** | si |
| 2 | Declaracion ejecutable CI | `.github/workflows/release.yml:208` | **si** | si |
| 3 | Declaracion ejecutable local | `build.bat:27` | **NO** | si |
| 4 | Ejemplo de codigo en la doc | `docs/ai/sandbox-rules.md:19-27` | **NO** | si |
| -- | Autogenerado, no es fuente | `woptimizer.spec:8` (`datas=[('assets','assets')]`) | si | **NO** |

Lista de flags medida (orden incluido):

- `force_build.py` y `release.yml` -> `['--onefile','--noconsole','--uac-admin','--name','woptimizer','--clean','--add-data','assets;assets','src/woptimizer/__main__.py']` — **identicos**
- `build.bat` y el ejemplo del doc -> la misma **menos** `'--add-data','assets;assets'`

**Solo en uno de los dos lados del encargo: ninguno.** La asimetria esta en los sitios 3 y 4, que el encargo no nombra.

## 3. Que lado manda, y por que (no por simetria)

Manda el lado **con `--add-data`**, y la razon esta medida en el codigo, no en la opinion:

- `src/woptimizer/config.py:11-14` — `_data_dir()` devuelve **`sys._MEIPASS`** cuando `sys.frozen` es verdad. O sea: los assets embebidos **si** se leen, y se leen de la extraccion temporal del `.exe`.
- `src/woptimizer/services/process_service.py:347` — lee `_data_dir()/assets/process_db.json` (**49 517 B**, 73 entradas).
- `src/woptimizer/ui/app.py:23` y `:269` — leen `_data_dir()/assets/woptimizer.ico`.

Sin `--add-data assets;assets` el `.exe` de `build.bat:27` arranca **sin base de datos de procesos y sin icono**. El `.exe` que publica GitHub Actions (`release.yml:208`) si los lleva. El `.exe` roto es el local, no el publicado. **El producto de `release.yml` es el bueno.**

## 4. Que pasa con `woptimizer.spec`: cambia la estrategia

`woptimizer.spec` existe, tiene `datas=[('assets','assets')]` y `uac_admin=True`, pero:

1. esta en `.gitignore:29` (`*.spec`) y **no aparece en `git ls-files`**: es un artefacto que PyInstaller regenera en cada build.
2. el job `build` corre `actions/checkout` + `pip install -e ".[dev]"`: si `release.yml` pasara `--spec woptimizer.spec`, el runner no tendria el fichero y el build **se romperia en produccion**.
3. `run_tests.py:6444-6447` lo recorre con `continue` si no existe, luego esa rama **no corre en CI** (el runner no lo tiene). Medir el `.spec` es medir un residuo local.

**Conclusion: el `.spec` no es la fuente de verdad y no puede serlo sin quitar `*.spec` del `.gitignore`.** La estrategia correcta es la que hace imposible tener dos listas, no la que las compara.

## 5. Decision de diseno

**Fuente unica: `force_build.py`.** Los otros tres sitios **dejan de declarar flags**:

1. `release.yml:208` -> `python force_build.py`
2. `build.bat:27` -> `python force_build.py`
3. `docs/ai/sandbox-rules.md:19-27` -> el ejemplo pasa a remitir a `force_build.py` en vez de re-listar los flags

Por que esto y no "un `build_flags.py` compartido":

- **Borrar la segunda lista** es lo que hace imposible la divergencia. Un modulo con `FLAGS = [...]` que los dos importan sigue dejando **dos listas de flags en dos ficheros**, y el test que las compara es exactamente el tautologo que el encargo pide evitar: si uno copia del otro, la igualdad se cumple sola.
- `force_build.py` ya es el builder nativo sincrono que exige `sandbox-rules.md` §2, ya usa `sys.executable -m PyInstaller` (que es justo el bypass de `spawn EPERM`), y ya lo invoca el checkpoint del skill (`.agents/skills/id-pipeline/SKILL.md:293`).
- El job `build` corre en `windows-latest` (`release.yml:184`), hace `pip install -e ".[dev]"` (que instala `pyinstaller>=6.0`) y el checkout incluye `force_build.py`. La invocacion es viable.

**Consecuencia sobre el test pedido.** Ya no hay "dos listas que comparar": hay **una declaracion y tres consumidores**. El test de paridad se reescribe como **guard de unicidad** (que nadie reintroduzca una segunda declaracion) + **guard de cobertura** (que la unica declaracion empaquete lo que la app lee). El segundo es el que discrimina de verdad, porque su expectativa sale de `src/` y no de `force_build.py`.

## 6. Restricciones medidas que el implementador tiene que respetar

1. **SIN PyYAML.** `pyproject.toml:15-19` solo declara `pytest` y `pyinstaller`. Un guard que haga `yaml.safe_load(release.yml)` **funciona en el host y falla en CI** con `ModuleNotFoundError`. Los guards leen **texto**, nunca parsean YAML.
2. **`sandbox-rules.md:55-56`**: la trampa es de honestidad documental, no de rojo. MEDIDO: `_declara_el_codigo_sobrecargado` (`validate_docs.py:1935`) compila el patron con `re.MULTILINE` sobre el **cuerpo entero**; no cita numeros de linea. Desplazar la tabla **no rompe el validador**, lo que se rompe es que las afirmaciones que la citan queden mintiendo: `validate_docs.py:1429`, `validate_docs.py:1924`, `run_tests.py:22264`, `docs/ai/sandbox-rules.md:1133`. Si la edicion del bloque de flags (lineas 16-32) cambia el recuento de lineas, **hay que actualizar las cuatro citas a la vez**. Forma segura: sustituir en el sitio sin cambiar el numero de lineas.
3. **`run_tests.py:22262`** exige `min(posiciones) > 61` para la seccion *"Por que el validador NO corre en CI"*. No se inserta nada por encima de la 61 en `sandbox-rules.md`.
4. **Prohibido escribir semver o palabras de version en `force_build.py` y `build.bat`.** `run_tests.py:6442-6456` (M7/M9/M10) escanea `("woptimizer.spec","build.bat","force_build.py")`, busca un token `\bver\b|\bversions?\b|__version__|--version` **y** un literal `\d+\.\d+\.\d+`, y falla si no coinciden con `3.0.1.dev0`. Comentarios como "flags v1.2.3" tumban la suite.
5. **`STATUS.md:87` (deuda D3)** declara `release.yml` con 193 lineas; tiene 214. La implementacion vuelve a cambiar el numero -> D3 se corrige con la cifra **medida** al cerrar, no antes.
6. **`validate_docs.py` no menciona `release.yml`** en ninguna linea: cambiar el workflow no rompe el validador.
7. **No se ejecuta `force_build.py`** desde un test. La suite es headless y el sandbox bloquea subprocesos (`run_tests.py:854-859` ya degrada con `AVISO`). El smoke test de compilacion es el checkpoint del skill, no un test.

## 7. Lo que este cambio NO arregla (y no se dresses de mas)

- El `.exe` local compilado con `build.bat` **antes** de este cambio ya existe en `dist/` y sigue sin assets hasta que se recompile. El guard lo detecta en el codigo, no repara un binario viejo.
- La descarga de `process_db.json` por red (`process_service.py:378-394`) puede enmascarar el symptoms: sin assets, la DB se recupera del remoto si hay red. El primer arranque sin red es el caso roto, y el icono no se recupera nunca.
- `woptimizer.spec` seguira apareciendo en el arbol del dueno como residuo. No se borra en este ciclo: `run_tests.py:6444` lo recorre y `openspec/changes/2026-09-28-v3-rewrite-phase1/tasks.md:28` ya lo dio por muerto sin cerrarlo.