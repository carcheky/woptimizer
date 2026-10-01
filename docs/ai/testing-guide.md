# Guía de Pruebas y Validación para Agentes IA

## Desafío en Entornos Headless
En muchos entornos de IA no existe un monitor o display activo de Windows conectado directamente al proceso del agente. Si un script ejecuta `app.mainloop()` de CustomTkinter, el script se quedará bloqueado de forma indefinida esperando interacción humana.

## Patrones de Prueba Obligatorios

### 1. Validación Estática de Sintaxis e Imports (`py_compile`)
Antes de dar por terminada cualquier edición de UI o servicios, compilar los archivos a bytecode:
```python
import py_compile
py_compile.compile('src/woptimizer/ui/app.py', doraise=True)
py_compile.compile('src/woptimizer/models.py', doraise=True)
```

### 2. Prueba de Inicialización Headless de la UI
Para verificar que los widgets cargan y los componentes se instancian sin errores de runtime:
```python
app = WOptimizerApp(process_service, pack_service, gaming_service)
# Programar cierre automático tras 1000ms para no bloquear la consola
app.root.after(1000, app.root.destroy)
app.run()
```

### 3. Pruebas Unitarias de Backend
Probar `process_service` y `pack_service` con tests independientes en `run_tests.py` sin levantar Tkinter.

#### Suite de Tests Actual (`run_tests.py`)
Ejecutar con `python run_tests.py` (PowerShell: `$env:PYTHONIOENCODING="utf-8"`). Contiene **91 tests**: 84 de backend + 7 headless de UI, numerados aquí en el **orden de registro** del `__main__` (los headless van al final).

> **Ese 81 no se escribe a mano, y por eso ya no puede caducar solo.** Fallo medido en el cierre
> del ciclo 26: esta tabla decía 78, `STATUS.md` decía 75 y `AGENTS.md` y `README.md` decían 28 —
> y `validate_docs.py` corría 72 comprobaciones **ninguna** de las cuales miraba un número de
> tests, así que informaba "72 OK, 0 FAIL" con los tres ficheros caducados. Es la clase "el
> validador deduce de lo que valida" que este repo ya sufriría dos veces. Desde la iteración 7,
> `validate_docs.py` deriva el número **con `ast`** —los `def test_*` de módulo y las llamadas
> del `__main__`—, exige que `defined == invoked` (un test definido y no invocado pasa en verde
> porque no corre nunca), lo compara con `STATUS.md`, `AGENTS.md`, `README.md` **y con el número
> de filas de esta tabla**. Si añades un test y no lo declaras, el validador falla; si el patrón
> de un fichero cambia y el validador ya no encuentra lo que debe leer, también falla en vez de
> dar verde por omisión.

| # | Test | Qué valida |
|---|------|-----------|
| 1 | `test_models` | Instanciación de `ProcessInfo`, `Pack`, `AppData` y valores por defecto Pydantic |
| 2 | `test_process_service_signatures` | `kill_processes` y `kill_pack_apps` retornan 4-tupla `(killed, failed, skipped, freed_mb)` |
| 3 | `test_freed_mb_return_type` | `freed_mb` es `float >= 0.0` en todos los casos (vacío, inexistente) |
| 4 | `test_gaming_pack_protected` | `delete_pack("gaming")` lanza `ValueError` — invariante de pack protegido |
| 5 | `test_corrupted_json_recovery` | JSON corrupto **sin** `.bak` → auto-recovery con pack gaming restaurado |
| 6 | `test_notification_without_tray_degrades` | Sin bandeja: `notify()` retorna `False` y no lanza; contadores de descartes |
| 7 | `test_notification_attach_detach` | `attach_tray` habilita, `detach_tray` deshabilita y es idempotente |
| 8 | `test_notification_never_raises` | Un backend que explota se degrada a log, nunca rompe la UI |
| 9 | `test_notification_message_formatting` | Helpers en español con plurales correctos y MB condicionales |
| 10 | `test_category_emoji_alignment` | Toda categoría de `assets/process_db.json` existe literalmente en `config.py` |
| 11 | `test_process_db_schema_integrity` | **TASK-032 (S1):** esquema estricto de `assets/process_db.json` (claves en minúsculas sin `.exe`, `category` en `PROCESS_CATEGORIES`, `priority` en `{"high","medium","low","none"}` y `description` no vacía) |
| 12 | `test_safety_badge_category_priority_order` | La categoría manda sobre la prioridad en `get_safety_badge` (regresión 🟡/🔴) |
| 13 | `test_gaming_service_should_kill` | Orden de reglas de `should_kill_for_gaming`: keeper > apps > categoría objetivo |
| 14 | `test_execute_gaming_pack_integration` | G0-G9 de `execute_gaming_pack`: barrera roja, keepers y kill recursivo real |
| 15 | `test_gaming_service_session_restoration` | **TASK-038:** restauración inteligente de apps tras Modo Gaming (`_last_closed_apps`, `get_last_closed_apps`, `clear_last_closed_apps`, `restore_gaming_session`) |
| 16 | `test_pack_service_crud` | `create_user_pack` rechaza duplicados y el id reservado `gaming`; persiste en disco |
| 16 | `test_pack_service_delete` | `delete_pack`: `ValueError` en gaming, `False` si no existe, `True` en pack propio |
| 17 | `test_pack_service_favorite_exclusive` | `set_favorite` deja como máximo 1 favorito; `set_favorite(None)` deja 0 |
| 18 | `test_pack_service_reset_gaming` | `reset_gaming_pack` restaura apps y `target_categories` de `DEFAULT_GAMING_PACK` |
| 19 | `test_gaming_pack_lists_isolated_from_global` | Las listas del pack gaming **no** comparten objeto con `DEFAULT_GAMING_PACK` (regresión de `model_copy()` shallow) |
| 20 | `test_cache_ttl_and_invalidation` | Dentro del TTL se devuelve el **mismo objeto**; `invalidate_cache()` y `force_refresh=True` re-escanean |
| 21 | `test_kill_recursive` | Kill recursivo: el nieto Python muere junto al padre (invariante de AGENTS.md) |
| 22 | `test_git_safe_commit_fail_safe` | Códigos de salida 0/1/2/3 y línea canónica `WOPT_*` de `git_safe_commit.py` |
| 23 | `test_double_tap_guard` | `DoubleTapGuard` exige segunda pulsación, con auto-revert y token de intención |
| 24 | `test_no_system_process_is_killable` | Blindaje anti-brick: ningún proceso de Familia A es cerrable por JSON, servicio ni kill |
| 25 | `test_gaming_pack_fallback_is_deep_copy` | **TASK-026 (FIX-001):** el *fallback* de `get_gaming_pack()` (con `gaming` borrado) copia `apps`/`keepers`/`target_categories` en profundidad |
| 26 | `test_default_meta_matches_canonical_otros` | **TASK-026 (FIX-005):** el centinela `⚪ Otros` (U+26AA) coincide con `CATEGORY_ORDER[-1]` y con el default de `ProcessInfo`, resuelve al último índice del orden, y los **tres** sitios de código usan el literal canónico |
| 27 | `test_pack_service_backup_and_recovery` | **TASK-026 (FIX-009):** rotación real del `.bak`, recuperación desde `.bak` con JSON corrupto, y un error de permisos no borra la configuración |
| 28 | `test_do_load_publica_sin_tk` | **TASK-026 (FIX-007) + TASK-030 (P8):** `_do_load` publica desde el hilo principal, con un arnés **sin Tk**; identidades de hilo, camino de crash y guarda `ast` |
| 29 | `test_save_atomic_nunca_toca_el_principal` | **TASK-030 (P1):** el volcado va a un temporal y, si se corta, el principal conserva sus bytes |
| 30 | `test_publicar_no_trunca_el_principal` | **TASK-030 (P1b):** publicar no usa un primitivo de copia (que trunca el destino) |
| 31 | `test_save_no_escribe_si_la_rotacion_no_puede_leer` | **TASK-030 (P2):** un `OSError` de lectura no se convierte en "sigo y sobrescribo" |
| 32 | `test_corrupcion_sin_backup_intenta_volar` | **TASK-030 (P3):** la regeneración llega a volcar (espía de `json.dump`, no de `save()`) |
| 33 | `test_forma_legacy_no_tumba_la_app` | **TASK-030 (P4):** `{"profiles": "texto"}` no tumba la app; solo la forma validada es corrupción |
| 34 | `test_todas_las_clases_de_corrupcion_se_recuperan` | **TASK-030 (P5):** tabla de las 4 clases de `CORRUPTION_ERRORS`, fila a fila |
| 35 | `test_oserror_de_lectura_no_es_corrupcion` | **TASK-030 (P6):** un `OSError` de lectura se propaga y no toca el `.bak` |
| 36 | `test_attribute_error_ajeno_no_es_corrupcion` | **TASK-030 (P7):** un `AttributeError` que no sea el deliberado se propaga |
| 37 | `test_la_rotacion_usa_la_misma_puerta_que_load` | **TASK-031 (L1):** la rotación usa `_read_json` y el `.bak` sano sobrevive a un `save()` real (mata L-M1) |
| 38 | `test_la_hoja_malformada_se_clasifica` | **TASK-031 (L2):** 6 hojas × 2 ramas se clasifican como corrupción, y el mensaje dice campo + pack + tipo real (mata L-M2) |
| 39 | `test_load_no_escribe` | **TASK-031 (L3):** `load()` no llama a `save()` en ninguna rama y no cambia ni un byte (mata L-M3) |
| 40 | `test_la_recuperacion_no_sobrescribe_el_bak` | **TASK-031 (L4):** recuperar no refresca el `.bak` byte a byte (mata L-M4) |
| 41 | `test_sin_bak_legible_no_se_sobrescribe_el_principal` | **TASK-031 (L5):** sin `.bak` el fichero se queda en disco y el pack queda marcado como dañado (mata L-M5) |
| 42 | `test_un_campo_desconocido_no_es_corrupcion_y_no_se_borra` | **TASK-031 (L6):** `notas` no es corrupción y sobrevive al `save()` (mata L-M6; separa la opción (a) de la (b)) |
| 43 | `test_packs_y_profiles_a_la_vez_es_corrupcion` | **TASK-031 (L7):** las dos claves a la vez se clasifican nombrándolas y ningún pack desaparece (mata L-M7) |
| 44 | `test_la_raiz_mal_escrita_no_destruye_los_packs` | **TASK-031 (L8):** una raíz sin clave válida no es corrupción ni borra los packs del usuario |
| 45 | `test_un_error_de_escritura_no_es_un_campo_desconocido` | **TASK-031 (L9):** un `OSError` al escribir no se clasifica como "campo desconocido" |
| 46 | `test_la_clave_del_mapa_es_la_identidad_del_pack` | **TASK-031 (L10):** la clave del mapa es la identidad del pack, no un campo libre |
| 47 | `test_la_raiz_legada_conserva_sus_claves_extra` | **TASK-031 (L11):** la raíz legacy conserva sus claves extra tras un `save()` real |
| 48 | `test_una_clave_raiz_nunca_es_un_error_de_escritura` | **TASK-031 (L12):** una clave raíz nunca es un error de escritura |
| 49 | `test_arranque_de_apps_no_usa_shell` | **TASK-027 (FIX-003):** arrancar una app no es ejecutar un comando: sin `Popen`, sin intérprete, contador honesto, log del motivo, guarda `ast` |
| 50 | `test_un_junction_no_puede_colar_lo_que_hay_detras` | **TASK-027 iter 2:** un junction/enlace **real** cuyo destino cae fuera de las raíces se rechaza, un `.exe` que apunta a un `.bat` se rechaza, y los dos controles positivos (enlace **dentro** de una raíz) arrancan |
| 51 | `test_la_contencion_no_acepta_un_hermano_de_prefijo` | **TASK-027 iter 2 (M10):** la contención es por componentes, no por prefijo de cadena (mata el `startswith`) |
| 52 | `test_la_contencion_no_depende_de_la_caja` | **TASK-027 iter 2:** `C:\PROGRAM FILES\...` está dentro de `C:\Program Files` en las dos direcciones, y fuera sigue siendo fuera |
| 53 | `test_la_guarda_de_shell_true_ve_atributos_y_aliases` | **TASK-027 iter 2:** la guarda anti-`shell=True` ve `ast.Attribute` y los alias de import, y no marca `shell=False` |
| 54 | `test_un_hard_link_no_es_una_hoja_y_el_script_no_pasa` | **TASK-027 iter 3:** un hard link real a un `.bat` de fuera y una **copia plena** del mismo `.bat` no arrancan (la regla es el **contenido**, `_es_imagen_pe`, no `st_nlink`); `MZ` sin `PE\0\0` y un `e_lfanew` absurdo tampoco; fail-closed; y un `.exe` **instalado** con `st_nlink > 1` **sí** arranca, que es lo que prohíbe la "solución" de rechazar todo enlace duro |
| 55 | `test_el_gestor_guarda_la_ruta_absoluta` | **TASK-027 (FIX-003, escritor):** lo que se guarda en `Pack.apps` es la ruta absoluta, con degradación a `full_name` |
| 56 | `test_orden_de_categorias_no_es_alfabetico` | **TASK-027 (FIX-004):** el orden es `CATEGORY_ORDER`, no el de `sorted()` sobre cadenas con emoji |
| 57 | `test_toggle_favorite_desmarca` | **TASK-027 (FIX-006):** la segunda pulsación de la estrella desmarca el favorito |
| 58 | `test_logging_va_a_fichero_y_no_a_stderr` | **TASK-028 (FIX-010):** el aviso acaba DENTRO de `woptimizer.log` y **no** en `stderr` (afirma sobre contenido y con el control negativo del `StreamHandler` sembrado: mata la implementación sin `force=True`) |
| 59 | `test_la_consulta_de_version_no_puede_desincronizarse` | **TASK-028 (FIX-018):** `pyproject.toml`, `__init__.py` y `tasks.json` declaran la **misma** versión, y no puede existir un cuarto sitio (escáner de `src/` con expectativa derivada del código) |
| 60 | `test_el_archivo_legacy_esta_versionado_y_no_vuelve_a_la_raiz` | **TASK-028 iter 2-5:** el archivo de `docs/archive` está versionado, completo y **sin volver ni a la raíz ni a la ruta viva que lee la app** (`_app_dir()`), por la **firma del esquema v2** (`profiles` + **dos** rasgos en el mismo registro). **Iter 5 (F1):** la ruta viva **ilegible da aviso, no muerte**, y eso se **afirma** con un control que escribe los tres ficheros de verdad (no-UTF8, truncado a mitad de un emoji de 4 B, `PermissionError` real) y exige el **motivo por su texto**; el literal `null` (que no lanza) también. Un control positivo sobre un documento vivo, porque un helper que declare todo ilegible pasaría los otros |
| 61 | `test_el_punto_de_entrada_declara_el_log_antes_de_los_servicios` | `__main__.main()` invoca `setup_logging()` **antes** de instanciar ningún servicio (AST, por **orden** de lineno; no ejecuta `main()`) |
| 62 | `test_process_list_file_sigue_siendo_un_contrato` | `PROCESS_LIST_FILE` existe, vale lo que debe y la nombran sus tres consumidores vivos |
| 63 | `test_la_documentacion_del_blindaje_no_puede_desfasarse` | las dos docs dicen el rango **medido con `ast`** y los 34 nombres **reales** del `frozenset` |
| 64 | `test_el_log_rota_con_el_limite_declarado` | el handler es un `RotatingFileHandler` **exacto** con `maxBytes`/`backupCount` declarados (`isinstance` no lo distinguiría: hereda de `FileHandler`) |
| 65 | `test_config_no_configura_nada_al_importarse` | `config.py` no **configura** el logging **al importarse**: ni en la cima, ni dentro de un `if`/`try`/`for`/`while` de módulo, ni en el **cuerpo de una clase** (que sí se ejecuta al importar); dentro de una **función** sí. **Iter 5:** además la **firma** de un `def` (decoradores, valores por defecto, anotaciones) se evalúa al importarlo, pero **su cuerpo no**, y un **generador perezoso** no se ejecuta al importarlo mientras que una **comprehension** sí. Detector probado en las dos direcciones, con el recuento **derivado de las tablas** (no escrito a mano) |
| 66 | `test_no_literal_colors_in_views` | **TASK-029 (UI-002):** cero colores literales en views/; todos los colores provienen de `theme.py` |
| 67 | `test_theme_tokens_complete` | **TASK-029 (UI-001):** 15 tokens de color, exactamente 6 tamaños tipográficos, 3 radios de curvatura |
| 68 | `test_contrast_wcag_aa` | **TASK-029 (UI-003):** cumplimiento de ratios WCAG 2.1 AA (>= 4.5:1 texto normal, >= 3.0:1 componentes) |
| 69 | `test_hit_targets_minimum` | **TASK-029 (UI-007):** todos los botones interactivos tienen un tamaño mínimo de 28x28px |
| 70 | `test_semantic_color_contract` | **TASK-029 (UI-012b):** Gaming verde `#1DB954`, peligro rojo `#c22d2d`, semáforos no contaminados |
| 71 | `test_woptimizer_ico_exists_and_valid` | **TASK-029 (UI-006):** existencia y validez del archivo de icono multi-resolución `assets/woptimizer.ico` |
| 72 | `test_scan_latency_and_lazy_exe_resolution` | **TASK-033:** optimización de latencia en `ProcessService` (`psutil.process_iter(['pid', 'name'])`, `exe_path=""` lazy, `model_construct`, precomputación `_CAT_ORDER_IDX`, `get_process_exe_path(pid)` on-demand con degradación segura y benchmark < 25 ms) |
| 73 | `test_models_strict_validation_and_contracts` | **TASK-034:** validación estricta de modelos Pydantic (`strict=True` en `is_favorite`/`is_gaming`, `default_action` restringido a `Literal["start", "kill"]`, `extra="allow"` en `Pack` y `AppData`, y defaults canónicos de `ProcessInfo`) |
| 74 | `test_main_window_navigation_transitions` | **TASK-034:** ciclo de vida y navegación headless en `MainWindow` (transiciones Dashboard -> Packs -> ProcessManager -> Dashboard, destrucción de vistas previas con `winfo_exists()`, activación de estilos nav y recarga asíncrona) |
| 75 | `test_los_workers_de_pack_solo_publican_por_after` | **TASK-035 ciclo 26 (S2, S3; iter 3 y 4):** el worker de `execute_pack`, `kill_pack`, `start_pack`, **`ProcessManagerView._do_load` y `ProcessManagerView.on_kill_selected`** —cinco métodos de tres clases de vista— solo **publica**. La lista de lo permitido son **pares `(raiz, metodo)`**, no raíces: con raíces, `self.pack_service.get_all_packs()` y `self.process_service.get_process_exe_path(1)` colaban. Baja por `ast.Subscript` (iter 3) y desde la iteración 4 también por `getattr`/`setattr`/`delattr`, por `ast.Delete` y por los **argumentos** de las llamadas permitidas: sin eso, `getattr(self, 'status_label').configure(...)`, `setattr(self, '_last_gaming_summary', 'x')`, `del self._last_gaming_summary` y `kill_pack_apps(self.status_label)` pasaban las cuatro. Exige que **cada** `self.after` lleve 0 ms y un callback de la lista blanca. La guarda se prueba **contra sí misma** (8 infracciones sintéticas, 1 worker conforme, y el caso de las dos ramas con `self.master.after` en una) |
| 76 | `test_el_feedback_de_pack_dice_la_verdad` | **TASK-035 ciclo 26 (S1, S4, S5, S9; iter 3) + TASK-036 (iter 4, 5 y 6):** el feedback de cierre dice la verdad en los **cuatro** desenlaces, por las **tres** puertas (gaming, pack normal y la no-gaming de la portada, que hasta la iteración 3 no se ejecutaba nunca), con el worker real, doble pulsación, hilo secundario real y `self.after` encolado. Desde la iteración 4 también entra por el worker de la **rama `start`** de `execute_pack` (que tampoco se ejecutaba nunca). Afirma el **texto exacto** (no "dice algo con 6"), incluido `killed == 1` como éxito, `"✅" not in texto` en las ramas `nada` y `fallo`, y la **omisión de la cláusula de MB con `freed_mb <= 0`**. Y afirma el **aviso del pack que no puede hacer nada** (vacío y Gaming inerte) por sus dos familias, con el color exacto, sin worker, sin nada encolado y **sin doble pulsación armada**, más el gaming sano con apps o con categorías (que no debe avisar). La barra de reposo se afirma por su **texto** (procesos activos y resumen del Gaming Mode) y los temporizadores se miden con un **reloj simulado de plazo absoluto** (t0, t=1000, t=5500, t=6500) en las **tres** puertas del banner, afirmando además que en `_timers_ui` queda exactamente un handle. **Iteración 5, dos bloques nuevos:** (a) el **verbo atado al método** en `start_pack` se afirma con un pack de la familia *opuesta* (gaming, `default_action="kill"`, sin apps), porque el pack vacío que ya había traía `default_action="start"` de serie y no distinguía `"start"` de `pack.default_action`; (b) el **contrato de canal no vacío** del aviso inline, que compara el `fg_color` del `status_label` **contra el fondo de reposo** (no contra el anterior: si el canal pintara `CANCEL`, el color ya sería `CANCEL` de antes y la comparación sería verde por construcción) y por eso detecta y descarta su propia versión vacía. **Iteración 6:** `kill_pack` con un pack **no gaming, vacío y `default_action="start"`** afirma el verbo **"apagar"**: el verbo lo decide la puerta, no el dato del pack (mata D5). **Iteración 7, cuatro bloques** (todos con el mismo arnés de doble de servicio, doble pulsación, hilo secundario y `after` encolado): (a) el **segundo** punto de guarda de `_aviso_pack_inerte`, al que el auditor de cierre mutó y el mutante sobrevivió — entra por `kill_pack` con un doble que entrega el pack **con** apps en las dos primeras lecturas y **sin** apps en el re-fetch, cuenta las lecturas y exige aviso, cero `kill_pack_apps` y cero worker (mata K-a); (b) la **tarjeta de la Portada** atada al `default_action` real por la vía real (`refresh_dashboard` → botón real → `cget("text")`), en las dos ramas y las dos direcciones, con un Gaming Mode de `default_action="start"` como control (mata P-d-a/b); (c) el **contrato de los llamantes** con una guarda `ast` que corre **primero** —el segundo argumento de `mensaje_sin_apps`/`mensaje_banner_sin_apps` tiene que ser una ACCION literal o `pack.default_action`— más la frontera: una acción desconocida (`"apagar"`, `"stop"`, `"Kill"`, `""`) es un `KeyError` con el nombre de la puerta, no un `"apagar"` silencioso (mata D5-c/e/f); (d) la **cadena causal** `create_user_pack` → `default_action="start"` → verbo de la puerta de apagar, medida con el `PackService` real y no con un `Pack(...)` de literales (mata D5-d) |
| 77 | `test_el_gestor_de_procesos_tampoco_miente` | **TASK-035 ciclo 26 iter 3:** la **tercera** puerta de feedback, `ProcessManagerView.on_kill_selected`, que el fix de la iteración 2 y la guarda AST no tocaban y que pintaba `"<tick> 0 cerrados, 0 fallidos."` con `killed == 0`. Entra por `on_kill_selected` de verdad (doble pulsación, hilo secundario real, `after` encolado) y afirma texto y color exactos en los cuatro desenlaces; comprueba que se cierran los PIDs marcados, que el refresco de la lista se programa a 1000 ms y no al instante, y que `skipped` no se confunde con `failed`. **No mata ningún proceso**: el `ProcessService` es un doble |
| 78 | `test_headless_ui` | UI completa se instancia y destruye en 1.5 s sin errores de runtime |
| 79 | `test_el_validador_avisa_en_vez_de_tirar_la_excepcion` | **TASK-037 ciclo 27 (T-27.1 a T-27.4):** la rama `if n_tests is None:` de `validate_docs.py` era **código muerto**: `_recuento_de_tests` no tenía ni un `return None`, así que sus dos rutas (fichero ausente, fuente rota) salían con traceback en vez de con informe. El arreglo es el **productor** (`except OSError` sobre el `open()`, `except SyntaxError` —no `IndentationError`— sobre el `ast.parse()`), NO la rama, que ya estaba escrita para el contrato correcto; y T-27.2 extrae `_comprobar_recuento_de_tests(root, errors, ok)` para que la rama sea alcanzable desde un test. Cuatro fixtures en un `tempfile.mkdtemp()`: **sangría rota** (el caso que medido lanza `IndentationError`), **fichero ausente**, **sano** (la 4-tupla, no `None`) y **definido y no invocado** (que además exige que el mensaje **no** lleve el segmento `invocado y NO definido: .` con la lista vacía). Cada llamada va envuelta en un `try/except Exception` que convierte el crash en `AssertionError`, para que los mutantes M1/M2 mueran por la aserción y no por traceback |
| 80 | `test_el_alcance_del_guard_de_llamantes_se_deriva_del_arbol` | **TASK-037 ciclo 27 (T-27.5 a T-27.7):** el guard del contrato de los llamantes tenía el alcance en una **tupla literal de dos ficheros**, que era una apuesta sobre qué ficheros importan `feedback` y la apuesta tenía un fichero mal (hay tres). El guard pasa a ser `_modulos_que_importan_feedback(raiz)` + `_guardar_contrato_de_llamantes(raiz, acciones_validas)`, y el alcance se **deriva** recorriendo `src/woptimizer/**` con `ast`. El test se monta sobre un **árbol sintético** en `%TEMP%` porque con el repo real no se distingue "derivé el alcance" de "escribí el alcance correcto a mano" (mutante M5): cinco módulos, **cuatro** importadores de `feedback` —dos conformes y dos con verbo cableado, uno de ellos **fuera de `ui/views/`** y otro en forma **`fb.mensaje_sin_apps(...)`** (`ast.Attribute`, que el `getattr(func,"id",None)` de antes se saltaba en silencio— y su import `from woptimizer.ui import feedback as fb`, que tampoco entraba en el alcance— mutantes M6 y M8)— y un quinto que **no** importa `feedback`. Control negativo obligatorio: `pack.default_action` y las ACCIONES literales `"start"`/`"kill"` no se pueden marcar, porque un guard que marca todo no vigila nada (mutante M7) |
| 81 | `test_pack_service_cache_invalidation_and_immutability` | **TASK-040 (Ciclo #30):** Caché inmutable de 2 capas en `PackService.get_all_packs()` (< 0.05 ms), copia defensiva `model_copy(deep=True)` e invalidación atómica de caché al actualizar packs |
| 82 | `test_process_filter_performance` | **TASK-040 (Ciclo #30):** Benchmark de filtrado en lista de procesos (< 350 items) completado en < 2.0 ms usando pre-tokenizado |
| 83 | `test_pydantic_extra_fields_persistence` | **TASK-041 (Ciclo #31):** Persistencia e inmutabilidad de campos extra no estándar en modelos Pydantic `AppData` y `Pack` tras ciclos de `load()` -> `save()` -> `json.load()` |
| 84 | `test_freed_mb_calculation_precision` | **TASK-041 (Ciclo #31):** Precisión del cálculo de `freed_mb` (suma de RSS física de padre e hijos y redondeo exacto a 2 decimales en megabytes) |
| 85 | `test_notification_service_rlock_and_concurrency` | **TASK-042 (Ciclo #32):** Thread-safety y reentrancia en `NotificationService` con `threading.RLock()` bajo concurrencia multihilo |
| 87 | `test_process_service_kill_defensive_zombie_and_oserror` | **TASK-042 (Ciclo #32):** Captura defensiva de `psutil.ZombieProcess` y `OSError` en `kill_processes` y `kill_pack_apps` |
| 88 | `test_process_categorization_latency_and_memoization` | **TASK-045 (Ciclo #35):** Memoización de metadatos de categorización en `_meta_cache` O(1) e invalidación atómica de `_proc_cache` al recargar la DB |
| 89 | `test_tray_session_restoration_integration` | **TASK-043 (Ciclo #33):** Integración de '🔄 Reabrir aplicaciones cerradas' en el menú contextual de `pystray` y notificación nativa resultante |
| 90 | `test_confirmable_mixin_lifecycle_and_widget_contracts` | **TASK-046 (Ciclo #36):** Contratos de ciclo de vida, widgets y estados en `Confirmable` mixin (mutación de estados en botón y label, throttling de 300 ms en 2ª pulsación, changed_text, auto-expiración a 3000 ms, `_cancel_confirm`, `cancel_on_destroy` y tolerancia a `winfo_exists() == False`) |
| 91 | `test_gaming_service_rlock_and_concurrency` | **TASK-047 (Ciclo #37):** Resiliencia de concurrencia y recuperación en `GamingService` (`threading.RLock()` reentrante, concurrencia multihilo en `restore_gaming_session`, preservación defensiva ante excepciones y aislamiento no-OSError en `ProcessService.start_pack_apps`) |



### Notas de Aislamiento
- Los tests de `PackService` usan `tempfile.NamedTemporaryFile` (helper `_pack_service_temporal()`) para no modificar `profiles.json` real. `test_pack_service_backup_and_recovery` limpia además los `.bak` y `.tmp` que genera, y restaura los permisos de solo lectura que usa para probar el `PermissionError`.
- Las sondas de TASK-030 usan `_limpiar_perfiles(ruta)` (principal + `.bak` + `.tmp`, tolerando el flag de solo lectura) o un `tempfile.mkdtemp()` propio por fila, y lo limpian en `finally`. Los dobles se inyectan con `_doble_en(modulo, **atributos)`: sustituyen `json`/`shutil` **en los globales de `pack_service`**, no en la stdlib, así que el resto de la suite nunca ve el doble.
- Los tests de `ProcessService` operan contra listas vacías o nombres inexistentes.
- Las sondas **L1–L7 (TASK-031)** usan un `tempfile.mkdtemp()` propio por escenario y lo
  limpian en `finally`. Los fixtures compartidos son `_HOJA_MALFORMADA` (JSON válido pero
  ilegible para el servicio: la divergencia entre las dos puertas) y `_BAK_CON_OTRO`. En L2
  la rama legacy se construye moviendo `name` → `label`, que es el mismo campo con el nombre
  del formato antiguo, para que la fila `name` rompa el mismo campo en las dos ramas.
- `test_pack_service_backup_and_recovery` (FIX-009) tiene **dos aserciones que TASK-031
  invirtió** a propósito, y su bloque lo dice: la instalación limpia ya **no** crea el
  fichero al arrancar (`load()` es de solo lectura) y el caso "sin `.bak`" ya **no** propaga
  un `OSError` de escritura porque no se escribe nada. Lo que se sigue exigiendo en ambos
  es lo que siempre se quiso: ni un `.bak` basura, ni un `.tmp` colgado, y el fichero del
  usuario intacto.
- `test_kill_recursive` espawnea solo procesos Python propios y los limpia siempre en un `finally`; si el entorno bloquea subprocesos o el kill está protegido por permisos, degrada con un `print` en vez de reventar la suite.
- El test headless requiere un display Windows (falla en CI headless puro).
- Los `print()` deben quedar en **ASCII puro**: la consola de PowerShell es `cp1252` y revienta con `UnicodeEncodeError`. Para mencionar un emoji usa escapes (`\U0001F7E1`), nunca el carácter literal dentro de un `print()`.

### Tests de concurrencia en Tk (TASK-026 / TASK-030)
- **Nada de `sleep` para ordenar hilos.** El entrelazado se provoca con `threading.Event`: un doble de servicio avisa (`cogido[i]`) cuando ya tiene su snapshot y espera (`continuar[i]`) a que el principal le dé paso.
- **El bucle de eventos es el propio test (TASK-030).** El test de FIX-007 ya **no monta un `ctk.CTk()`**: la vista se construye con `__new__` sobre una subclase en la que `processes` y `grouped_processes` son **propiedades que anotan `threading.get_ident()`**, el `after` de la vista **encola** el callback y el test hace de bucle: `join(10)` al hilo secundario y ejecución en el principal de lo entregado. Sin `CTk`, sin `root`, sin `mainloop` y sin Tcl **no existe ruta por la que Tcl pueda colgarse**, así que el reloj de guardia `faulthandler.dump_traceback_later(150, exit=True)` **se ha eliminado**: mataba el runner entero (y con él todos los tests posteriores) y costs 150 s de suite colgada en cada regresión. El helper `_pump()` desaparece con él. Lo que se conserva: las dos cargas solapadas, la puerta por `Event` sin `sleep`, el camino de crash (`_RecordingDict` + iterador abierto) y la **guarda `ast`** de la fase D, que sigue prohibiendo `self.master.after` (TASK-023) y deja de ser la única red.
- **Esperar a que el callback se APLIQUE, no a que se postee.** En el arnés sin Tk no hace falta `mainloop`, pero el mismo error conceptual sigue vigente: `posts` (quién encoló) y las escrituras de las propiedades (quién publicó) se cuentan por separado, y la aserción de identidad de hilo va **antes** que la de recuento, porque su mensaje nombra la mutación exacta.
- **Las comprobaciones estáticas van primero, sin Tk**, para que una regresión falle en milisegundos con un mensaje legible.
- **Nada de assert con tupla.** `assert (a, b), msg` es una tupla siempre verdadera: es la forma más rápida de escribir un test que no comprueba nada.

## Ciclo 26: el feedback que mentía en verde y las guardas que no guardaban (TASK-035)

`mutation-auditor` dio **FAIL** al ciclo 25 con 19 supervivientes. Dos no eran huecos de
cobertura sino **bugs vivos, demostrados en runtime**: `kill_pack` pintaba
`"✅ 0 procesos cerrados (0.0 MB liberados)"` en VERDE Gaming con un pack sin apps vivas (todo
en `keepers`, pack vacío, rutas muertas), y la guarda `ast` que el doc daba por "estricta" era
una lista de 3-4 nombres de método, por la que un `self.status_label.configure(...)` desde el
hilo pasaba. **Una afirmación documental falsa se arregla como un bug**, no se matiza.

### 1. Un test que se llama a sí mismo no verifica nada (S9)

La sonda anterior hacía esto tres veces:

```python
pm._inline_status("✅ 5 procesos cerrados (180.2 MB liberados) · 'Gaming'.", VERDE)
assert pm.status_label.cget("text") == "✅ 5 procesos cerrados (180.2 MB liberados) · 'Gaming'."
```

Es afirmar que el código hace lo que el código acaba de escribir: **100% de cobertura, 0 de
verificación**. Peor, su docstring decía "kill_pack exitoso actualiza status_label…" siendo que
**nunca llamaba a `kill_pack`** (`grep` de la suite: 0 llamadas). El arreglo no es "añadir más
aserciones": es entrar por el camino real. Ahora la sonda pulsa **dos veces** (el contrato de
doble pulsación), el worker corre en un hilo secundario real, el `after` **encola** y el test
hace de bucle de eventos: `join(20)` y aplicación en el principal de lo entregado. Lo que se
afirma es el **texto y el color que produjo el código**, en los cuatro desenlaces y por las tres
puertas de cierre.

| Lo que se afirma | Mutante que muere |
|---|---|
| `color == VERDE` solo con `killed > 0` | color forzado a VERDE siempre |
| `"✅" not in texto` con 0 cerrados | vuelta al literal incondicional |
| `"0 procesos cerrados" in texto` y `"4" in texto` | `"apps cerradas: len(apps)"` |
| el gaming va por `execute_gaming_pack` y **no** por `kill_pack_apps` | rama gaming muerta o intercambiada |
| `color == ROJO` cuando `failed > 0` y nada se cerró | todo en ámbar |

### 2. Un reloj simulado, porque el doble anterior no ordenaba el tiempo (S5)

`_FakeScheduler.fire_due(ms)` dispara por `delay <= elapsed`. Con dos temporizadores de 5000 ms
(el viejo sin cancelar y el nuevo) **vencerían los dos en el mismo `fire_due(5000)`** y el bug
sería invisible. El doble nuevo (`_Reloj`, dentro de la sonda) guarda un **plazo absoluto** por
job y `avanzar(ms)` mueve el reloj. Con él se mide el escenario exacto del auditor sin esperar
5,5 s: t0 primer banner, t=1000 segundo banner, **t=5500** el banner del segundo mensaje tiene
que seguir en pantalla (el viejo lo apagaría a los 5000 ms desde t0) y **t=6500** tiene que
haber saltado el auto-ocultado de 5000 ms (si desaparece o se va a 60 s, no).

Matriz `_matrix_c26.py` (utillaje de diagnóstico en la raíz, con prefijo `_`; copia del árbol a
`%TEMP%` sin `.git`, `__pycache__` purgada, sondas en **subproceso** — nunca en el proceso que
importa `run_tests`, por la trampa del `sys.stdout` de este repo — y las **tres** sondas del
ciclo en cada mutación).

> **La tabla anterior era mentira y la tabla esta la reproduce.** La versión previa de
> `_matrix_c26.py` declaraba "12 mutaciones, 12 muertes, 0 supervivientes" y **reventaba en la
> mutación 5 de 12** con `AssertionError: no se encontró el ancla de M6` (el ancla
> `self._schedule_ui(5000, ...)` ya no existía: la iteración 3 extrajo
> `_reprogramar_autoocultado()`), y `correr()` lanzaba **2 de las 3 sondas**, así que la
> tercera puerta nunca estuvo en esa matriz. Además el `print` de la salida podía llevar
> emoji y la consola es cp1252. Todo eso está arreglado: las anclas se comprueban contra el
> código de hoy y **un ancla que no se encuentra es un error duro**, no una mutación saltada
> en silencio, y la salida se filtra a ASCII. Una tabla de mutaciones que nadie puede
> reproducir es peor que no tenerla: parece cobertura y no lo es.

**30 mutaciones, 30 muertes, 0 supervivientes** (ejecutadas el 2026-10-01, salida literal de
`python _matrix_c26.py`). La fila **D5** es de la iteración 6 y las **K-a, P-d-a/b y D5-c/d/e/f**
son de la iteración 7 (las afirmaciones que el cierre de auditoría encontró sin respaldo);
**D1/D2** son de la iteración 5 y se han rescueado aquí. **D3/D4 no son reproducibles** y el
doc lo declara más abajo en vez de fingir una tabla que nadie puede correr.

| Mutante | Muere por |
|---|---|
| **M-A** `execute_pack` vuelve al `return` mudo | "un pack no gaming y vacío SE AVISA, no se traga en silencio" |
| **M-B** el verbo se cablea a `apagar` | el aviso preventivo de `start_pack` ("no tiene apps que iniciar") |
| **M-C** el aviso en el color de marca (`GAMING`) | "el aviso de pack inerte es de ATENCIÓN" |
| **M-D** la guarda sin sitio (equivale a ir tras la doble pulsación) | la misma aserción de texto; `_sin_confirmacion_pendiente` la mata detrás |
| **M-E** se borra el diagnóstico del gaming inerte | "el Gaming Mode inerte se diagnostica" |
| **M-F** `es_pack_inerte` con `or` | `or` hace inerte al gaming CON categorías: "se esperaba 1 worker secundario, se crearon 0" |
| **M-G** el aviso reusa `_inline_status` | "el aviso va sobre SURFACE_ALT, no sobre el fondo CANCEL" (y el auto-ocultado detrás) |
| **M-H** se borra `if freed_mb <= 0` de `clausula_mb` | "cerrar un proceso sin liberar MB no puede inventar una cifra de RAM" |
| **S1-a** `_run_start` intercambia `launched`/`failed` | "tiene que entregar launched y failed sin intercambiarlos" |
| **S1-b** `_run_start` arranca `start_pack_apps([])` | "la rama start arranca SUS apps, no una lista vacía: llegó []" |
| **S1-c** `_run_start` publica en `_show_banner` con `p.name` como `is_gaming` | "el after debe publicar en `_show_start_banner`" |
| **S2-a** la guarda vuelve a no bajar por `getattr`/`setattr` | su control sintético: "la guarda no ve los accesos dinámicos a la vista" |
| **S2-b** la guarda vuelve a ignorar `ast.Delete` | su control: "la guarda no ve los `del` sobre la vista" |
| **S2-c** la guarda vuelve a mirar solo `call.func` | su control: "no ve `self.<attr>` como ARGUMENTO de una llamada permitida" |
| **S3** el sustantivo se cablea en la rama `nada` | "el sustantivo también se usa en la rama 'nada'" |
| **D5** `_aviso_pack_inerte` vuelve a cablear el verbo a `pack.default_action` | "el verbo lo decide la PUERTA que se está pulsando (aquí apagar), no el `default_action` del pack" |
| **K-a** desaparece el **segundo** punto de guarda de `_aviso_pack_inerte` (el del re-fetch) | "el pack perdió sus apps ENTRE las dos pulsaciones: la segunda guarda de `kill_pack` tiene que avisar" — **era el superviviente real**: lo midió el auditor de cierre, y el mutante no es equivalente (es alcanzable y cambia el comportamiento) |
| **P-d-a** la tarjeta de la Portada vuelve al literal `KILL` (rama normal) | "un pack de arrancar no puede anunciarse como 'KILL'" |
| **P-d-b** la tarjeta del Gaming Mode vuelve al `KILL` congelado en la vista | "un Gaming Mode con `default_action='start'` se INICIA, así que su tarjeta no puede prometer 'KILL'" |
| **D5-c** `_verbo` vuelve al `get` con el default silencioso | "cablear el VERBO 'apagar' en la puerta tiene que fallar, no devolver un 'apagar' silencioso" |
| **D5-d** el default del modelo pasa a `"kill"` (mata la cadena causal) | "un pack recién creado nace con `default_action='start'` y no con 'kill'" |
| **D5-e** un llamante cablea un verbo donde va la acción | la guarda `ast` de los llamantes, que corre **primero**: "pack_manager_view.py:L482 mensaje_sin_apps recibe 'apagar', que no es una ACCION" |
| **D5-f** "arreglar" el fallo duro metiendo el verbo como clave del mapa | "una palabra no puede ser ACCION y verbo a la vez en el mapa de `VERBOS`" |
| **D1** `start_pack` vuelve a cablear el verbo al pack | el aviso preventivo de `start_pack` con el gaming de apagar ("no tiene apps que iniciar") |
| **D2** `start_pack` cablea el verbo a `"kill"` a pelo | el mismo aviso preventivo: sale "apagar" |
| **R-1** `clasificar_cierre` dice siempre `EXITO` | "nada que cerrar dice exactamente eso" |
| **R-2** `_show_banner` deja de refrescar la barra de reposo | "tiene que refrescar la barra de reposo: antes …, después …" |
| **R-3** se borra la cancelación del auto-ocultado previo | "el banner nuevo debe cancelar el auto-ocultado anterior" |
| **R-4** el worker de la portada vuelve a tirar `failed`/`skipped` | "tiene que entregarle a `_show_banner` el resultado completo" |
| **R-5** la guarda AST anulada (`return []`) | "el detector no ve las tres infracciones de control" |

Las dos primeras filas de esta tabla son la prueba de que el arreglo de TASK-036 no es código
muerto: sin M-A a M-H, `run_tests.py` estaría en verde con el silencio, el verbo cableado, el
color equivocado, la guarda movida, el diagnóstico borrado, el `or`, el canal equivocado y la
cláusula de MB siempre escrita.

#### Iteración 5 — D1 a D4, medidas sobre copia en `%TEMP%` (2026-10-01)

> ⚠️ **Esta tabla estaba documentada y NO era reproducible.** El script de una sola
> pasada que la produjo no quedó en el repo, así que nadie podía volver a correrla: una
> tabla de mutaciones que solo existe en un markdown es exactamente lo que este mismo
> doc condena en `:194-197`. La iteración 7 lo resuelve partida en dos, y lo dice:
> **D1 y D2 SÍ son reproducibles** — mutan código de `src/`, así que se han incorporado a
> `_matrix_c26.py` (30 mutaciones, salida literal arriba) con ancla al código de hoy.
> **D3 y D4 NO son reproducibles y no se pueden volver reproducibles tal cual**:
> mutaban el **arnés de la propia sonda** (el `_inline_status` del doble y la aserción
> del canal vacío) en su versión de la iteración 5, que la iteración 7 reescribió. Anclarlas
> hoy significaría inventar una mutación distinta y llamarla D3/D4, que es peor que
> declararlas no reproducibles. Se conservan como **registro histórico** de por qué el
> contrato de canal no vacío se midió entonces; quien necesite volver a medirlas debe
> escribir un script nuevo, y ese script es suyo, no una reconstrucción de este bloque.

Salida literal de aquella medición (script de una sola pasada, control primero, `src/` **nunca** mutado en sitio).
**4 mutaciones, 4 muertes, 0 supervivientes.** Las cuatro van contra el código que la iteración 5
escribió: el verbo atado al método en `start_pack` y el contrato de canal no vacío.

```
CONTROL (sin mutar): rc=0 -> VERDE

D1  start_pack vuelve a cablear el verbo al pack (pack.default_action) MUERE
   por: arrancar dice INICIAR aunque el pack sea de apagar: el verbo lo decide el metodo que se
   esta ejecutando, no el default_action del pack. Con la otra cableacion sale 'apagar':
   "'Gaming Vacio Start' no tiene apps que ap..."
D2  start_pack cablea el verbo a 'kill' a pelo                 MUERE
   por: aviso preventivo de pack vacio: "'Pack Vacio' no tiene apps que apagar."
D3  el canal inline de la base pinta fondo CANCEL              MUERE
   por: el canal inline no pinta fondo: el diagnostico ROJO caeria sobre el '#5a4a1e' de la
   confirmacion pendiente. Reposo: 'transparent', despues: '#5a4a1e'
D4  el aviso del pack vacio pierde su texto (canal vacio)      MUERE
   por: aviso preventivo de pack vacio: ''
```

**Por qué D1 necesita el pack de la familia opuesta.** El caso viejo (`Pack(id="vacio", name=
"Pack Vacio", apps=[])`) trae `default_action="start"` **de serie**, así que `"start"` y
`pack.default_action` producen el mismo texto y la convención queda sin medir: el mutante D1
sobrevivía. El caso nuevo usa un pack **gaming con `default_action="kill"` y sin apps**, donde las
dos cableaciones divergen de verdad. La regla general: **para afirmar que un valor no está
cableado a un campo, el fixture tiene que hacer que ese campo valga lo contrario.**

**Por qué D3 compara contra el fondo de reposo y no "contra el anterior".** Si el canal pintara
`CANCEL`, el color ya sería `CANCEL` *de antes* y la comparación "antes/después" sería verde por
construcción — el mismo test que se llama a sí mismo, que es el vicio que este ciclo vino a cerrar.
El dev además **descarbó su propia versión vacía**: la medición compara contra un valor leído del
widget real *antes* de que ningún `_inline_status` lo toque, y esa es la razón de que un detector
autodetectado y descartado sea exactamente lo que se quería.

**D5 (iteración 6) es el espejo exacto de D1**, y por eso el caso nuevo es el pack de la familia
opuesta en la otra puerta: `Pack(id="recien", apps=[], default_action="start")` en `kill_pack`, que
tiene que decir **"apagar"**. Sin ese caso, `_aviso_pack_inerte` podía seguir cableado al
`pack.default_action` —que es como estaba— y la suite en verde, porque el Gestor solo se probaba
con el gaming inerte y con un id inexistente. Un pack recién creado nace con `default_action="start"`
(`on_new_pack` → `create_user_pack(pack_id, name, [])` → modelo por defecto), así que el bug era la
**primera acción de un usuario recién instalado**: "Apagar" respondía "no tiene apps que **iniciar**".

> **Esa última frase la sustained el comentario de la sonda y este doc, y no la medía nadie.**
> Cambiar el default del modelo (`models.py`: `default_action: Literal["start", "kill"] = "start"`)
> a `"kill"` dejaba los 78 tests en verde. La iteración 7 la ata por la **vía real**: la sonda
> llama a `create_user_pack` de verdad, exige `default_action == "start"` en lo que devuelve y pasa
> ese mismo pack por la puerta de apagar exigiendo el texto "apagar". Mutante **D5-d** de
> `_matrix_c26.py`, MUERE. Lo que sigue siendo verdad sin medición es la consecuencia: el bug era
> visible para un usuario recién instalado **si pulsaba apagar sin apps**; que lo hiciera o no, eso
> ya no lo afirma nadie.

**K-a (iteración 7) — el punto que el cierre de auditoría encontró sin respaldo.** `_aviso_pack_inerte`
tiene dos puntos de comprobación y el código lo decía ("por eso está en un método y no en dos
literales"). El auditor mutó el **segundo** y el mutante **vivió**: con un pack que tiene apps en la
primera lectura y ninguna en la segunda, el usuario veía "no tiene apps que apagar"; mutado, se
lanzaba `kill_pack_apps([])` **después** de consumir la doble pulsación. El caso nuevo no puede llamar
a `_aviso_pack_inerte` con un pack vacío, porque eso mide el **primer** punto (y es lo que hacía la
iteración 6). Entra por `kill_pack` con doble pulsación y un doble de servicio que entrega el pack
**con** apps en las dos primeras lecturas y **sin** apps en el re-fetch por `id`: tres lecturas, que es
lo que hace alcanzable el segundo punto. El bloque además **cuenta las lecturas** y exige que la
confirmación esté armada y consumida, porque si el arnés no llegara al re-fetch el bloque estaría
afirmando el primer punto con otro nombre — el mismo falso verde que produce un fixture que no llega.
Mutante **K-a** de `_matrix_c26.py`, MUERE.

### 3. La guarda `ast` compara **pares**, y eso obliga a decir qué NO comprueba

Del objetivo real de cada `threading.Thread(target=...)` se permite una lista **corta y
explícita** de **pares `(raiz, metodo)`**, y es infracción toda llamada o escritura que se
resuelva sobre `self` por `Attribute`, por `Subscript`, por `getattr`/`setattr`/`delattr`,
por `del`, o **pasada como argumento** de una llamada permitida. Se exige que **cada**
`self.after` del worker lleve 0 ms y un callback de la lista blanca, no solo el primero que
aparece.

**Por qué pares y no raíces** (medido en la iteración 3, 80 mutaciones / 21 supervivientes):
con una lista de raíces, `self.pack_service.get_all_packs()` y
`self.process_service.get_process_exe_path(1)` pasaban las dos. Y
`self.__dict__['status_label'].configure(...)` pasaba porque la resolución de la raíz no bajaba
por `ast.Subscript` — la misma llamada de widget, escrita por la puerta de atrás. Con la lista
de pares y el descenso por `Subscript`, el mutante de "borrar el `discard`" y el de
"comparar solo la raíz" mueren.

**Por qué tampoco bastaba mirar `call.func`** (medido en la iteración 4): cuatro formas más
de llegar a `self` pasaban la guarda entera con la suite en verde, y las cuatro son la misma
infracción con distinta ropa:

| se escapaba | por qué |
|---|---|
| `getattr(self, 'status_label').configure(text='x')` | `getattr` no es ni `Attribute` ni `Subscript`: el `Attribute` estaba partido en dos |
| `setattr(self, '_last_gaming_summary', 'x')` | la llamada es el nodo más externo; `_raiz_de_self` solo se preguntaba por `call.func` |
| `del self._last_gaming_summary` | la guarda miraba `ast.Assign`, no `ast.Delete` |
| `self.process_service.kill_pack_apps(self.status_label)` | el widget no se escribe ahí, pero se **saca de la vista** para que otro lo escriba |

Una guarda así **se prueba contra sí misma** antes de que la use: ocho infracciones sintéticas
que tiene que ver, un worker conforme que no puede marcar, y el caso de las dos ramas. Un
detector que no ve nada y uno que ve de más dan **el mismo verde**, y sin las dos direcciones
no se sabe cuál de los dos se tiene.

**Lo que la guarda NO comprueba, escrito para que nadie lo lea como más:**

* que el `after` se ejecute de verdad en el hilo principal, ni el resultado de la operación.
  Eso lo cubren las sondas dinámicas con hilo secundario real;
* los `threading.Thread` de `ui/app.py` (el toast de arranque y el hilo del icono de la
  bandeja), que no son vistas, ni ningún worker nuevo que se añada sin meterlo en la lista
  del test — la lista de vistas y métodos está **en el bucle de aplicación** de la sonda, a la
  vista;
* **un alias local**: `lbl = self.status_label` y luego `lbl.configure(...)` no se resuelve
  hasta `self`, y ese agujero no lo cierra un análisis estático de este tipo. Es el que queda
  abierto, y se dice en vez de prometer "todo lo que cuelgue de `self`".

Un doc que promete más de lo que el guard comprueba es la misma clase de defecto que el bug
que el guard no veía. La iteración 4 corrigió exactamente eso: la frase anterior ("todo lo
demás que cuelgue de `self` es infracción") era una promesa de muro sobre una red.

### 3-bis. La iteración 3: lo que la auditoría encontró y no era estilo

Tres correcciones de fondo, todas medidas:

- **Había una TERCERA puerta de feedback.** `ProcessManagerView.on_kill_selected` —la que
  mata uno a uno lo que el usuario marcó a mano— pintaba `"<tick> 0 cerrados, 0 fallidos."`
  con `killed == 0`, porque tenía su **propia** verdad y no el formateador común. Era el bug
  que motivó el ciclo, vivo en la vista que nadie había tocado. Ahora entra por
  `mensaje_cierre_pack` con el sustantivo parametrizado, y hay una sonda propia
  (`test_el_gestor_de_procesos_tampoco_miente`).
- **Un bloque de código duplicado es dos sitios donde el bug se esconde.** La cancelación del
  temporizador del banner estaba byte a byte en `_show_start_banner` y en `_show_banner`, y la
  sonda solo instrumentaba la primera. Se extrajo a `_reprogramar_autoocultado()` y el escenario
  con reloj simulado se monta ahora en **las dos** puertas. No es "duplicar el test": es no
  duplicar el código.
- **Una rama sin ejecutar no es una rama probada.** La rama no-gaming de `execute_pack` no se
  ejecutaba nunca, así que `if p.is_gaming:` y `kill_pack_apps(p.apps)` podían romperse sin
  que nada se notase. El mismo patrón del ciclo 14. Basta con un caso con pack no gaming.
  Lo mismo con `killed == 1` (que `clasificar_cierre` con `killed > 1` degradaba a "nada") y con
  `failed != skipped` (que hacía invisible intercambiar el orden de la 4-tupla).

### 3-ter. La iteración 4: tres cosas que el verde no distingüía

1. **La rama `start` de `execute_pack` tampoco se ejecutaba nunca.** Tres mutaciones pasaban
   la suite entera: intercambiar `launched`/`failed` en `_run_start`, arrancar
   `start_pack_apps([])`, y publicar en `_show_banner` con `p.name` en el hueco de `is_gaming`
   (banner verde Gaming y `_last_gaming_summary` basura, sin crash). El caso entra por el
   **worker real** —hilo secundario, `after` encolado, aplicado en el principal—, no llamando
   a `_show_start_banner` con valores puestos a mano, que es el patrón "test que se llama a sí
   mismo" que el §1 de esta guía condena. Y como `_last_gaming_summary` es un atributo que
   **persiste entre casos**, la aserción correcta no es "no aparece Último Gaming Mode" sino
   "la barra de reposo no ha cambiado": la primera afirmación habría muerto por el caso
   anterior, no por el mutante.
2. **Una aserción que afirma el silencio se convierte en la especificación de la mentira.**
   `assert dash.status_label.cget("text") == antes_texto` con el mensaje *"se corta en
   silencio: ni aviso ni confirmación armada"* era verde, y además era verdad sobre el código
   viejo. Invertirla en el mismo commit que el aviso es la parte que hace el arreglo
   comprobable; lo que se mantiene del caso viejo es que no hay worker ni nada encolado, que
   sigue siendo cierto y sigue importando.
3. **Un parámetro probado en una sola rama no está probado.** La comprobación de
   `sustantivo="apps"` miraba solo el desenlace de éxito, y el valor por defecto solo la rama
   `nada`: cablear `"procesos"` a mano dejaba la suite en verde, porque los dos llamantes de
   producción pasan `"procesos"`. Ahora se comprueban las dos ramas que nombran el sustantivo.

## Sondas de mutación: cada test nombra la mutación que mata (TASK-030)
Regla del ciclo #18: **un criterio sin mutación asociada es un deseo**. La tabla está medida
(reescritura del texto de `src/` + `importlib` + las sondas finales), no es una intención:

| Sonda | Invariante | Muerte (medida) |
|---|---|---|
| **P1** el volcado nunca toca el principal | el volcado va a otro fichero del mismo directorio y el principal conserva sus bytes si se corta | M1 (×4), M3, M4, M10 |
| **P1b** publicar no trunca el principal | publicar no usa un primitivo de copia | M2, M10 |
| **P2** `save()` no escribe si la rotación no puede leer | un error que no es corrupción no se convierte en "sigo y sobrescribo" | M6, M2, M10 |
| **P3** se intentó volcar (espiando `json.dump`) | se distingue "no intentó escribir" de "intentó y falló" | M1, M10 |
| **P4** la forma legacy no tumba la app | `profiles` no-mapa no revientan `PackService()` y sí se recuperan del `.bak` | M5, M6, M9, **M12 (el bug)** |
| **P5** tabla de clases de corrupción | las 4 clases de `CORRUPTION_ERRORS` se recuperan, fila a fila | M5 |
| **P6** un `OSError` de lectura no es corrupción | se propaga y el `.bak` queda intacto byte a byte | M6, M7 |
| **P7** un `AttributeError` ajeno no es corrupción | un `AttributeError` no deliberado se propaga | M7, M9 |
| **P8** arnés sin Tk | el estado se publica desde el hilo principal | reintroducción de la publicación desde el hilo (M13) |

### Sondas L1–L7: las hojas del pack y el `.bak` que nunca se consultó (TASK-031)
Regla del ciclo #19: **un criterio sin mutación asociada es un deseo**. Las siete sondas se
verificaron rompiendo `src/` a propósito sobre una **copia** en `%TEMP%` (el árbol real no
se toca) y confirmando que cada una muere con **su** mutación. La columna del `.bak` de la
matriz de `proposal.md` §0.1 pasó de *"DESTRUIDO en 7 de 8"* a **INTACTO en los 8**.

| Sonda | Invariante | Muerte (medida) | Por qué esa aserción y no otra |
|---|---|---|---|
| **L1** la rotación usa la misma puerta que `load()` | con principal **JSON válido pero ilegible para el servicio** + `.bak` sano, tras un `save()` real el `.bak` sigue siendo **legible** y contiene el pack `salvado` | **L-M1** (`_rotate_backup` vuelve a `json.load`) | Afirmar *"el `.bak` existe"* sería verde por la razón equivocada: basta con que el mutante lo borre en vez de pisarlo. Con `json.load` el mutante **pisa**, y la lectura del `.bak` falla con `ValidationError` **dentro** de la comprobación. |
| **L2** la hoja malformada se clasifica | **8** hojas (`keepers` str, `target_categories` dict, `apps` int, `name` int, `is_favorite` **"true"** y **`1`**, `default_action` "PURGAR", `is_gaming` **"true"**) × **2 ramas** (la última solo en la moderna, porque en la legacy `is_gaming` se fuerza a `False` por diseño): cada una da `PerfilCorruptoError` (legacy) o `ValidationError` (moderna), con `.bak` sano recupera `salvado`, y el mensaje dice **campo + pack + tipo real** | **L-M2** (volver al `Pack(...)` literal de 5 campos), **L-M2b** (`traducido["id"] = k`), **L-M8d** (`is_gaming` sin `strict=True`), **M4b** (`is_favorite` sin `strict=True`) | Sin exigir el **texto**, E-2 podría "cumplirse" dejando que Pydantic hable con sus 14 líneas y su URL: quien repara el fichero es el usuario. La aserción del texto en una sola línea es la que obliga a traducirlo. **Corrección de la iteración 2:** esta fila afirmaba que también mataba `L-M2b` y era **FALSO**: la fixture traía `"id"` de serie, así que la línea era código muerto y su mutación-sobreviviente era invisible. Ahora la fixture legacy **quita `id`** (como un registro legacy de verdad) y `L10` afirma además sobre el **contenido** (`pack.id == clave`). **Corrección de la iteración 3:** la fila `is_favorite: "si"` tampoco podía morir (Pydantic laxo rechaza `"si"`); ver la corrección de `L11`–`L12` más abajo. |
| **L3** `load()` no escribe | con **cualquier** principal: `save()` no se invoca desde `load()` y los bytes del principal y del `.bak` son los de antes | **L-M3** (`_ensure_gaming_pack` vuelve a llamar a `save()`; o `load()` recupera su `self.save()`) | Es la **única** sonda que ata E-1 y E-3: con solo E-1+E-2 el `.bak` se seguiría destruyendo, un poco más tarde. El contador de `save()` va acompañado de la aserción de **bytes**: `0` no es un umbral arbitrario, es la definición de "solo lectura". |
| **L4** la recuperación no sobrescribe el `.bak` | tras recuperar **y** guardar, `bytes(.bak)` es byte a byte el original y **no** contiene la versión recuperada | **L-M4** (un `save()` en la ruta de recuperación, o rotar "para dejar el backup al día") | Sin comparar **bytes**, "no sobrescribir" y "sobrescribir con lo mismo" son indistinguibles. La aserción final ("el guardado real **ocurrió**") es la que impide el verde por no hacer nada. |
| **L5** sin `.bak` legible no se sobrescribe el principal | principal corrupto sin `.bak`: los bytes no cambian, la app arranca, y el pack queda **marcado como dañado** | **L-M5** (reponer `AppData()` + `_ensure_gaming_pack()` + `save()`) | La aserción que muere es "los bytes del principal son los de antes", que no depende de cuántas veces se escriba. La segunda mitad (marcado) evita que la recuperación siga siendo silenciosa por otro camino. |
| **L6** un campo desconocido no es corrupción y no se borra | `packs.mio.notas` arranca **sin** recuperar del `.bak` y **sigue** en el fichero tras un `save()` | **L-M6** (`extra="forbid"`, o la whitelist de `isinstance` de la opción (a)) | **Es la sonda que separa la opción (a) de la (b)**: sin ella, "más `isinstance`" y "validar contra el modelo" son indistinguibles. Fija además que un `.bak` de un build más nuevo no es corrupción. |
| **L7** `packs` y `profiles` a la vez es corrupción | se clasifica **nombrando las dos claves** y, con `.bak` sano, ni `salvado` ni `otro` se pierden tras el `save()` | **L-M7** (quitar `'packs' not in raw_data`) | Hoy el pack `otro` desaparecía del disco sin clasificar nada. La aserción que muere es "el pack `otro` sigue en el fichero **después** del `save()`", que es donde la pérdida es observable. |

**Por qué L1 y L3 son dos sondas y no una.** Con E-3 (`load()` de solo lectura) la rotación ya
no se ejecuta durante el arranque, así que un espía del arranque **no la vería nunca**; y sin
E-3, la rotación del arranque lo que destruye el `.bak`. L1 dispara la rotación con un `save()`
**real** del usuario y mira el `.bak`; L3 mira lo que hace `load()` sin escribir. Juntas
cierran las dos puertas.

### Sondas L8–L10: los tres agujeros que dejó la auditoría de la iteración 2 (TASK-031)

El `mutation-auditor` de la iteración 1 dio **FAIL**: la línea `extra="allow"` de `AppData` era
**portante** contra la pérdida de datos y no tenía ni una sonda (mutación `L-M6c`, que
sobrevivía a las siete). Estas tres sondas cierran ese agujero y los dos que salieron al
inspeccionar la política de `extra`:

| Sonda | Invariante | Muerte (medida) | Por qué esa aserción y no otra |
|---|---|---|---|
| **L8** una raíz mal escrita no destruye los packs | `{"perfiles": …}` / `{"packs2": …}` / `{"paquets": …}` / `{"Packs": …}`, **con y sin `.bak`**: al arrancar los bytes del principal son los de antes, y tras un `save()` **real** la raíz mal escrita sigue en el fichero **con los packs del usuario byte a byte** | **L-M6c** (`extra="ignore"` en `AppData`) y **L-M8a** (clasificar la raíz mal escrita como corrupción) | Con cero packs en memoria no hay nada que mirar en memoria: lo único observable es el **fichero**. La comparación es del subárbol del usuario con el mismo `json.dumps(sort_keys=True)` a los dos lados, porque el `indent=4` del escritor es cosa suya y no debe ser parte del contrato. Y `fichero_danado is False` fija el **coste** de la decisión (el arranque ve cero packs sin avisar): cambiarla obliga a cambiar el test a propósito. **Corrección de la iteración 3:** la muerte de `L-M8a` depende de **qué variante** se implemente; medido en las dos, y la tabla está en `data-models.md` §4.6. |
| **L9** un error de escritura no es un campo desconocido | **9** campos mal escritos × **2 ramas**: 7 a una pulsación (`keeper`, `keeppers`, `" keepers"`, `app`, `is_favorit`, `default_actions`, `is_gamingg`) + **2 de grafía** (`IS-FAVORITE`, `IS_GAMING`, que están a **11** y **2** de distancia en bruto y solo colisionan por coincidencia exacta sobre la clave normalizada); `PerfilCorruptoError` que nombra el campo mal escrito, **la clave que queda sin leer** y el pack; y al recuperar del `.bak` **los `keepers` reales vuelven** | **L-M8b** (quitar la colisión), **L-M8f** (umbral 1 → 2) y **M13** (`_normalizar_clave` → identidad) | La segunda mitad de la primera parte es la que hace que la elección sea "corrupción" y no "normalizar a `[]`": si al recuperar volvieran `keepers == []`, el criterio de §3.1 estaría mintiendo. La segunda mitad del test (10 campos extra legítimos, el más cercano `note` a distancia 2 de `name`) es la que **mata el desbordamiento del filtro**: por construcción no puede rechazar campos de verdad, y un umbral de 2 ya lo haría. Las dos filas de grafía son las que hacen que la normalización deje de ser "cosmética": sin ellas, `_normalizar_clave` podría ser la identidad y la sonda seguiría verde. |
| **L10** la clave del mapa es la identidad del pack | `id != clave` es corrupción en las 2 ramas, **sin tocar un byte**; y en un fichero bien escrito, cada pack se encuentra por su `id` (la expresión literal de `pack_manager_view.py:100`) y un registro legacy sin `id` hereda la identidad de la clave | **L-M8c** (quitar la guarda de identidad) y **L-M2b** (quitar `traducido["id"] = k`) | Sin la segunda mitad, la guarda de identidad podría "cumplirse" con un `KeyError` en la UI en el mutante. Sin el bloque legacy, `L-M2b` sería código muerto otra vez: aquí la aserción es de **contenido** (`packs[clave].id == clave`), y sin la línea `Pack(**traducido)` ni siquiera llega a la aserción. |

**Reparto de competencias (por qué esto no es la lista de `isinstance` campo a campo que
`proposal.md` §2(a) rechazó).** `Pack` es dueño de los **tipos** y los **enumerados**; el
servicio (`_vigilar_hojas`) es dueño de la **identidad** y de la **política de campos
desconocidos**. Son dos reglas que parten de `Pack.model_fields`, no una lista escrita a mano:
verificado con un campo inventado (`ventilador`), un `ventiladors` mal escrito se clasifica y
un `ventilador` bien escrito se acepta, sin tocar una línea de código. **Límite de ese
reparto, fijado en la iteración 3:** las dos reglas son afirmaciones **sobre las hojas** y
no tienen versión para la raíz, y `L12` es la sonda que lo impide (`data-models.md` §4.6).

### Sondas L11–L12: la raíz, de las dos mitades (TASK-031 iteración 3)

El `mutation-auditor` de la iteración 2 dejó tres supervivientes. Los dos primeros eran de la
**raíz**, y son justo las dos mitades de un mismo contrato: *no se clasifica* / *no se borra*.

| Sonda | Invariante | Muerte (medida) | Por qué esa aserción y no otra |
|---|---|---|---|
| **L11** la raíz **legacy** conserva sus claves extra | `{"profiles": {…}, "favorite": "mio", "version": 2, "escrito_por": {…}}`: arranca sin clasificar, y tras un `save()` **real** las tres claves siguen en el fichero **con su valor**, los packs del usuario también, y **`profiles` no aparece**; el fichero escrito **vuelve a arrancar limpio** | **M8** (`AppData(packs=packs_dict)`: `favorite` desaparece del disco) y **M8b** (copiar también `profiles`) | La aserción de M8b no es "la clave no está", que un mutante cumpliría por casualidad, sino **releer el fichero escrito** y afirmar que arranca limpio: conservar `profiles` deja un fichero con las **dos** claves, que la lectura siguiente clasifica como corrupción (`L7`), y el landmine solo explotaría en el **segundo** arranque. El control del final (una raíz legacy *sin* extras) es lo que impide que "funcione" por no cargar nada. |
| **L12** una clave raíz **nunca** es un error de escritura | 5 claves raíz que se parecen a un campo de hoja a una pulsación (`names`, `ids`, `favorite`, `keeper`, `is_favorit`) junto a un `packs` válido, **más** 4 raíces sin clave válida (`{"names": …}`, `{"ids": …}`, `{"packs2": …}`, `{"profiless": …}`): ninguna se clasifica, ninguna borra el `.bak` sano, y todas **siguen en el fichero** con su valor tras un `save()` real | **M9** (`_colision_de_tecla` aplicado a la raíz) y **L-M8a** (clasificar la raíz sin clave conocida) | Es la sonda que hace **ejecutable** la decisión de `data-models.md` §4.6: no se vigila la raíz porque hacerlo es pérdida de datos, no porque "no aplique". La segunda mitad (raíz **sin** clave válida) existe porque un filtro de colisión contra campos de *hoja* no ve `perfiles`: sin ella, una variante del mutante pasaba en verde (medido, no supuesto). |

**Corrección de la iteración 3 en la fila de `L2`** (`test_la_hoja_malformada_se_clasifica`):
la fila `is_favorite: "si"` **no podía morir**. Pydantic v2 en modo **laxo** rechaza `"si"`
igual que en estricto (no está en su lista de booleanos laxos), así que la fila quedaba
verde **con y sin** `strict=True`: el `strict` de `is_favorite` estaba puesto y nadie lo
vigilaba. Sustituida por `"true"` y por `1`, que **sí** coaccionan a `True`. De ahí sale
la muerte de **`M4b`**. Regla general extraída: **el valor de una fila de coerción tiene que
ser un valor que el modo laxo coaccione**, o la prueba no distingue los dos modos.

**Lo que esta iteración NO arregla (deuda declarada, no esconde).** Una raíz mal escrita
arranca con **cero packs y sin aviso** (`data-models.md` §4.3). Clasificarla como corrupción
sería **peor**: en la ruta sin `.bak`, `load()` hace `self._data = AppData()` y el siguiente
guardado publicaría `{"packs": {"gaming": …}}` — los packs se perderían igual, y con un aviso
de encima. El precio de la política está **fijado por `L8`**, no escondido.

**`P3` cambió de sentido en TASK-031 y su docstring lo dice.** Nació para demostrar que la
regeneración **llegaba a volcar**; con E-3 esa ruta no existe. La aserción se invirtió
(`load()` no vuelca) y la muerte de M1/M10 se trasladó a la escritura real, que es la que
sigue existiendo. Se conserva la misma costura (`json.dump` en los globales de
`pack_service`) porque **nunca** se cuentan llamadas a `save()` para demostrar el destino de
un volcado.

M2 y M10 también matan P1b/P2 de rebote: `copyfile` no borra el temporal, y un temporal en una
ruta que no existe revienta el `open`. La muerte **nombrada** de cada uno es la de su fila: P1b
para M2, P1/P3 para M10.

Dónde está cada una y por qué existe:
- **P1** inyecta el fallo **dentro** de `json.dump`, con el **handle real**, y afirma sobre los **bytes** del principal. Afirmar "no queda un `.tmp`" (el test anterior) es afirmar un **artefacto**: si `save()` deja de crear el temporal, el assert sigue verde por la razón equivocada. Orden obligatorio: `antes = read_bytes()` se toma **después** de construir el servicio, porque `__init__` → `load()` → `_ensure_gaming_pack()` → `save()` ya reescribió el archivo una vez.
- **P1b** existe porque **la atomicidad de la publicación no es observable desde un solo hilo**: entre el `truncate` del destino y el último byte de una copia hay una ventana que ningún test de un hilo puede ver. Con `shutil.copyfile` el volcado **sí** va al temporal, así que P1 pasa igual. Un `copyfile` hostil que trunca el destino y reventa sí lo distingue. La guarda `ast` que lo acompaña se declara como **red**, no como prueba.
- **P3** espía `json.dump`, **no** `save()`. Con el camino D2 el código correcto y el mutante llaman a `save()` una vez y vuelcan una vez (`save()=1, volcados=1` en ambos): **D2 es indiscriminable por construcción**, así que un espía de llamadas no puede funcionar y no se escribe. Además `load()` escribe **dos veces** (ver `data-models.md` §4.3), lo que hace cualquier umbral de llamadas arbitrario. P3 es complementario y limitado: mata M1/M10, **no** mata M6/M7, y su docstring lo dice.
- **P2/P6/P7** miran la **clasificación** y la **escritura**, nunca el número de llamadas. M7 (`except Exception` en `load()`) los mata P6 y P7, que son los que pasan por `load()`; P2 mata M6 por el lado de `save()`.

### Sondas del arranque de apps: el junction, el hermano de prefijo y la guarda (TASK-027 iteración 2)
El `mutation-auditor` de la iteración 1 dio **FAIL** por cuatro hallazgos. La tabla está
**medida** con `_mutmatrix_t027_iter2.py`: una copia de `src/` en `%TEMP%` por mutación, el
**producto** mutado (nunca la sonda) y **una sonda por subproceso**. Regla de la tabla: una
mutación tiene que morir en la sonda que **declara** esa propiedad; cruzarla con otra que no
la declara no encuentra un agujero, y cuando lo parece, casi siempre es que la otra sonda
afirma algo distinto. Las cuatro cruces informativas están en la salida del script con su
motivo, y ninguna propiedad queda sin sonda: `A1` muere en la del junction, `M10` en la del
hermano, `G1` en la de la guarda.

| Sonda | Invariante | Muerte (medida) | Por qué esa aserción y no otra |
|---|---|---|---|
| **A1–A10** un junction no cuela lo que hay detrás | un junction de **directorio** y un enlace de **fichero** cuyo destino cae fuera de las raíces se rechazan; un `.exe` que apunta a un `.bat` **de una raíz** también; y los dos controles positivos (enlace **dentro** de una raíz, y raíz que **es** un junction) arrancan y devuelven la ruta **real** | A1 (borrar la resolución real), A2 (contención real siempre `True`), A3 (extensión solo en el alias), A4 (`realpath` sin `strict`), A5 (rechazar todo reparse point), A6 (devolver la ruta léxica), A7 (fail-open al no resolver), A8 (raíces léxicas contra la real), A9 (sin motivo en el log), A10 (comparar la léxica contra las raíces reales) | Los enlaces se crean **de verdad** con `mklink` y el helper `_mklink` **falla ruidosamente** si no puede: una sonda que se pone verde porque "el caso no se pudo construir" es peor que no tener sonda. El destino del junction es un directorio controlado fuera de las raíces, **no** `C:\Windows\System32`, porque un `rmtree` que siguiera el enlace borraría `System32`; el `cmd.exe` de verdad se cubre con un enlace de **fichero**, que `os.remove` solo borra a sí mismo. Los controles positivos son lo que impide "arreglarlo" rechazando todo reparse point, que rompe Steam y itch.io. |
| **M10** la contención no acepta un hermano de prefijo | `...Temp\wopt_x` como raíz **no** contiene `...Temp\wopt_xEvil\a.exe`; y `C:\a\b` no contiene `C:\a\b2` | `startswith` en vez de `commonpath` | El hermano se construye **de verdad**, con ficheros reales, para que el rechazo no pueda venir de "no existe": solo puede venir de la contención. Antes de esta sonda la suite entera seguía verde con `startswith` (medido por el auditor): nadie vigilaba `commonpath`. |
| **C1–C3** la contención no depende de la caja | `C:\PROGRAM FILES\x.exe` está dentro de `C:\Program Files` **y al revés**, extremo a extremo con ficheros reales; y `C:\PROGRAM FILES (x86)` **sigue** estando fuera | quitar `normcase`, y quitarlo solo en uno de los dos lados | Las dos direcciones son necesarias: con `normcase` solo en la común, la mitad de los casos sigue falling. El caso negativo `(x86)` es un **hermano**, no una variante de caja, y es lo que impide que un arreglo por "bajar las cadenas" abra la puerta de al lado. |
| **G1–G4** la guarda anti-`shell=True` ve lo que hay que ver | ve `ast.Attribute` (`subprocess.Popen(…)`), el alias de módulo (`sp.Popen`), el alias de import (`abrir`), y un `shell` que no es un literal falso (`shell=1`); **no** marca `shell=False`, `Popen` sin `shell`, `subprocess.run`, ni una cadena que mencione `shell=True` | quitar la rama `ast.Attribute`, quitar el mapa de alias, volver a `value is True`, marcar cualquier mención de `shell` | La guarda anterior solo miraba `ast.Name`: era **ciega a la grafía exacta del bug original**, y sin una sonda que le pase esa grafía "ampliar el visitor" es una intención sin prueba. Los falsos positivos se prohíben a propósito: una guarda que marca de más acaba ignorándose. El mismo helper (`_hallazgos_shell_true`) es el que recorre `src/`, para que no existan dos guarditas con coberturas distintas. |

**Reintroducir el bug en el producto también se mide** (`P1`/`P2`): meter
`subprocess.Popen(ruta, shell=True)` en `_lanzar` mata la sonda de la guarda **y** la sonda
original, y con alias de módulo también.

### Sondas del contenido: el hard link, su hermano y por qué no `st_nlink` (TASK-027 iteración 3)

Este párrafo **decía una razón falsa** y la iteración 3 la cierra. Decía que un **hard link**
(`mklink /H`) "no es un reparse point: ni `realpath` ni `st_file_attributes` lo ven, así que no lo
cierra esta regla. No hace falta cerrarlo". **Las dos mitades estaban mal**: `st_file_attributes`
cierto, pero `st_nlink` **sí** lo ve (vale 2, medido), y —lo que de verdad importa— **el hard link no
era el agujero**: una **copia plena** del mismo `.bat` con nombre `.exe` (`st_nlink == 1`, sin un solo
enlace) se colaba igual. Cerrar solo el raro habría sido seguridad de teatro.

La tabla está **medida** con `_mutmatrix_t027_iter3.py`, con la misma mecánica (una sonda por
subproceso, el producto mutado, nunca la sonda).

| Sonda | Invariante | Muerte (medida) | Por qué esa aserción y no otra |
|---|---|---|---|
| **H1–H5** un hard link no es una hoja y el script no pasa | un hard link real a un `.bat` de fuera y una **copia plena** del mismo `.bat` se rechazan; un PE de verdad arranca; `MZ` sin la firma `PE\0\0` se rechaza; un `e_lfanew` absurdo se rechaza; lo ilegible y lo inexistente se rechazan (fail-closed); y un `.exe` **instalado** con `st_nlink > 1` **sí** arranca | H1 (borrar la regla 9), H2 (la regla existe pero no hace nada), H3 (solo mira `MZ`), H4 (fail-open al no leer), H5 (rechazar cualquier `st_nlink > 1`) | El enlace duro es **real** (`os.link`, la misma llamada que `mklink /H`; sin privilegios, solo mismo volumen) y si no se puede crear la sonda **falla en voz alta**: verde por no construir el caso es peor que no tener sonda. El caso (2), la **copia plena**, es el que hace inútil `st_nlink`: por eso está y por eso se afirma `st_nlink == 1` en él. El control (6) se mide sobre un `.exe` **de verdad instalado** con enlaces duros de verdad, porque la cifra que lo justifica ("el 8,32 % de los `.exe`/`.com` instalados son multi-enlazados legítimos") es una afirmación sobre el software de la máquina, y una sonda que la comprobara con un `.exe` vacío hecho a mano no la comprobaría. |

**La lección de esta iteración, que es la que hay que llevarse:** al añadir la regla 9, los fixtures
que hacían de "una app" eran ficheros **vacíos**, y un `.exe` vacío no es un PE, así que la regla nueva
los rechazaba **por el motivo equivocado**. Dos propiedades dejaron de estar probadas **sin que ninguna
sonda se quejara**: la extensión real (mutación **A3** de la iteración 2, que llegó a sobrevivir) y la
lista blanca (caso (b) del arranque). Se detecta mirando la matriz de la iteración anterior, no la
suite: la suite seguía verde. Arreglo: helper `_escribir_pe_minimo` para que las fixtures sean PEs de
verdad, y el caso (b) ampliado para que **el mismo contenido** con `.bat` no arranque y con `.exe` sí,
de modo que la diferencia la tenga que hacer la extensión y no el contenido.

### Trampa de Windows: `chmod` NO niega la lectura
`os.chmod(0o400)` en Windows activa el atributo **solo escritura**: el archivo sigue siendo
legible (medido: `open(w)` → `PermissionError`, `os.access(W_OK)` → `False`, lectura permitida).
Negar lectura de verdad exigiría ACL (`icacls` = `subprocess`, prohibido por la Trampa #9) o un
handle con `FILE_SHARE_NONE` (no expuesto por la API estándar). Se probaron tres escenarios
solo-filesystem y **ninguno distinguía M6**. Conclusión operativa: **toda prueba de la
clasificación de `OSError` tiene que inyectar el fallo en la costura de parseo**, no confiar en los
permisos del filesystem. Por eso P3 (que sí usa solo-lectura) pone el discriminante en el doble de
`json.dump` y no en el permiso.

### Aserciones tautológicas (TASK-026)
- `assert cat != "? Otros"` en `test_no_system_process_is_killable` **dejó de comprobar nada** al arreglar el literal (FIX-005): comparaba contra un texto que ya no existía en el código. Ahora compara contra `CATEGORY_ORDER[-1]`, el centinela **vivo**.
- El centinela de los tests se construye por codepoint (`chr(0x26AA) + " Otros"`), nunca pegando el glifo, para que el propio test no dependa de cómo se escribió el emoji en el editor.

### Sondas del ciclo 21: cerrar los 16 supervivientes del `mutation-auditor` (TASK-028 iter. 2)

El `mutation-auditor` rompió el código a propósito sobre copias en `%TEMP%` y devolvió **16
supervivientes** y **4 afirmaciones documentales falsas**. Tabla medida por este ciclo
(21 mutaciones, **21 muertas, 0 supervivientes**; `MUT-0` va aparte porque necesita un repo git
propio, no una mutación de fichero):

| Sonda | Invariante | Muerte (medida) | Por qué esa aserción y no otra |
|---|---|---|---|
| **N1** el archivo de `docs/archive` está versionado y no vuelve a la raíz | la norma "nunca borrar, siempre archivar" produce un archivo **en el histórico**, no en el disco de una máquina | **M12** (borrar la excepción `!` de `.gitignore`), **M12b** (dejarlo fuera del índice con `git rm --cached` en un repo scratch), **M13/M13b** (devolver `profiles.json` o `inconsistencies_plan.md` a la raíz), **M14** (README vacío), **M15** (borrar el directorio), **M15b** (README que ya no nombra lo archivado) | **La trampa de `check-ignore`, medida:** sin `--no-index` git mira el índice y un fichero **ya versionado** nunca sale como ignorado (la sonda pasaría con la excepción borrada, o sea sin distinguir nada); y con `--no-index -v` el código de salida es **0 también para un patrón negativo**. Por eso va `-q --no-index` (rc=1 = no ignorado) **con un control negativo** (`saved_processes.json` sí ignorado → rc=0): sin ese control, una herramienta que no distingue daría verde igual. Además el entorno de git se monta como `git_safe_commit.get_env()` (el `.git` real está desacoplado en `%LOCALAPPDATA%`), y **si `git` no se puede ejecutar la sonda falla fuerte**: una guarda que se salta sola cuando no puede comprobar ya no guarda. |
| **N2** la versión no puede desincronizarse (ampliada) | la versión vive en **tres** sitios y no puede haber un cuarto | **M7** (`tasks.json` a `0.0.1`), **M9** (`ver = "9.9.9"` en `woptimizer.spec`), **M10** (`APP_VERSION` a nivel de módulo en `config.py`) | El filtro del escáner de empaquetado pasó de "la línea contiene `version`" a **dos condiciones** (literal semver **y** token de versión, con `\b` para que no entren `Verificar` ni `servicio`): el viejo no veía `ver =`. El escáner de `src/` cubre el **cuarto sitio** en cualquier `.py`, con expectativa derivada del código. |
| **N3** el punto de entrada declara el log antes de los servicios | `setup_logging()` la invoca `__main__.main()` **antes** de instanciar nada | **M4** (borrar la llamada), **M4b** (moverla debajo) | Lee el **AST** y compara **lineno contra lineno**. No se ejecuta `main()` (abriría la UI). Sin esto la suite es un **validador que se deduce a sí mismo**: `run_tests.py` se llama a sí mismo `setup_logging()`, o sea que el punto de entrada del producto le era invisible. |
| **N4** `PROCESS_LIST_FILE` sigue siendo un contrato | la constante existe, vale lo que debe y la usan sus consumidores reales | **M18** (borrarla), **M18b** (apuntarla a otro sitio), **M18c** (un consumidor deja de nombrarla) | Afirma la **existencia sobre el AST antes de importarla**, para que borrarla dé una **aserción** y no un `ImportError` que parece otra cosa. Y nombra a los **tres** consumidores vivos: el cuarto (`smoke_check.py`) está muerto y no se cuenta (D1). |
| **N5** la documentación del blindaje no puede desfasarse | el rango y los 34 nombres de `data-models.md` y `architecture.md` son los **reales** | **M10a** (la doc vuelve a decir `23-38`), **M11** (un comentario desplaza el rango a `33-49`), **M10c** (el código pierde `securityhealthservice`), **M10c-bis** (la doc lo pierde) | Mide con `ast` y **deriva la expectativa del código**, nunca de la doc: un test que compara la doc consigo misma no distinguiría nada, que es justo el defecto que se está corrigiendo. |
| **N6** el log rota con el límite declarado | el handler es un `RotatingFileHandler` con `maxBytes`/`backupCount` | **M3b** (`FileHandler` plano, bien construido) | `type(h) is RotatingFileHandler`, **no** `isinstance`: `RotatingFileHandler` **hereda** de `FileHandler`. Contraste medido: con el mutante aplicado, la sonda vieja (T1) **sigue en verde**; sin N6, la rotación no está probada. |
| **N7** `config.py` no configura nada al importarse | no hay `basicConfig` fuera de una función | **M16** (reinyectarlo a nivel de módulo) | AST **más un control** que demuestra que el detector encuentra `basicConfig` dentro de `setup_logging`: sin ese control, "no hay ninguna" sería el verde de un detector muerto. |

**Mutantes EQUIVALENTES (no se testean, y no es "sin cobertura").** El arquitecto decidió no
testearlos y la auditoría lo **confirma con medición**:

- **M17a (FIX-012):** `True if X else True == True` para todo `X`. Un test ahí sería decorativo.
- **M17b (FIX-016):** el `import sys` local de `quit_app()` se usa una sola vez, después del import.

Un fix equivalente por construcción **no necesita** guarda; lo que no puede es llevar el nombre de
una que no vigila. Queda escrito aquí para que la diferencia entre "sin cobertura" y "no hace
falta" no se pierda en el siguiente ciclo.

### Sondas del ciclo 21, iteración 3: dos huecos de ALCANCE (TASK-028)

Los 16 supervivientes del ciclo 21 ya estaban cerrados. Lo que el `mutation-auditor` encontró en la
tercera vuelta no eran supervivientes sino **huecos de alcance**: la promesa de la documentación era
más fuerte que lo que la sonda media. Dos, y solo dos, eran trabajo real.

**N7 solo veía `basicConfig`.** `architecture.md` §15 promete que `config.py` **no configura nada al
importarse**, y el detector AST buscaba **una sola** llamada. Las tres que el auditor dejó en verde
(`logging.getLogger().addHandler(...)`, `logger.addHandler(...)`, `logging.config.dictConfig({...})`)
son **el mismo defecto con otro nombre de función**: el root se configura como efecto colateral de
importar. El criterio está escrito en el docstring de `_configuraciones_de_logging`, y las dos mitades
importan:

- **configurar** = adjuntar un handler, fijar nivel o formato, o reemplazar la lista `handlers`;
- **obtener** no es configurar: `logger = logging.getLogger(__name__)` —incluso sin argumentos— es
  una asignación normal, y ese `logger` lo importan cuatro módulos y es el punto de contrato. Un
  detector que lo marque acabaría ignorándose (o obligaría a mover el punto de contrato para no
  tener que pensar, que es el invariante equivocado).

| Sonda | Invariante | Muerte (medida, `_mutmatrix_t028_iter3.py`) | Por qué esa aserción y no otra |
|---|---|---|---|
| **N1** el archivo de `docs/archive` no vuelve **a la ruta que la app lee** | si hay documento en `PROFILES_FILE` (`_app_dir()`), es del esquema **vivo**; el v2 archivado ahí es un fallo | **M13c** (copia byte a byte del v2), **M13d** (el mismo v2 **reformateado**: `indent=1`, claves ordenadas), **M13e** (un v2 que **no** es el archivado: otro nombre de preset, `factory` propia), **P1a** (mirar la raíz `packs` en vez de `profiles` → **el mutante escapa**, medido) | **La ruta viva no es la raíz**: `PROFILES_FILE` sale de `_app_dir()`, que en desarrollo es `src/woptimizer/`. El auditor copió el v2 archivado ahí y la suite siguió verde. Y ahí no es un fichero inerte: `load()` tiene **rama legacy**, así que la app lo abriría de verdad. Por eso la aserción es **sobre el contenido** (`__system_gaming__`, `factory`, `kill_low_chat` no existen en `models.py`) y **no** "no existe": en la ruta viva vive el `profiles.json` de estado local que escribe la propia app, y exigir su inexistencia sería **una sonda que falla siempre**. M13d y M13e son los que demuestran que se mira el **contenido** y no la igualdad de bytes. |
| **N7** `config.py` no configura nada al importarse | ninguna llamada de nivel de módulo que **configure** el logging | **M16b** (`logging.getLogger().addHandler(...)`), **M16c** (`logger.addHandler(...)`), **M16d** (`logging.config.dictConfig`), **M16e** (`logging.config.fileConfig`), **M16f** (`logging.getLogger().setLevel(...)`), **M16g** (`root.handlers[:] = [...]`), **M16h** (`root.handlers.clear()`), **M16i** (`logger.setLevel(...)` sobre un logger nombrado), y para la sonda: **P7a** (detector muerto), **P7b** (detector demasiado amplio), **P7c** (parte A anulada + detector amplio), **P7d** (parte A anulada + M16b: **el mutante escapa**, medido) | El detector se **prueba contra sí mismo** con código sintético en las dos direcciones: 8 formas ilegales que tiene que marcar y 6 legales que no puede marcar. Un detector que no ve nada y uno que ve de más dan el **mismo verde**, y sin las dos tablas no se sabe cuál de los dos se tiene — que es exactamente por lo que este ciclo existe. Las tablas son un **control del detector, no del fichero**: por eso `P7d` mide que la parte A es la que lleva el veredicto. |

**M10 (categoría) queda como DEUDA ACEPTADA, y es una decisión, no un olvido.** El escáner de
versión no pilla un semver en una línea sin token de versión (`set TAG=9.9.9` en `build.bat`,
`release = "9.9.9"` en el `.spec`). El `mutation-auditor` lo dictaminó **aceptable**: ya está escrito
en `architecture.md` §15 y en la spec, y la consecuencia es **desincronización de la versión de
empaquetado**, no seguridad ni datos. **No se arregla en esta iteración**; queda aquí para que el
siguiente que lo lea no lo scourta como una forgot.

**Punto 5: `run_tests.py:8` reemplaza `sys.stdout` (preexistente, NO se cambia).**
`sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')` deja el `sys.stdout` **original**
sin ninguna referencia que lo cierre, y su wrapper sustituto **cierra el buffer subyacente al
liberarse**. Importar `run_tests` desde **otro** proceso es lo que dispara eso: cuando el proceso
importador termina, el buffer del host se queda cerrado y **todo lo que el host escriba después sale
roto**. Le costó un ciclo entero de depuración. **No se toca** (arriesga tumbar el runner entero), pero
queda anotado como **trampa para el próximo que escriba un validador que importe la suite**: si un
script tiene que importar `run_tests` para reutilizar una sonda, que lance la sonda en un
**subproceso** (`python -c "import run_tests; run_tests.<sonda>()"`, cwd = raíz del repo) y no en el
propio proceso. Es exactamente la mecánica de `_mutmatrix_t028_iter3.py`.

### Sondas del ciclo 21, iteración 4: los **falsos positivos que matan datos del usuario** (TASK-028)

La iteración 3 cerró huecos de **alcance** (la promesa era más fuerte que la sonda). La iteración 4
cierra lo contrario y es más grave: **dos sondas afirmaban sobre ficheros del usuario**. Un test que
mata de más no es "una guarda demasiado estricta": es una guarda que puede decirle a alguien que su
configuración está rota. Estas cuatro se arreglan, no se documentan.

**S1 (DATOS) — la sonda N1 tumbaba la suite ante un `profiles.json` corrupto o vacío, y pedía
borrarlo.** El `except ValueError → raise AssertionError` sobre el `PROFILES_FILE` **real** convertía
un estado que **la app ya tolera** (el corte de luz, el antivirus que trunca a 0 bytes, el editor que
guarda a medias) en un fallo de la suite. El mensaje era lo peor: reconocía el caso ("la app tampoco lo
abriría: lo marcaría como dañado y arrancaría con cero packs") y aun así terminaba con *"se borra y la
app lo regenera"*. **Una sonda jamás debe terminar con una instrucción de borrar el fichero del
usuario.** Ahora: si el documento no se puede leer, **no se afirma nada** y se avisa por `print()`
como observación, con la ruta y el motivo. El JSON válido es un **requisito de la comprobación**, no
una exigencia al usuario.

**S2 (DATOS) — N1 declaraba "v2 retirado" ante un `profiles.json` legítimo con un campo de usuario
llamado `factory` o `kill_low_chat`.** `Pack` es `extra="allow"`: esos nombres son un documento
**válido** que la app abre sin quejarse, y la condición `{"factory","kill_low_chat"} & set(registro)`
aplicada a cualquier registro bastaba para declararlo —y para pedirle que lo borrara. El criterio
ahora es la **combinación**, medido contra el `docs/archive/legacy-root-data/profiles.json` real
(420 B): los rasgos se cuentan **dentro del mismo registro** y hacen falta **dos o más** —
la clave `__system_gaming__`, el campo `factory`, el campo `kill_low_chat`, y `kind: "system"`. El
archivado acumula los cuatro. **Un discriminante único es frágil por definición**, porque es
exactamente el nombre que un usuario puede elegir. El riesgo residual, dicho en voz alta: un pack de
usuario que declarase **`factory` y `kill_low_chat` a la vez** en el mismo registro seguiría activando
la guarda; es un precio conscientemente aceptado a cambio de no perder el v2 real.

| Sonda | Invariante | Muerte **medida** (`_mutmatrix_t028_iter4.py`) | Controles **positivos** (lo que NO puede morir) |
|---|---|---|---|
| **N1** el v2 retirado no vuelve a la ruta que la app lee | si el documento de `PROFILES_FILE` se puede leer, su firma de v2 (raíz `profiles` + **dos** rasgos en el mismo registro) tiene que estar ausente | **M13c** (archivado byte a byte), **M13d** (el mismo v2 **reformateado**: `indent=1`, claves ordenadas), **M13e** (un v2 que **no** es el archivado: otro nombre de preset, `factory` propia) | **P1a** JSON inválido, **P1b** fichero **vacío (0 B)**, **P1c** JSON que no es un mapa → **VERDE**, con el aviso impreso. **P2a** campo de usuario `factory`, **P2b** `kill_low_chat`, **P2c** un pack que se llama `__system_gaming__` pero sin campos del v2, **P2d** un campo de usuario en cada uno de dos packs → **VERDE**. **P3a** el detector vuelto a "un campo basta" + un campo de usuario → **ROJO por el control positivo**; **P3b** el detector anulado (`return False, []`) → **ROJO por el control negativo**. |
| **N7** `config.py` no configura nada al importarse | ninguna llamada que **configure** el logging se ejecute al importar: ni en la cima, ni en un `if`/`try`/`for`/`while`/`with` de módulo, ni en el **cuerpo de una clase** | **S3** (el logger nombrado dentro de un `try` de módulo + `addHandler` a nivel de módulo), **S4** (`addHandler` en el cuerpo de una clase) | **P7e** S3 revertido + tabla `ILEGALES` saltándose S3/S4 + mutante S3 → **ESCAPA (VERDE)**: prueba que la muerte la aporta el arreglo S3 y no otra cosa. **P7f** ídem con S4 → **ESCAPA**. **P7g/P7h** los dos revertidos **con** la tabla intacta → **ROJO por la propia autocomprobación** del detector (que es lo que se quiere: el detector se delata a sí mismo). |

**La trampa del mutante S3 que casi mide lo contrario (medido, no supuesto).** La primera versión del
mutante era `if __name__ == '__main__': logger_mut = logging.getLogger(...)` + `logger_mut
.addHandler(...)`. Eso **no es un mutante válido**: al **importar** `config.py` el `__name__` no es
`'__main__'`, la asignación no se ejecuta y el módulo revienta con `NameError: name 'logger_mut' is
not defined` — la suite muere en **0,2 s** y sin ninguna aserción. Un mutante que revienta el módulo
produce un **falso positivo de muerte** idéntico al de un mutante que muere de verdad. La forma
correcta es la que asigna **siempre** al importar (`try/except` con la misma asignación en las dos
ramas, y el `.addHandler()` al nivel de módulo después), que es además la forma realista.

**Deuda de LECTURA, medida y NO arreglada (decisión del `mutation-auditor`, con SHA-256).**
`test_headless_ui()` instancia `PackService()` **sin `data_path`** sobre el `profiles.json` real, lo
que parece una escritura en estado del usuario. **Medido con SHA-256 antes/después en los tres
escenarios** (legítimo, corrupto y v2): los bytes son **idénticos**, no se crea ningún `.bak` ni
`.tmp`, y las 5 llamadas a `save()` están en **métodos de acción de usuario**, ninguna en el
arranque. Es deuda de **lectura**, no de escritura, y **no se arregla**: tocarlo arriesga el
arranque por un riesgo que no existe. Queda escrito para que el próximo que lo lea no lo confunda con
un descuido.


## Iteración 5 — la rama «ilegible» de N1 era código muerto (F1)

La iteración 4 dejó N1 prometiendo que un `profiles.json` **ilegible da aviso y no tumba la suite**, y
ese texto estaba literalmente en el `proposal.md` §3.1. **Era falso.** El `open()` y el `read()`
estaban **fuera** del `try`, así que el `except (OSError, UnicodeDecodeError)` **no podía ejecutarse
nunca**: no era un mensaje feo, era una guarda que no guardaba.

### El patrón general, y por qué se mide así

Una muerte por **traceback** prueba que el código se rompió, **no** que afirmara lo correcto. Un
`try/except` que devuelve `("", "")` en todo caso también pasa. Por eso el arreglo va con un control
que **escribe de verdad** los ficheros ilegibles y exige una respuesta sobre su **texto**, y no
«que no reventara».

| Estado sembrado en la ruta viva | Antes | Ahora |
|---|---|---|
| bytes que no son UTF-8 | ROJO (`UnicodeDecodeError` en el `read()`) | **aviso** |
| truncado a mitad de un emoji de 4 B | ROJO (`UnicodeDecodeError`) | **aviso** |
| sin permiso de lectura | ROJO (`PermissionError` en el `open()`) | **aviso** |
| el literal JSON `null` | VERDE, con el motivo **vacío** | aviso con motivo |

El escenario es real, no hipotético: el `profiles.json` vivo del usuario tiene un `U+1F680`
(`F0 9F 9A 80`), y un corte de luz o un antivirus que trunca ahí produce exactamente ese fichero.
Y la **asimetría con la app** se midió contra `pack_service.py:40-41`, que **sí** incluye
`UnicodeDecodeError` en `CORRUPTION_ERRORS`: con el mismo fichero y un `.bak` válido, la app
**arranca y recupera** (`packs: ['gaming']`) en los tres casos, y la sonda moría en dos.

### Dos detalles que no son detalles

1. **El orden de las ramas es la mitad del arreglo.** `UnicodeDecodeError` es **subclase de
   `ValueError`** (`issubclass(UnicodeDecodeError, ValueError) is True`, medido), así que con
   `except ValueError` primero la rama de lectura **vuelve a ser inalcanzable para la
   decodificación**: el `read()` ya no revienta, pero el aviso culparía al JSON de un fallo de bytes.
   Mover el `open()` sin invertir el orden **no cierra F1**, y está medido como mutante.
2. **`json.loads("null")` devuelve `None` sin lanzar.** El `motivo` se quedaba vacío y el aviso se
   leía *«Hay un profiles.json local en X **y .** La app lo tolera»*. No es una aserción, pero es un
   texto que se lee.

La lectura se movió a una función, `_leer_documento_de_packs()`, **para que el control pueda
ejercitar el mismo código que corre**: un control que reescribiera la lógica probaría una copia, que
es el validador que se deduce a sí mismo.

**Matriz de F1/D1** (`wopt_matrix_f1.py`, copia a `%TEMP%` sin el puntero `.git`, `__pycache__`
purgada, suite en subproceso). Controles positivos: el vivo legítimo se lee y sale VERDE; los tres
ilegibles dan aviso; el v2 retirado se sigue detectando (ROJO).

| Mutante | control_vivo | no_utf8 | Muere por |
|---|---|---|---|
| `M-F1a` `open()`/`read()` fuera del `try` | ROJO | ROJO | el control de alcanzabilidad |
| `M-F1b` la rama de lectura se queda solo con `OSError` | ROJO | ROJO | el control de alcanzabilidad |
| `M-F1c` orden de las ramas al revés | ROJO | ROJO | el motivo blamed al JSON |
| `D1` sin la rama del literal `null` | ROJO | ROJO | el control del `null` |
| `P` helper que declara **todo** ilegible | ROJO | ROJO | **el control positivo** |

Las diez filas salen ROJO. El orden de los controles importa y se puso a propósito: el **positivo va
antes que el del `null`**, para que un helper muerto por completo muera por su propia causa y el
control positivo no se quede sin comprobar nunca.

El `PermissionError` del control se provoca con un **directorio** con el nombre del fichero, no con
`os.chmod`: en Windows `chmod` no impide la lectura, y un control que no controla nada es peor que
ninguno.

### D3 y D4 — el detector de logging tenía dos criterios que no eran los que decía

**D3: el `def` se saltaba su propia firma.** `visit_FunctionDef = pass` se saltaba los argumentos
por defecto y los decoradores, que **sí se evalúan al definir la función**. Medido en este
intérprete (`root.handlers` tras importar, sin ningún `setup_logging`):

| Forma | ¿configura al importar? |
|---|---|
| `def f(h=logging.basicConfig(force=True))` | **sí** (1 handler) |
| `class C: def m(self, h=logging.basicConfig(...))` | **sí** |
| `f = lambda h=logging.basicConfig(force=True): h` | **sí** |
| `def f(*, h=logging.basicConfig(force=True))` | **sí** |
| `def f(h: logging.basicConfig(force=True))` (anotación) | **sí** |
| la anterior **con** `from __future__ import annotations` | **no** (0) |
| `def f(): logging.basicConfig(force=True)` (cuerpo) | **no** (0) |

El disparo es bajo pero **real**, no ≈0. El arreglo recoge la **firma** y deja el **cuerpo**, que es
la frontera que S4 y la iteración 3 ya tenían medida. Las anotaciones se saltan con
`from __future__ import annotations`, porque entonces se guardan como texto y marcarlas sería un
falso positivo sobre documentos legítimos (`NamedTuple`, `TypedDict`).

**D4: un generador perezoso no es una comprehension.** El elemento de un generador **no** se ejecuta
al importar (`0` handlers), mientras que el de una list comp sí (`1`). Marcarlo era un falso
positivo: código que no configura nada. El arreglo recorre **solo el iterable de entrada** del
generador, que es lo único que se evalúa al crearlo — y `[logging.basicConfig(...)]` en ese iterable
**sí** dispara (la lista se construye entera), así que la fila queda en `ILEGALES`.

**Matriz de D3/D4** (`wopt_matrix_d3d4.py`): las seis mueren por la **autocomprobación** de las
tablas `ILEGALES`/`LEGALES`, que es exactamente lo que se quiere: el detector se delata a sí mismo.
Control positivo: sin mutación, VERDE y con el recuento **derivado** (20 ilegales / 14 legales).

| Mutante | Muere por |
|---|---|
| `M-D3a` el `def` de módulo no se mira | falso negativo: no marca el argumento por defecto |
| `M-D3b` solo se miran los decoradores | falso negativo: idem |
| `M-D3c` sin anotaciones | falso positivo: marca una anotación con `__future__` |
| `M-D4a` el generador se recorre entero | falso positivo: marca el elemento perezoso |
| `M-D4b` el generador no se mira | falso negativo: no marca el iterable de entrada |
| `M` el `__future__` se ignora | falso negativo: no marca la anotación sin `__future__` |

**El recuento del `print` se deriva ahora de `len(ILEGALES)`/`len(LEGALES)`.** Estaba escrito a mano
(«14 ilegales, 10 legales») y era un número que mentía en cuanto se añadía una fila: el mismo patrón
de doc que miente, aplicado al propio mensaje de la sonda.

### D2 — por qué el detector solo mira la raíz `profiles`

El detector del esquema v2 retirado mira **únicamente `doc["profiles"]`**, no la raíz entera, y eso es
correcto por una razón concreta del producto, no por comodidad: la rama legacy de
`pack_service.py:403/420` **solo se engancha ahí** (`raw_data['profiles']`, con
`k == "__system_gaming__"`). Un `profiles.json` con un pack de usuario que declare `factory` **y**
`kill_low_chat` en la raíz **viva `packs`** no lo resucita, porque `load()` no mira esa raíz para
detectar el esquema retirado. **El riesgo residual existe pero es más estrecho de lo que parecía**,
y el detector **no se cambia** por ello.

## Ciclo 27: el alcance de un detector se deriva, o no es un detector (TASK-037)

Este ciclo no toca el producto: es el turno de la rotación que le toca al **tooling que vigila al
producto**, y los tres hallazgos que cierra son **la misma afirmación escrita en tres sitios** —
*una promesa de cobertura escrita a mano que nadie mide*.

### La regla que gobierna el diseño

> Lo que un detector promete es «todo lo que hay». Para que eso sea cierto, su alcance tiene que
> **derivarse** de la realidad, y la derivación tiene que **compararse** contra la realidad medida
> con `ast`.

| el alcance estaba escrito a mano | qué pasaba al mutarlo |
|---|---|
| el estado `None` estaba escrito en la rama; el productor no lo emitía | la rama se quedaba **muerta en verde** |
| los ficheros que había que mirar estaban en una tupla literal | la lista desfasada **no daba síntoma**: el tercer módulo hoy no viola nada |
| que el alcance sea el correcto **no se comprobaba en ninguna parte** | el guard podía volverse rama muerta y la suite seguía verde |

### 1. La rama `if n_tests is None:` era código muerto (no «un agujero de seguridad»)

`validate_docs.py` declaraba esa rama para el caso «no se puede derivar el número de tests», y su
productor `_recuento_de_tests` **no tenía ni un `return None`**: o devolvía la 4-tupla o propagaba.
Medido: con la fuente rota lanza `IndentationError` (subclase de `SyntaxError`) y con el fichero
ausente `FileNotFoundError`. Las dos rutas salían con **traceback en vez de informe**.

**Rigor en el informe**: esto **no produce falso verde**. `main()` termina con
`sys.exit(0 if not errors else 1)`, así que una excepción sin capturar sale con rc=1 y nadie puede
leer un `0 FAIL` donde no lo hay. Es un agujero de **diagnóstico**, no de detección, y la severidad
es 🟡 por eso.

El arreglo es el **productor** (`except OSError` sobre el `open()`, `except SyntaxError` sobre el
`ast.parse()`), **no la rama**: la rama ya estaba escrita para el contrato correcto, y editarla sería
dejar la expectativa a mano con un productor que no puede cumplirla. El `except` es `SyntaxError` y
**no `IndentationError`** porque este es subclase: estrecharlo deja fuera `TabError` y reabre el
mismo agujero por el otro lado (medido: las dos subclases aparecen con fixtures reales).

Y el **refactor mínimo** que lo hace testeable: `_comprobar_recuento_de_tests(root, errors, ok)`.
Sin raíz, esa rama solo se despertaba lanzando el validador entero contra el repo entero — es decir,
nunca. Una rama que existe y nadie ejecuta es *exactamente* el defecto que se iba a arreglar, un
nivel más abajo.

### 2. El guard de los llamantes: de la tupla de dos ficheros a un alcance derivado

La tupla literal `("views/dashboard_view.py", "views/pack_manager_view.py")` **no era una lista de
ficheros**: era una **apuesta sobre qué ficheros importan `feedback`**, y la apuesta tenía un fichero
mal. Medido con `ast` sobre `src/woptimizer/`: **tres** importadores.

**Y esa apuesta no daba ningún síntoma.** `process_manager_view.py` solo importa `mensaje_cierre_pack`,
que el guard no vigila, así que corregir la lista a mano con los tres ficheros reales **no cambia
ningún resultado**. Ese es el motivo de que el control vaya sobre un **árbol sintético**: es lo
único que distingue «derivé el alcance» de «escribí el alcance correcto a mano».

El guard quedó en dos funciones de módulo con **raíz como parámetro**:

* `_modulos_que_importan_feedback(raiz_paquete)` recorre `raiz_paquete/**.py` con `ast` y devuelve
  los que importan el módulo `feedback`. Es **total por construcción**: un módulo que no importa
  `feedback` no puede llamar a sus formateadores, así que no hay lista que mantener.
* `_guardar_contrato_de_llamantes(raiz_paquete, acciones_validas)` aplica el contrato y falla
  nombrando **fichero y línea**. Si el alcance apunta a un fichero que no existe, eso **también** es
  un `AssertionError`: un alcance que no se puede leer es una apuesta, y una apuesta que se salta en
  silencio es peor que no tener guard.

### 3. Dos ceguidas de la MISMA causa, encontradas al escribir el control

Las dos son «mirar una sola forma de la escritura»:

| forma | nodo | qué hacía el guard de antes |
|---|---|---|
| `from woptimizer.ui.feedback import mensaje_sin_apps(...)` | `ast.Name` | la veía |
| `fb.mensaje_sin_apps(...)` tras `import feedback as fb` | `ast.Attribute` | `getattr(func,"id",None)` → `None` → **`continue`** en silencio |
| `from woptimizer.ui import feedback as fb` | `ImportFrom` con `module="ui"` y alias `feedback` | el módulo **no entraba en el alcance** |

La segunda y la tercera son **la misma forma escrita de dos maneras**, y juntas son el agujero
latente que la auditoría del ciclo 26 no vio: la forma **idiomática** de importar el módulo entero
era invisible para el guard, justo la forma que hace posibles las llamadas `fb.mensaje_...` que
tampoco se veían. Ninguna de las dos daba síntoma en `src/` (no hay ninguna llamada así), y por eso
solo un árbol sintético las destapa.

### La matriz de este ciclo

Los nueve mutantes, todos por `AssertionError` (**no** por crash, que es lo que exige la lección del
ciclo 26):

| mutante | control que lo mata |
|---|---|
| M1 `except (OSError, SyntaxError)` → `except OSError` | fixture de sangría rota, vía el envoltorio que convierte el crash en aserción |
| M2 → `except SyntaxError` | fixture de fichero ausente, ídem |
| M3 la rama `n_tests is None` muerta | los fixtures dejan de dar línea `[FAIL]` |
| M4 `errors.append` → `ok.append` | ídem, y además el resumen contaría un OK donde hay un fallo |
| **M5 el alcance vuelve a una tupla literal** | el árbol sintético tiene un **cuarto** módulo que ninguna tupla del repo real contiene |
| M6 el guard vuelve a mirar solo `ast.Name` | el módulo que llama en forma `fb.mensaje_sin_apps(...)` |
| M7 el guard marca todo | el control negativo: `pack.default_action` y `"start"`/`"kill"` no se pueden marcar |
| M8 el recorrido se limita a `ui/views/` | el módulo que cablea el verbo está **fuera** de `views/` |
| M9 vuelve el segmento con lista vacía | el fixture de test definido y no invocado |

**El control negativo no es opcional**: sin él, un guard que marcara todo daría el mismo verde que
uno que no ve nada, que es la razón por la que un detector necesita las **dos** direcciones.

**Un mutante de control que hay que correr**: M5 **más** M4 a la vez. Si uno muere solo por el otro,
hay una dependencia invisible entre la rama y el alcance. Medido en este ciclo: cada uno muere por su
propia aserción y el par combinado muere en la primera que se encuentra, así que **no se solapan**.

### Cómo se auto-instrumenta un guard (el patrón, para el que venga)

1. El guard se extrae a una **función de módulo que recibe la raíz**. Sin raíz no hay control: hay
   que apuntarla al repo entero.
2. El alcance se **deriva** con `ast`, y una entrada del alcance que no se puede leer es un fallo
   explícito, no un salto.
3. Se escribe un **árbol sintético** con un módulo de más que el repo real, **fuera** del
   subdirectorio que el guard recorre por costumbre, y con un módulo más que **no** entra en el
   alcance (control negativo).
4. Se cubre **cada forma de escribir** la llamada y **cada forma de importar** lo vigilado. Una
   forma sin cubrir es un agujero latente con la misma causa que el que se acaba de cerrar.
5. Las llamadas del test al guard van envueltas en `try/except Exception → AssertionError`, para que
   un mutante muera **por la aserción** y no por un traceback que el runner cuente como muerte sin
   distinguir el motivo.

## Hallazgo abierto (fuera de alcance, declarado)

**Un `PermissionError` en la ruta viva tumba `test_headless_ui`, y no es la sonda.** No es
`run_tests.py`: es `PackService.__init__` → `load()` → `_read_json()`, que abre el fichero en
`pack_service.py:379` **sin ninguna protección** frente a `OSError`, y `CORRUPTION_ERRORS`
(`pack_service.py:40-41`) **no incluye `PermissionError`** — solo `UnicodeDecodeError` y los de JSON.
Es decir: **la app no tolera un `PermissionError`**, a diferencia de la corrupción de bytes, que sí
recupera del `.bak`. Se deja escrito porque el siguiente que lo lea lo interpretaría al revés
(«la sonda es la que revienta»). Arreglarlo exige tocar `src/`, que el encargo de esta iteración
prohíbe; la **sonda** sí queda correcta: avisa y no muere, que es lo suyo.


Python reutiliza un `.pyc` obsoleto cuando el mutante tiene la **misma longitud en bytes** y el
**mismo segundo de `mtime`**. Purgar `__pycache__` entre mutaciones no es hygiene: sin purga, un
veredicto de muerte puede salir **falso** (el test pasa contra el código viejo) y una muerte puede
atribuirse a la mutación equivocada. La segunda trampa es la repo scratch: el `.git` de este
proyecto es un **fichero** (puntero al gitdir desacoplado), así que copiar el árbol a `%TEMP%` y
correr `git init`/`git add`/`git rm` ahí cae al **índice real** y modifica el staging del
proyecto. Se excluye el fichero `.git` de la copia y se verifica `git rev-parse
--absolute-git-dir` antes de tocar nada.

## Deuda técnica: tests heredados v2
En la raíz del repo conviven **11 ficheros `test_*.py` heredados** que están **muertos**:

`test_categorization.py`, `test_debug_list.py`, `test_gaming_profile.py`, `test_gaming_session.py`, `test_harness.py`, `test_harness_v2.py`, `test_kill_expansion.py`, `test_kill_real.py`, `test_powershell_direct.py`, `test_profiles.py`, `test_relaunch_grouping.py`.

- Los 11 hacen `import process_manager as pm` a nivel de módulo. `process_manager` es un módulo de la **v2** que ya no existe en `src/woptimizer/`, así que todos fallan con `ModuleNotFoundError` en la línea de import, antes de ejecutar un solo test.
- La suite actual usa `services/process_service.py` (psutil) y `services/pack_service.py`; no hay equivalente de `process_manager` en v3. Existe `ui/views/process_manager_view.py`, pero es una vista de UI y no el módulo que esos tests necesitan.
- **No se borran por decisión expresa del propietario**: son referencia histórica y retirarlos no aporta valor frente al riesgo de perder contexto.
- **No se ejecutan** y **no se modifican**. No forman parte de la CI ni de la verificación de calidad.
- **No cuentan como cobertura.** La cobertura real y viva del proyecto vive **únicamente en `run_tests.py`**.

Consecuencia práctica: al añadir cobertura, **editar siempre `run_tests.py`**. Un `test_*.py` nuevo en la raíz no se ejecutará y dará una falsa sensación de cobertura.

