# Tareas de implementacion — TASK-076

Estado: **planificado, no implementado**. El ejecutor es `openspec-dev`.
Nada de esto se ejecuta hasta que el arquitecto dé el visto bueno (ya dado).

## Orden de ejecucion

### T-1 · Una sola declaracion de flags (AC-1)

- [ ] `release.yml:208`: sustituir la llamada directa por `python force_build.py`.
      El nombre del paso puede pasar a "Compilar el ejecutable" (el worktree ya
      esta en el tag, `release.yml:192-194`). Sin tocar ninguna otra linea.
- [ ] `build.bat:27`: sustituir `pyinstaller --onefile ... --clean src/...` por
      `python force_build.py`. **Mantener `python` delante**: en Windows, `force_build.py`
      a secas no se ejecuta.
- [ ] `build.bat` conserva el paso 2 (limpiar `build/` y `dist/`): es comportamiento,
      no declaracion de flags. `force_build.py` usa `--clean`, que limpia la cache de
      PyInstaller pero **no** borra `dist/` a pelo.

### T-2 · El ejemplo del doc deja de re-listar los flags (AC-3)

- [ ] `docs/ai/sandbox-rules.md:19-27`: el bloque de ejemplo pasa a remitir a
      `force_build.py` (los flags viven ahi; aqui se explica **por que** se compila
      asi y **por que** el bypass de shell).
- [ ] **Sin anadir ni quitar lineas** en `sandbox-rules.md` por encima de la 61.
      Si el recuento cambia por necesidad, actualizar **a la vez** las cuatro citas:
      `validate_docs.py:1429`, `validate_docs.py:1924`, `run_tests.py:22264`,
      `docs/ai/sandbox-rules.md:1133`. Y `run_tests.py:22262` (`min(posiciones) > 61`).
- [ ] `docs/ai/sandbox-rules.md:32` dice "Debe incluir el flag `--uac-admin`": se
      conserva el requisito, se anade el de `--add-data` con la razon de `config.py:11-14`.
- [ ] `docs/ai/release-pipeline.md:87` y `docs/ai/architecture.md:8`: el job `build`
      ya no invoca PyInstaller directamente; que lo digan.

### T-3 · Guard de unicidad (AC-1) — el que reemplaza al "test de paridad"

- [ ] En `run_tests.py`, test nuevo que falle si **alguien vuelve a declarar flags**
      fuera de `force_build.py`:
      - `release.yml` no contiene ningun literal de flag (`--onefile`, `--noconsole`,
        `--uac-admin`, `--add-data`, `--name`, `--clean`) **ni** `-m PyInstaller`,
        y si llama a `force_build.py`.
      - `build.bat` igual, y con `python ` delante.
      - `sandbox-rules.md` no vuelve a listar flags como codigo ejecutable.
      - Ninguno de los tres pasa `--spec`.
- [ ] Lectura por **TEXTO**, nunca `yaml.safe_load`: no hay PyYAML en las dev deps.

### T-4 · Guard de cobertura de assets (AC-2) — el que discrimina de verdad

- [ ] Test que **escanea `src/woptimizer/**/*.py`**, recoge cada ruta relativa bajo
      `assets/` que la app lee (`process_service.py:347`, `app.py:23`, `app.py:269`),
      y exige que la declaracion de `force_build.py` empaquete ese destino.
      La expectativa sale de `src/`, no de `force_build.py`: por eso no es tautologica.
- [ ] Sin subprocesos: todo regex sobre texto.

### T-5 · Guard de las citas por linea (AC-4)

- [ ] Test que verifique que las afirmaciones que citan `sandbox-rules.md:55-56`
      **siguen siendo ciertas hoy**, en vez de dejar que se pudran en silencio.
      MEDIDO: `_declara_el_codigo_sobrecargado` no cita lineas (`re.MULTILINE` sobre
      el cuerpo), asi que el riesgo no es rojo, es mentira documental.

### T-6 · Cierre documental

- [ ] `STATUS.md:37`: la fila de TASK-076 pasa a `completed` con su ancla.
- [ ] `STATUS.md:87` (D3): corregir el numero de lineas de `release.yml` con la cifra
      **medida** tras el cambio.
- [ ] `.taskmaster/tasks.json`: `"status": "completed"` en TASK-076.
- [ ] Changelogs en los dos ficheros (`CHANGELOG.md` y `.taskmaster/CHANGELOG.md`).
- [ ] Journal: `.taskmaster/rd_journal.json`.

## Fuera de alcance (deliberadamente)

- No se versiona `woptimizer.spec`, ni se quita `*.spec` de `.gitignore`.
- No se ejecuta `force_build.py` ni se compila. El smoke test de compilacion es el
  checkpoint del skill (`SKILL.md:293`), no un paso de este cambio.
- No se toca `src/woptimizer/**`.

## Pendiente para el orquestador

- **Checkpoint de empaquetado**: el skill pide un smoke test de `force_build.py` cada
  3 ciclos. El ultimo documentado es anterior al ciclo #62 y con el #64 ya se cumple.
  Corresponde al orquestador **antes de cerrar el #65**, y este cambio lo hace mas
  barato: `build.bat` y CI compilan ahora el mismo camino, asi que un fallo se ve en
  los dos sitios a la vez.