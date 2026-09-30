# Cierre de los supervivientes del ciclo 21 (TASK-028 iteracion 2) — plan de ejecución

Diseño completo en [`proposal.md`](proposal.md). Tarea propia: **no reutiliza TASK-028** (que queda
`completed`). Ficheros tocables: `run_tests.py`, `src/woptimizer/config.py`,
`docs/ai/*.md`, `docs/archive/legacy-root-data/README.md`, el `proposal.md` de TASK-028 (D2) y el
`.gitignore` **solo para leerlo**. Nada más.

Orden de ejecución = orden de prioridad del encargo. Los cinco primeros son el mínimo entregable.

---

## BLOQUE 1 — crítico (M12, M7, M4/M4b, D1, D2)

- [ ] **N1** `run_tests.py`: `test_el_archivo_legacy_esta_versionado_y_no_vuelve_a_la_raiz`
      (M12 + M13 + M14 + M15). Entorno de git igual que `git_safe_commit.get_env()`;
      `check-ignore -q --no-index`; `ls-files --error-unmatch`; control negativo con
      `saved_processes.json`.
- [ ] **N2** `run_tests.py`: ampliar `test_la_consulta_de_version_no_puede_desincronizarse` con
      `.taskmaster/tasks.json` (M7), el filtro de dos condiciones del escáner de empaquetado (M9) y
      el escáner de `src/` (M10). Sin tocar `pyproject.toml` ni `__init__.py`.
- [ ] **N3** `run_tests.py`: `test_el_punto_de_entrada_declara_el_log_antes_de_los_servicios`
      (M4/M4b). AST de `__main__.py`; **no** ejecutar `main()` (arrancaría la UI).
- [ ] **D1** `src/woptimizer/config.py:68-71`: corregir el comentario de `PROCESS_LIST_FILE`.
      Decir que `smoke_check.py` **muere en `:8`** con `FileNotFoundError` y nunca alcanza su
      línea 23; los consumidores vivos son los 3 tests del root (FIX-014).
- [ ] **D2** `openspec/changes/2026-09-30-task028-debt-cleanup/proposal.md` §12 criterio 3:
      marcarlo muerto por escrito y sustituirlo por el criterio cumplible.

## BLOQUE 2 — media (M18, M11/M10a-c, M13-M15, M3b, M16)

- [ ] **N4** `run_tests.py`: `test_process_list_file_sigue_siendo_un_contrato` (M18).
      Existencia + valor leído del módulo + los 3 consumidores nombrados en su AST.
- [ ] **N5** `run_tests.py`: `test_la_documentacion_del_blindaje_no_puede_desfasarse`
      (M10a/M10b/M10c/M11). Expectativa derivada del **código** con `ast`.
- [ ] **N6** `run_tests.py`: `test_el_log_rota_con_el_limite_declarado` (M3b).
      `type(h) is RotatingFileHandler` + `maxBytes`/`backupCount` contra las constantes.
- [ ] **N7** `run_tests.py`: `test_config_no_configura_nada_al_importarse` (M16).
      AST de `config.py` + control que demuestra que el detector sí encuentra `basicConfig`.
- [ ] Registrar N1-N7 en el `__main__` de `run_tests.py` (FIX-014: toda prueba nueva es una función
      aquí, nunca un `test_*.py` nuevo en la raíz).

## BLOQUE 3 — baja (M9 ya cerrado en N2, D3, D4, deuda)

- [ ] **D3** `docs/archive/legacy-root-data/README.md:44`: `verify_task1.py:12` define
      `TEST_FILE`; la instanciación es `verify_task1.py:15` con `PackService(data_path=TEST_FILE)`.
- [ ] **D4** `docs/ai/architecture.md` §11 y `docs/ai/data-models.md`: `is_system_protected` es un
      `@staticmethod` de `ProcessService` (`process_service.py:330-336`), no una función de módulo.
- [ ] **Deuda anotada, no cerrada (M10 como categoría):** un sitio de versión en un fichero de
      empaquetado fuera de la lista, o un literal semver en un `.bat`/`.spec` sin token de versión
      al lado, queda fuera del alcance. Se deja escrito en `docs/ai/testing-guide.md` con lo que sí
      se cubre.

## BLOQUE 4 — documentación y verificación

- [ ] `docs/ai/architecture.md` §15: nombre las sondas N3, N6, N7 (invariantes ya declarados que
      hasta ahora nadie comprobaba).
- [ ] `docs/ai/data-models.md`: la transcripción de los 34 nombres y el rango pasan a ser
      **contrastados** por N5 (declarar quién los mide, no solo afirmarlos).
- [ ] `docs/ai/testing-guide.md`: tabla de sondas de este ciclo + **M17a/M17b como mutantes
      EQUIVALENTES** (no "sin cobertura": no hace falta).
- [ ] Verificar cada sonda muerta con su mutación en `%TEMP%`, purgando `__pycache__` entre
      mutaciones. Tabla mutación→muerte en el informe.
- [ ] `python run_tests.py`, `python verify_ui_syntax.py`, `python validate_docs.py` en verde.
- [ ] `python .taskmaster/git_safe_commit.py "test(task028): cerrar supervivientes del ciclo 21"`
      con salida **0**.

## Fuera de alcance (NO tocar)

- `TASK-028` en `.taskmaster/tasks.json`: se queda `completed`. Solo se lee su `version`.
- `rd_journal.json`, `CHANGELOG.md`, `.taskmaster/CHANGELOG.md`, `STATUS.md`: los escribe el
  orquestador.
- `.gitignore`: **leer**, no editar. Si la línea 13 fuera necesaria, eso se reporta, no se arregla
  aquí.
- FIX-013 (migración del CSV): sigue bloqueada.
