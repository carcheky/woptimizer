# Guía de Pruebas y Validación para Agentes IA

## Los finales de línea de los ficheros del arnés, MEDIDOS (TASK-069, ronda 2)

Antes de escribir un arnés de mutación hay que saber en qué está el fichero que se va a
anchorar, porque una ancla con `\n` pelado **no aplica** contra un fichero en CRLF y el
mutante no se pone: el veredicto sale "no ha muerto" y lo que en realidad es un arnés que
no ha hecho nada. MEDIDO en este host el 2026-10-05 con `git ls-files --eol` y contando
bytes; **REMEDIDO el 2026-10-22**, cuando `validate_docs.py` paso a LF y su fila seguia
diciendo CRLF (un arnes anclado con `\r\n` no aplicaba NINGUN mutante y todos salian
"no ha muerto", que es un arnes que no ha hecho nada):

| Fichero | En el árbol de trabajo | Declarado | Ancla del arnés |
|---|---|---|---|
| `run_tests.py` | **LF** (0 CRLF, 32 435 LF) | `* text=auto eol=lf` | `\n` pelado |
| `validate_docs.py` | **LF** (0 CRLF, 3 446 LF) | `* text=auto eol=lf` | `\n` pelado |
| `pack_service.py` | LF | `eol=lf` | `\n` pelado |
| `.gitattributes` | LF, `i/lf w/lf` | se declara a sí mismo `text=auto eol=lf` | — |
| `build.bat` | **LF**, con `*.bat text eol=crlf` declarado | — | es la fila viva de `STATUS.md` |

Dos trampas, ambas medidas y ambas ya pagadas por alguien:

- **"`.gitattributes` declara `eol=crlf`" es FALSO.** No se declara a sí mismo: lo cubre
  `* text=auto eol=lf`, y solo `*.bat`, `*.cmd` y `*.ps1` llevan `eol=crlf` a la fuerza.
  Medido: `.gitattributes` sale `i/lf w/lf attr/text=auto eol=lf`. Un documento que diga
  lo contrario es un documento que miente, y hay que corregirlo en vez de heredarlo.
- **"`run_tests.py` es CRLF" fue verdad y hoy es FALSO.** Lo medido ahora es `w/lf`. Quien
  monte un arnés en binario "por si acaso" no rompe nada, pero quien afirme el dato en un
  informe está describiendo un árbol que ya no existe. `validate_docs.py` **sí** sigue en
  CRLF, y esa es la que importa: es la que hace que un arnés de anclas con `\n` no aplique y
  el mutante parezca superviviente.

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
Ejecutar con `python run_tests.py` (PowerShell: `$env:PYTHONIOENCODING="utf-8"`). Contiene **235 tests**: 159 de backend + 76 headless de UI.

> **REGLA de TASK-081 (ciclo 67): el ALCANCE de un guard se DERIVA del arbol; nunca se escribe a mano.**
> MEDIDO antes del arreglo: `verify_ui_syntax.py` enumeraba DIEZ rutas escritas a mano y el arbol de
> `src/woptimizer/` tenia mas. Las que faltaban eran `ui/theme.py` y `ui/tray_menu.py`, y en camara
> desechable **con control positivo** los dos rotos daban **exit 0, VERDE**: el guard discriminaba
> sobre su lista y no veia nada fuera de ella. Corria en **CI** y no tenia **ni una contraprueba** en
> toda la suite.
>
> La propiedad que se blinda NO es el caso, es la forma: **un guard es vaciable cuando el conjunto que
> mira esta escrito como enumeracion literal DENTRO del propio guard, y ese conjunto es un dato
> DERIVADO del sistema de ficheros.** Enumeracion y conjunto son dos fuentes de verdad que nadie ata.
>
> Tres reglas que salen de ahi, y las tres son de este repo:
>
> 1. **Se deriva, no se enumera.** El sujeto se recorre con `rglob("*.py")`. Sin lista de exentos
>    tampoco: una lista de exentos es una lista mas que envejece, y degrada el guard en la rama
>    principal porque las comprobaciones especificas solo se aplican a la rama principal.
> 2. **La cifra tambien.** `verify_ui_syntax.py` imprime `ALCANCE_DERIVADO=N` y `STATUS.md` declara esa
>    cifra, atada a lo que el script **imprime** por `test_el_recuento_de_modulos_de_sintaxis_es_derivado`.
>    Una cifra atada a su derivado avisa con el numero bueno al lado del malo; una cifra ausente no dice
>    nada. Y una cifra que nadie comprueba es exactamente la que este repo ha pagado tres veces (8/8,
>    9/9 y 10 para el mismo conjunto).
> 3. **La contraprueba mira el PRODUCTO, no la fuente.** Comparar `rglob` contra `rglob` es
>    **tautologico**: las dos mitades serian la misma expresion y el guard no mediria nada. El sujeto
>    es `verify_ui_syntax.py` **ejecutado** contra un arbol sintetico de `%TEMP%` con un modulo NUEVO
>    roto, que exige `exit 1` nombrando el modulo, mas su **control positivo** (arbol sano -> `exit 0`).
>    Sin el control positivo, AC-3 lo cumple un script que sale siempre con 1: es el mutante `S2` que
>    sobrevivio en el ciclo 66.
>
> Y la forma que **NO** vale para tapar una enumeracion pre-existente: meterla en una lista muda de
> permitidos. La tolerancia de `test_ningun_guard_enumera_el_arbol_de_src_que_ya_esta_en_el_sistema_de_ficheros`
> es el **docstring del propio guard**, con las dos frases exigidas -- (a) por que existe la
> enumeracion y (b) que la retira -- y con texto de verdad detras de cada marcador. Ese guard
> **denuncia, no repara**: nombrar la deuda la hace visible; repararla es del ciclo que la recoja.

> **Aviso de TASK-073: NO "arregles" el guard de los workers metiendo la puerta nueva en `PERMITIDOS`.**
> Cuando los diez `self.after(0, ...)` de `views/` pasaron a `self._publicar_en_el_bucle(0, ...)`,
> `test_los_workers_de_pack_solo_publican_por_after` se puso en rojo, porque su rama era
> `if raiz != "after": ... infraccion`. El arreglo de una línea —añadir
> `("_publicar_en_el_bucle", "_publicar_en_el_bucle")` a `PERMITIDOS`— **degrada el guard**: las
> comprobaciones de 0 ms y de callback en la lista blanca (`CALLBACKS`) solo se aplican a la rama
> `raiz == "after"`, así que a partir de ese momento un worker podría publicar a 3000 ms y a un
> callback cualquiera sin que nadie lo viera. Lo correcto fue una **rama nueva** que exige
> exactamente lo mismo a las dos puertas, y su contraprueba vive dentro del propio test
> (control 9: `3000` ms y un callback fuera de la lista tienen que salir marcados). Regla
> general: **un guard que no mide es peor que no tener guard.**

> **La numeración de la tabla NO es el orden de registro del `__main__`, y antes de TASK-070 este
> documento afirmaba que sí.** MEDIDO el 2026-10-06 comparando con `ast` las llamadas `test_*` del
> `__main__` contra las filas: la fila 141 es `test_la_puerta_de_paridad_va_despues_de_validar_repo`,
> que se **registra en la posición 144**. El orden real de la tabla es el de alta de cada ciclo, y las
> filas nuevas se **añaden al final** para no renumerar las anteriores. El único número que importa
> es que la tabla tenga **una fila por test**, y eso lo deriva `validate_docs.py` con `ast`. La
> columna de reparto (`backend` / `headless`) **tampoco** se deduce de "tooling puro": lo decide la
> **posición respecto al marcador**, y `TASK-070` es el contraejemplo vivo —sus dos sondas no abren
> ventana y son tooling puro, y van **delante** del marcador por eso puntúan como backend.

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
| 17 | `test_pack_service_delete` | `delete_pack`: `ValueError` en gaming, `False` si no existe, `True` en pack propio |
| 18 | `test_pack_service_favorites_acumulan` | **TASK-048 (Ciclo #38):** Favoritos acumulativos en `PackService.set_favorite()`, persistiendo múltiples favoritos sin exclusividad global |
| 19 | `test_pack_service_reset_gaming` | `reset_gaming_pack` restaura apps y `target_categories` de `DEFAULT_GAMING_PACK` |
| 20 | `test_gaming_pack_lists_isolated_from_global` | Las listas del pack gaming **no** comparten objeto con `DEFAULT_GAMING_PACK` (regresión de `model_copy()` shallow) |
| 21 | `test_cache_ttl_and_invalidation` | Dentro del TTL se devuelve el **mismo objeto**; `invalidate_cache()` y `force_refresh=True` re-escanean |
| 22 | `test_kill_recursive` | Kill recursivo: el nieto Python muere junto al padre (invariante de AGENTS.md) |
| 23 | `test_git_safe_commit_fail_safe` | Códigos de salida 0/1/2/3 y línea canónica `WOPT_*` de `git_safe_commit.py` |
| 24 | `test_double_tap_guard` | `DoubleTapGuard` exige segunda pulsación, con auto-revert y token de intención |
| 25 | `test_no_system_process_is_killable` | Blindaje anti-brick: ningún proceso de Familia A es cerrable por JSON, servicio ni kill |
| 26 | `test_gaming_pack_fallback_is_deep_copy` | **TASK-026 (FIX-001):** el *fallback* de `get_gaming_pack()` (con `gaming` borrado) copia `apps`/`keepers`/`target_categories` en profundidad |
| 27 | `test_default_meta_matches_canonical_otros` | **TASK-026 (FIX-005):** el centinela `⚪ Otros` (U+26AA) coincide con `CATEGORY_ORDER[-1]` y con el default de `ProcessInfo`, resuelve al último índice del orden, y los **tres** sitios de código usan el literal canónico |
| 28 | `test_pack_service_backup_and_recovery` | **TASK-026 (FIX-009):** rotación real del `.bak`, recuperación desde `.bak` con JSON corrupto, y un error de permisos no borra la configuración |
| 29 | `test_do_load_publica_sin_tk` | **TASK-026 (FIX-007) + TASK-030 (P8):** `_do_load` publica desde el hilo principal, con un arnés **sin Tk**; identidades de hilo, camino de crash y guarda `ast` |
| 30 | `test_save_atomic_nunca_toca_el_principal` | **TASK-030 (P1):** el volcado va a un temporal y, si se corta, el principal conserva sus bytes |
| 31 | `test_publicar_no_trunca_el_principal` | **TASK-030 (P1b):** publicar no usa un primitivo de copia (que trunca el destino) |
| 32 | `test_save_no_escribe_si_la_rotacion_no_puede_leer` | **TASK-030 (P2):** un `OSError` de lectura no se convierte en "sigo y sobrescribo" |
| 33 | `test_corrupcion_sin_backup_intenta_volar` | **TASK-030 (P3):** la regeneración llega a volcar (espía de `json.dump`, no de `save()`) |
| 34 | `test_forma_legacy_no_tumba_la_app` | **TASK-030 (P4):** `{"profiles": "texto"}` no tumba la app; solo la forma validada es corrupción |
| 35 | `test_todas_las_clases_de_corrupcion_se_recuperan` | **TASK-030 (P5):** tabla de las 4 clases de `CORRUPTION_ERRORS`, fila a fila |
| 36 | `test_oserror_de_lectura_no_es_corrupcion` | **TASK-030 (P6):** un `OSError` de lectura se propaga y no toca el `.bak` |
| 37 | `test_attribute_error_ajeno_no_es_corrupcion` | **TASK-030 (P7):** un `AttributeError` que no sea el deliberado se propaga |
| 38 | `test_la_rotacion_usa_la_misma_puerta_que_load` | **TASK-031 (L1):** la rotación usa `_read_json` y el `.bak` sano sobrevive a un `save()` real (mata L-M1) |
| 39 | `test_la_hoja_malformada_se_clasifica` | **TASK-031 (L2):** 6 hojas × 2 ramas se clasifican como corrupción, y el mensaje dice campo + pack + tipo real (mata L-M2) |
| 40 | `test_load_no_escribe` | **TASK-031 (L3):** `load()` no llama a `save()` en ninguna rama y no cambia ni un byte (mata L-M3) |
| 41 | `test_la_recuperacion_no_sobrescribe_el_bak` | **TASK-031 (L4):** recuperar no refresca el `.bak` byte a byte (mata L-M4) |
| 42 | `test_sin_bak_legible_no_se_sobrescribe_el_principal` | **TASK-031 (L5):** sin `.bak` el fichero se queda en disco y el pack queda marcado como dañado (mata L-M5) |
| 43 | `test_un_campo_desconocido_no_es_corrupcion_y_no_se_borra` | **TASK-031 (L6):** `notas` no es corrupción y sobrevive al `save()` (mata L-M6; separa la opción (a) de la (b)) |
| 44 | `test_packs_y_profiles_a_la_vez_es_corrupcion` | **TASK-031 (L7):** las dos claves a la vez se clasifican nombrándolas y ningún pack desaparece (mata L-M7) |
| 45 | `test_la_raiz_mal_escrita_no_destruye_los_packs` | **TASK-031 (L8):** una raíz sin clave válida no es corrupción ni borra los packs del usuario |
| 46 | `test_un_error_de_escritura_no_es_un_campo_desconocido` | **TASK-031 (L9):** un `OSError` al escribir no se clasifica como "campo desconocido" |
| 47 | `test_la_clave_del_mapa_es_la_identidad_del_pack` | **TASK-031 (L10):** la clave del mapa es la identidad del pack, no un campo libre |
| 48 | `test_la_raiz_legada_conserva_sus_claves_extra` | **TASK-031 (L11):** la raíz legacy conserva sus claves extra tras un `save()` real |
| 49 | `test_una_clave_raiz_nunca_es_un_error_de_escritura` | **TASK-031 (L12):** una clave raíz nunca es un error de escritura |
| 50 | `test_arranque_de_apps_no_usa_shell` | **TASK-027 (FIX-003):** arrancar una app no es ejecutar un comando: sin `Popen`, sin intérprete, contador honesto, log del motivo, guarda `ast` |
| 51 | `test_un_junction_no_puede_colar_lo_que_hay_detras` | **TASK-027 iter 2:** un junction/enlace **real** cuyo destino cae fuera de las raíces se rechaza, un `.exe` que apunta a un `.bat` se rechaza, y los dos controles positivos (enlace **dentro** de una raíz) arrancan |
| 52 | `test_la_contencion_no_acepta_un_hermano_de_prefijo` | **TASK-027 iter 2 (M10):** la contención es por componentes, no por prefijo de cadena (mata el `startswith`) |
| 53 | `test_la_contencion_no_depende_de_la_caja` | **TASK-027 iter 2:** `C:\PROGRAM FILES\...` está dentro de `C:\Program Files` en las dos direcciones, y fuera sigue siendo fuera |
| 54 | `test_la_guarda_de_shell_true_ve_atributos_y_aliases` | **TASK-027 iter 2:** la guarda anti-`shell=True` ve `ast.Attribute` y los alias de import, y no marca `shell=False` |
| 55 | `test_un_hard_link_no_es_una_hoja_y_el_script_no_pasa` | **TASK-027 iter 3:** un hard link real a un `.bat` de fuera y una **copia plena** del mismo `.bat` no arrancan (la regla es el **contenido**, `_es_imagen_pe`, no `st_nlink`); `MZ` sin `PE\0\0` y un `e_lfanew` absurdo tampoco; fail-closed; y un `.exe` **instalado** con `st_nlink > 1` **sí** arranca, que es lo que prohíbe la "solución" de rechazar todo enlace duro |
| 56 | `test_el_gestor_guarda_la_ruta_absoluta` | **TASK-027 (FIX-003, escritor):** lo que se guarda en `Pack.apps` es la ruta absoluta, con degradación a `full_name` |
| 57 | `test_orden_de_categorias_no_es_alfabetico` | **TASK-027 (FIX-004):** el orden es `CATEGORY_ORDER`, no el de `sorted()` sobre cadenas con emoji |
| 58 | `test_toggle_favorite_desmarca` | **TASK-027 (FIX-006):** la segunda pulsación de la estrella desmarca el favorito |
| 59 | `test_logging_va_a_fichero_y_no_a_stderr` | **TASK-028 (FIX-010):** el aviso acaba DENTRO de `woptimizer.log` y **no** en `stderr` (afirma sobre contenido y con el control negativo del `StreamHandler` sembrado: mata la implementación sin `force=True`) |
| 60 | `test_la_consulta_de_version_no_puede_desincronizarse` | **TASK-028 (FIX-018):** `pyproject.toml`, `__init__.py` y `tasks.json` declaran la **misma** versión, y no puede existir un cuarto sitio (escáner de `src/` con expectativa derivada del código) |
| 61 | `test_el_archivo_legacy_esta_versionado_y_no_vuelve_a_la_raiz` | **TASK-028 iter 2-5:** el archivo de `docs/archive` está versionado, completo y **sin volver ni a la raíz ni a la ruta viva que lee la app** (`_app_dir()`), por la **firma del esquema v2** (`profiles` + **dos** rasgos en el mismo registro). **Iter 5 (F1):** la ruta viva **ilegible da aviso, no muerte**, y eso se **afirma** con un control que escribe los tres ficheros de verdad (no-UTF8, truncado a mitad de un emoji de 4 B, `PermissionError` real) y exige el **motivo por su texto**; el literal `null` (que no lanza) también. Un control positivo sobre un documento vivo, porque un helper que declare todo ilegible pasaría los otros |
| 62 | `test_el_punto_de_entrada_declara_el_log_antes_de_los_servicios` | `__main__.main()` invoca `setup_logging()` **antes** de instanciar ningún servicio (AST, por **orden** de lineno; no ejecuta `main()`) |
| 63 | `test_process_list_file_sigue_siendo_un_contrato` | `PROCESS_LIST_FILE` existe, vale lo que debe y la nombran sus tres consumidores vivos |
| 64 | `test_la_documentacion_del_blindaje_no_puede_desfasarse` | las dos docs dicen el rango **medido con `ast`** y los 34 nombres **reales** del `frozenset` |
| 65 | `test_el_log_rota_con_el_limite_declarado` | el handler es un `RotatingFileHandler` **exacto** con `maxBytes`/`backupCount` declarados (`isinstance` no lo distinguiría: hereda de `FileHandler`) |
| 66 | `test_config_no_configura_nada_al_importarse` | `config.py` no **configura** el logging **al importarse**: ni en la cima, ni dentro de un `if`/`try`/`for`/`while` de módulo, ni en el **cuerpo de una clase** (que sí se ejecuta al importar); dentro de una **función** sí. **Iter 5:** además la **firma** de un `def` (decoradores, valores por defecto, anotaciones) se evalúa al importarlo, pero **su cuerpo no**, y un **generador perezoso** no se ejecuta al importarlo mientras que una **comprehension** sí. Detector probado en las dos direcciones, con el recuento **derivado de las tablas** (no escrito a mano) |
| 67 | `test_no_literal_colors_in_views` | **TASK-029 (UI-002):** cero colores literales en views/; todos los colores provienen de `theme.py` |
| 68 | `test_theme_tokens_complete` | **TASK-029 (UI-001):** 15 tokens de color, exactamente 6 tamaños tipográficos, 3 radios de curvatura |
| 69 | `test_contrast_wcag_aa` | **TASK-029 (UI-003):** cumplimiento de ratios WCAG 2.1 AA (>= 4.5:1 texto normal, >= 3.0:1 componentes) |
| 70 | `test_hit_targets_minimum` | **TASK-029 (UI-007):** todos los botones interactivos tienen un tamaño mínimo de 28x28px |
| 71 | `test_semantic_color_contract` | **TASK-029 (UI-012b):** Gaming verde `#1DB954`, peligro rojo `#c22d2d`, semáforos no contaminados |
| 72 | `test_woptimizer_ico_exists_and_valid` | **TASK-029 (UI-006):** existencia y validez del archivo de icono multi-resolución `assets/woptimizer.ico` |
| 73 | `test_scan_latency_and_lazy_exe_resolution` | **TASK-033:** optimización de latencia en `ProcessService` (`psutil.process_iter(['pid', 'name'])`, `exe_path=""` lazy, `model_construct`, precomputación `_CAT_ORDER_IDX`, `get_process_exe_path(pid)` on-demand con degradación segura y benchmark < 25 ms) |
| 74 | `test_models_strict_validation_and_contracts` | **TASK-034:** validación estricta de modelos Pydantic (`strict=True` en `is_favorite`/`is_gaming`, `default_action` restringido a `Literal["start", "kill"]`, `extra="allow"` en `Pack` y `AppData`, y defaults canónicos de `ProcessInfo`) |
| 75 | `test_main_window_navigation_transitions` | **TASK-034:** ciclo de vida y navegación headless en `MainWindow` (transiciones Dashboard -> Packs -> ProcessManager -> Dashboard, destrucción de vistas previas con `winfo_exists()`, activación de estilos nav y recarga asíncrona) |
| 76 | `test_los_workers_de_pack_solo_publican_por_after` | **TASK-035 ciclo 26 (S2, S3; iter 3 y 4) + TASK-078 (SV3):** el worker de `execute_pack`, `kill_pack`, `start_pack`, **`ProcessManagerView._do_load` y `ProcessManagerView.on_kill_selected`** —cinco métodos de tres clases de vista— solo **publica**. **TASK-078: esa tupla escrita a mano era el agujero y ya no existe**: el inventario recorre las clases enteras de las tres vistas, suma los objetivos de `threading.Thread(target=...)` y los callbacks que un servicio ejecuta en hilo secundario (`load_db_async`), y **exige que las publicaciones que ha visto sean las mismas que el código tiene** (10 de 10, contadas aparte sobre los ficheros). Mutado a una tupla corta, el mutante M8a —publicar a 3000 ms y a un callback inventado en `process_manager_view.py:196`, uno de los cuatro call sites que la tupla no miraba— muere por la comprobación de inventario, y no por suerte. La lista de lo permitido son **pares `(raiz, metodo)`**, no raíces: con raíces, `self.pack_service.get_all_packs()` y `self.process_service.get_process_exe_path(1)` colaban. Baja por `ast.Subscript` (iter 3) y desde la iteración 4 también por `getattr`/`setattr`/`delattr`, por `ast.Delete` y por los **argumentos** de las llamadas permitidas: sin eso, `getattr(self, 'status_label').configure(...)`, `setattr(self, '_last_gaming_summary', 'x')`, `del self._last_gaming_summary` y `kill_pack_apps(self.status_label)` pasaban las cuatro. Exige que **cada** `self.after` **y cada `self._publicar_en_el_bucle`** lleven 0 ms y un callback de la lista blanca. La guarda se prueba **contra sí misma** (8 infracciones sintéticas, 1 worker conforme, el caso de las dos ramas con `self.master.after` en una, y el control 9 que degrada la puerta nueva a par permitido). **TASK-079 (R5f): los callbacks que `load_db_async` ejecuta en hilo secundario pagan el invariante ENTERO del worker, no solo la regla de la puerta.** Antes se les aplicaba `_publicaciones_malas` con un docstring que lo justificaba diciendo que "dentro de esos cuerpos tocar widgets es lo correcto, ya están en el hilo principal", y esa medición era FALSA: `ProcessService.load_db_async` invoca `on_error` y `callback` DENTRO de su `_download` (`process_service.py:402/411`), que es el cuerpo de `threading.Thread(target=_download)` (`:416`), o sea que corren en el **secundario**; lo que corre en el principal es lo que ellos publican. El corte por el que el guard no marca dentro de esas clausuras es **por los nombres que se publican**, no por "todo lo anidado": una clausura que el cuerpo solo llama sigue corriendo en el secundario y se mide entera |
| 77 | `test_el_feedback_de_pack_dice_la_verdad` | **TASK-035 ciclo 26 (S1, S4, S5, S9; iter 3) + TASK-036 (iter 4, 5 y 6):** el feedback de cierre dice la verdad en los **cuatro** desenlaces, por las **tres** puertas (gaming, pack normal y la no-gaming de la portada, que hasta la iteración 3 no se ejecutaba nunca), con el worker real, doble pulsación, hilo secundario real y `self.after` encolado. Desde la iteración 4 también entra por el worker de la **rama `start`** de `execute_pack` (que tampoco se ejecutaba nunca). Afirma el **texto exacto** (no "dice algo con 6"), incluido `killed == 1` como éxito, `"✅" not in texto` en las ramas `nada` y `fallo`, y la **omisión de la cláusula de MB con `freed_mb <= 0`**. Y afirma el **aviso del pack que no puede hacer nada** (vacío y Gaming inerte) por sus dos familias, con el color exacto, sin worker, sin nada encolado y **sin doble pulsación armada**, más el gaming sano con apps o con categorías (que no debe avisar). La barra de reposo se afirma por su **texto** (procesos activos y resumen del Gaming Mode) y los temporizadores se miden con un **reloj simulado de plazo absoluto** (t0, t=1000, t=5500, t=6500) en las **tres** puertas del banner, afirmando además que en `_timers_ui` queda exactamente un handle. **Iteración 5, dos bloques nuevos:** (a) el **verbo atado al método** en `start_pack` se afirma con un pack de la familia *opuesta* (gaming, `default_action="kill"`, sin apps), porque el pack vacío que ya había traía `default_action="start"` de serie y no distinguía `"start"` de `pack.default_action`; (b) el **contrato de canal no vacío** del aviso inline, que compara el `fg_color` del `status_label` **contra el fondo de reposo** (no contra el anterior: si el canal pintara `CANCEL`, el color ya sería `CANCEL` de antes y la comparación sería verde por construcción) y por eso detecta y descarta su propia versión vacía. **Iteración 6:** `kill_pack` con un pack **no gaming, vacío y `default_action="start"`** afirma el verbo **"apagar"**: el verbo lo decide la puerta, no el dato del pack (mata D5). **Iteración 7, cuatro bloques** (todos con el mismo arnés de doble de servicio, doble pulsación, hilo secundario y `after` encolado): (a) el **segundo** punto de guarda de `_aviso_pack_inerte`, al que el auditor de cierre mutó y el mutante sobrevivió — entra por `kill_pack` con un doble que entrega el pack **con** apps en las dos primeras lecturas y **sin** apps en el re-fetch, cuenta las lecturas y exige aviso, cero `kill_pack_apps` y cero worker (mata K-a); (b) la **tarjeta de la Portada** atada al `default_action` real por la vía real (`refresh_dashboard` → botón real → `cget("text")`), en las dos ramas y las dos direcciones, con un Gaming Mode de `default_action="start"` como control (mata P-d-a/b); (c) el **contrato de los llamantes** con una guarda `ast` que corre **primero** —el segundo argumento de `mensaje_sin_apps`/`mensaje_banner_sin_apps` tiene que ser una ACCION literal o `pack.default_action`— más la frontera: una acción desconocida (`"apagar"`, `"stop"`, `"Kill"`, `""`) es un `KeyError` con el nombre de la puerta, no un `"apagar"` silencioso (mata D5-c/e/f); (d) la **cadena causal** `create_user_pack` → `default_action="start"` → verbo de la puerta de apagar, medida con el `PackService` real y no con un `Pack(...)` de literales (mata D5-d) |
| 78 | `test_el_gestor_de_procesos_tampoco_miente` | **TASK-035 ciclo 26 iter 3:** la **tercera** puerta de feedback, `ProcessManagerView.on_kill_selected`, que el fix de la iteración 2 y la guarda AST no tocaban y que pintaba `"<tick> 0 cerrados, 0 fallidos."` con `killed == 0`. Entra por `on_kill_selected` de verdad (doble pulsación, hilo secundario real, `after` encolado) y afirma texto y color exactos en los cuatro desenlaces; comprueba que se cierran los PIDs marcados, que el refresco de la lista se programa a 1000 ms y no al instante, y que `skipped` no se confunde con `failed`. **No mata ningún proceso**: el `ProcessService` es un doble |
| 79 | `test_headless_ui` | UI completa se instancia y destruye en 1.5 s sin errores de runtime |
| 80 | `test_el_validador_avisa_en_vez_de_tirar_la_excepcion` | **TASK-037 ciclo 27 (T-27.1 a T-27.4):** la rama `if n_tests is None:` de `validate_docs.py` era **código muerto**: `_recuento_de_tests` no tenía ni un `return None`, así que sus dos rutas (fichero ausente, fuente rota) salían con traceback en vez de con informe. El arreglo es el **productor** (`except OSError` sobre el `open()`, `except SyntaxError` —no `IndentationError`— sobre el `ast.parse()`), NO la rama, que ya estaba escrita para el contrato correcto; y T-27.2 extrae `_comprobar_recuento_de_tests(root, errors, ok)` para que la rama sea alcanzable desde un test. Cuatro fixtures en un `tempfile.mkdtemp()`: **sangría rota** (el caso que medido lanza `IndentationError`), **fichero ausente**, **sano** (la 4-tupla, no `None`) y **definido y no invocado** (que además exige que el mensaje **no** lleve el segmento `invocado y NO definido: .` con la lista vacía). Cada llamada va envuelta en un `try/except Exception` que convierte el crash en `AssertionError`, para que los mutantes M1/M2 mueran por la aserción y no por traceback |
| 81 | `test_el_alcance_del_guard_de_llamantes_se_deriva_del_arbol` | **TASK-037 ciclo 27 (T-27.5 a T-27.7):** el guard del contrato de los llamantes tenía el alcance en una **tupla literal de dos ficheros**, que era una apuesta sobre qué ficheros importan `feedback` y la apuesta tenía un fichero mal (hay tres). El guard pasa a ser `_modulos_que_importan_feedback(raiz)` + `_guardar_contrato_de_llamantes(raiz, acciones_validas)`, y el alcance se **deriva** recorriendo `src/woptimizer/**` con `ast`. El test se monta sobre un **árbol sintético** en `%TEMP%` porque con el repo real no se distingue "derivé el alcance" de "escribí el alcance correcto a mano" (mutante M5): cinco módulos, **cuatro** importadores de `feedback` —dos conformes y dos con verbo cableado, uno de ellos **fuera de `ui/views/`** y otro en forma **`fb.mensaje_sin_apps(...)`** (`ast.Attribute`, que el `getattr(func,"id",None)` de antes se saltaba en silencio— y su import `from woptimizer.ui import feedback as fb`, que tampoco entraba en el alcance— mutantes M6 y M8)— y un quinto que **no** importa `feedback`. Control negativo obligatorio: `pack.default_action` y las ACCIONES literales `"start"`/`"kill"` no se pueden marcar, porque un guard que marca todo no vigila nada (mutante M7) |
| 82 | `test_pack_service_cache_invalidation_and_immutability` | **TASK-040 (Ciclo #30):** Caché inmutable de 2 capas en `PackService.get_all_packs()` (< 0.05 ms), copia defensiva `model_copy(deep=True)` e invalidación atómica de caché al actualizar packs |
| 83 | `test_process_filter_performance` | **TASK-040 (Ciclo #30):** Benchmark de filtrado en lista de procesos (< 350 items) completado en < 2.0 ms usando pre-tokenizado |
| 84 | `test_pydantic_extra_fields_persistence` | **TASK-041 (Ciclo #31):** Persistencia e inmutabilidad de campos extra no estándar en modelos Pydantic `AppData` y `Pack` tras ciclos de `load()` -> `save()` -> `json.load()` |
| 85 | `test_freed_mb_calculation_precision` | **TASK-041 (Ciclo #31):** Precisión del cálculo de `freed_mb` (suma de RSS física de padre e hijos y redondeo exacto a 2 decimales en megabytes) |
| 86 | `test_notification_service_rlock_and_concurrency` | **TASK-042 (Ciclo #32):** Thread-safety y reentrancia en `NotificationService` con `threading.RLock()` bajo concurrencia multihilo |
| 87 | `test_process_service_kill_defensive_zombie_and_oserror` | **TASK-042 (Ciclo #32):** Captura defensiva de `psutil.ZombieProcess` y `OSError` en `kill_processes` y `kill_pack_apps` |
| 88 | `test_process_categorization_latency_and_memoization` | **TASK-045 (Ciclo #35):** Memoización de metadatos de categorización en `_meta_cache` O(1) e invalidación atómica de `_proc_cache` al recargar la DB |
| 89 | `test_tray_session_restoration_integration` | **TASK-043 (Ciclo #33):** Integración de '🔄 Reabrir aplicaciones cerradas' en el menú contextual de `pystray` y notificación nativa resultante |
| 90 | `test_confirmable_mixin_lifecycle_and_widget_contracts` | **TASK-046 (Ciclo #36):** Contratos de ciclo de vida, widgets y estados en `Confirmable` mixin (mutación de estados en botón y label, throttling de 300 ms en 2ª pulsación, changed_text, auto-expiración a 3000 ms, `_cancel_confirm`, `cancel_on_destroy` y tolerancia a `winfo_exists() == False`) |
| 91 | `test_gaming_service_rlock_and_concurrency` | **TASK-047 (Ciclo #37):** Resiliencia de concurrencia y recuperación en `GamingService` (`threading.RLock()` reentrante, concurrencia multihilo en `restore_gaming_session`, preservación defensiva ante excepciones y aislamiento no-OSError en `ProcessService.start_pack_apps`) |
| 92 | `test_pack_service_favorite_contracts_and_resilience` | **TASK-048 (Ciclo #38):** Contratos de favoritos (validación `ValueError` en `set_favorite(None)`, `toggle_favorite()` lee estado vivo y persiste, `_ensure_gaming_pack()` restaura `is_favorite=True` en gaming, y guard AST de ausencia de `get_favorite_pack`) |
| 93 | `test_dashboard_favorite_grid_adaptive_contracts` | **TASK-049 (Ciclo #39):** Rejilla adaptativa al ancho de ventana en `DashboardView` (`ANCHO_MIN_CARD` = 280, cálculo de columnas `cols = min(n, max_cols)`, re-grid dinámico en `<Configure>`, liberación de pesos a 0 en columnas sobrantes y placeholder span) |
| 94 | `test_process_service_db_download_contracts` | **TASK-050 (Ciclo #40):** Contratos de descarga remota de DB (`DB_REMOTE_URL` centralizada en GitHub, sin literales en el cuerpo de `load_db_async`, reporte observable a `on_error`, fallback a DB local offline y contrato anti-red) |
| 95 | `test_process_manager_db_update_button_and_feedback` | **TASK-051 (Ciclo #41):** Botón de actualización de DB en `ProcessManagerView` (`btn_update_db` cableado a `_force_update_db()`, reporte observable y honesto de fallos en `status_label`, distinción de estados y desacoplamiento de GitLab) |
| 96 | `test_process_manager_pack_dropdown_single_arrow_and_placeholder` | **TASK-052 (Ciclo #42):** Indicador único en desplegable de packs (`PLACEHOLDER_PACK` centralizado sin glifo ▼ redundante, guard AST de literal único y verificación headless) |
| 97 | `test_docs_api_and_index_v3_contracts` | **TASK-054 (Ciclo #44):** Contratos de veracidad y actualidad en `docs/api.md` y `docs/index.md` (v3) (ausencia de residuos v2 eliminados, verificación en runtime de existencia de métodos citados de `ProcessService`, `PackService`, `GamingService`, `NotificationService` y modelos, prohibición de auto-elevación UAC en `index.md`, e integridad de archivos nav de `mkdocs.yml`) |
| 98 | `test_no_legacy_test_files_in_root` | **TASK-055 (Ciclo #45):** Guard anti-regresión y contratos de archivo de scripts `test_*.py` legacy (cero archivos `test_*.py` en la raíz del repositorio, preservación de los 11 ficheros trasladados en `docs/archive/legacy-root-tests/`, validez de `README.md` explicativo y aislamiento de `test_powershell_direct.py`) |
| 99 | `test_dead_code_ast_guard` | **TASK-056 (Ciclo #46):** Guard AST de código muerto en `src/woptimizer/**` (recorrido exhaustivo del árbol de módulos, verificación de referencias en producción y tests para las 201 definiciones, lista blanca justificada y eliminación de residuos legacy `_get_priority` y `process_db`) |
| 100 | `test_el_ancla_de_commits_no_depende_del_que_escribe_el_journal` | **TASK-057 (Ciclo #47):** El requisito de registrar cada ciclo se exige por la **UNIÓN** de `rd_journal.json` y el historial de commits, para que el registro validado no sea su propio testigo (4 sondas con `GIT_DIR` en `tempfile`, nunca el historial real: parser que lee ciclo y no `TASK-` con cifras divergentes, residuo de un ciclo comiteado y ausente del journal que da 2 errores **acusando su conjunto** (el 047, nunca el 046) más el árbol espejo con journal {46,47} e historial {46} que exige 0 errores, unión que no sustituye al journal, y ancla ilegible que produce informe en vez de excepción o verde por omisión) |
| 101 | `test_el_ancla_se_cablea_en_el_camino_real_del_validador` | **TASK-057 iter 3 (Ciclo #47, S2 + S2b):** El ancla tiene que estar cableada en la ruta que el producto ejecuta, no solo existir (**S2 del auditor**: la suite llamaba a las funciones privadas y `main()` no las invocaba nunca, así que borrar el cableado dejaba la suite entera verde). Copia el `validate_docs.py` real a un árbol temporal con el esqueleto que `validar(root)` lee y lo ejecuta como subproceso: acusa el ciclo 999 comiteado y ausente del journal, exige `## CYCLE-999` y salida `1`, y exige `Resumen:` en el informe. Sus **dos mitades mutantes**, cada una escrita desde la fuente intacta, exigen que el residuo desaparezca: (S2) el cableado del ancla sustituido por `pass`, y (S2b) `main()` sin llamar a `validar(root)`, que declara `0 OK / 0 FAIL` y sale con `0` |
| 102 | `test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador` | **TASK-057 iter 2 (Ciclo #47, S5):** El `except (ValueError, OSError)` de la lectura de `.taskmaster/rd_journal.json` no se puede estrechar a `json.JSONDecodeError`: con un `PermissionError` real (inyectado en el `open` del módulo) el validador debe dar **informe con el motivo y un único error**, no traceback, y no puede confundirse con el estado "journal vacío". Desde la iteración 3 se asienta por `validar(root)` sobre el esqueleto real copiado |
| 103 | `test_el_ancla_sobre_un_arbol_sintetico_tabla_de_escenarios` | **TASK-057 iter 3 (Ciclo #47, D1/D3/D4) + cierre del ciclo #47:** los escenarios del ancla son **filas de una tabla**, no tests, y todos se asientan por `validar(root)` —la misma función que `main()` llama— sobre el esqueleto real copiado **una vez** (1,7 MB). Cada fila mata un mutante distinto: (a) historial sin marcadores con journal que sí registra → parser roto `[FAIL]`; (b) el **mismo** historial con journal vacío → silencio (desactivar la rama y quitarle `and journal_cycles` son mutantes distintos y cada fila mata el suyo); (c) un ciclo cerrado en una **rama lateral** se acusa, por su conjunto y sin invertirlo (mata `--all` y la diferencia al revés); (d) journal que se lee pero no aporta ningún ciclo entero → `[FAIL]`; (e) sin `GIT_DIR` en el entorno el anclaje cae a `%LOCALAPPDATA%` y lee su ciclo (mata el fallback, que deja `None` en el entorno de `subprocess`); **(f) el encabezado `## CYCLE-015` borrado y el número vivo solo en la prosa** (`TASK-015` y `CYCLE-015`, las dos citas) → mata P2, P3 y H2, los tres del falso verde del ciclo #15 reabierto por otra puerta; **(g) `git` falla una vez con `TimeoutExpired` y el ancla se lee en el reintento** → mata E2 (`except OSError` deja el timeout con traceback, sin comprobar ni el check 6 ni el 7) y E3 (quitar el reintento); **(h) el historial tiene `feat(ciclos 14-20)` y `ciclos 1-9999`, el journal solo registra el 1 y el 14 y el changelog solo tiene esas dos entradas** → los dos errores que salen tienen que nombrar **exactamente** 015 a 020, ni uno más ni uno menos, lo que mata G1 (el plural deja de leerse y el historial no aporta nada) y el `MAX_CICLOS_DE_UN_RANGO` (sin tope los errores nombrarían 9998 ciclos más). La fila (g) sustituye `subprocess.run` de la stdlib y lo restaura en un `finally` propio, más interno que el del árbol |
| 104 | `test_la_deuda_exige_un_ancla_resoluble_en_toda_fila_viva` | **TASK-060 (Ciclo #49, check 8 de `validate_docs.py`):** la sección `## Deuda Técnica Conocida` de `STATUS.md` gobierna qué trabajo hace el bucle cuando el backlog está vacío, y hasta el ciclo #48 no la miraba nadie: `validate_docs.py` tenía **0** coincidencias de la palabra `Deuda`. **Veinticinco escenarios de una tabla**, todos por `validar(root)` —la misma función que `main()` llama— sobre un árbol sintético con el esqueleto real copiado una vez, y con el total **derivado con `ast` del árbol del test** (6 + 1 = 7), nunca del repo real. La tabla cuenta sus filas con un `assert` (C8), y **crecer escenarios no crece el número de tests** Cada fila mata un mutante distinto: (a) ancla viva que no resuelve → `VIVA sin ancla resoluble` + `ancla NO RESOLUBLE`; (b) la **misma** fila `CERRADA` → nada (mata borrar la exención); (c) `42 tests` contra el derivado → `NO es el derivado con ast`; (d) panel solo de cerradas → cero errores de la sección; (e) sección ausente → `no existe la sección`; **(f1) `CERRAD` dentro de código inline → la fila sigue viva** (mata borrar el `re.sub`, que la dejaría exenta y en verde); (f2) la fila que escribe el criterio marcada `CERRADA` → `se ha autoeximido`; (g) única fuente una `TASK` `completed` → `su UNICA fuente es una TAREA YA CERRADA`; (h) `AMARILLO` con el código de salida sobrecargado vivo → `su comprobable SIGUE VIVO`; (i) cita que ya no apunta a lo que dice → `NO contiene el identificador`; (j) reparto que el `ast` desmiente → `separa 6/1`; (k) marcador headless ausente → `NO SE ENCUENTRA el marcador`; (l) la palabra de cierre en prosa → no exime; (m) el veredicto en negrita que **niega** el cierre → no exime; (n) la fila cuya única verdad es el propio `STATUS.md` → `ancla NO RESOLUBLE: … es el propio panel`; (o) la cifra **declarada** que es la verdadera → cero errores; (p) el tramo de código inline vacío → el validador devuelve informe; (q) mencionar el contrato no es **declararlo**; (r) veredicto con un id que **no resuelve** → sigue viva; (s) el marcador en **minúsculas** → no cierra nada; (t) la frase que se exime y se rebaja a la vez → el suelo tiene que disparar; (u) el marcador tiene que estar en **negrita**; (v) la negación en la **prosa**; (w) el panel citado con **otra grafía** (`status.md`) → tampoco es fuente. Los **veinte límites residuales** del check están escritos en `docs/ai/sandbox-rules.md`, no omitidos |
| 105 | `test_pack_no_gaming_apaga_por_categoria_y_respeta_keepers` | **TASK-063:** un pack **no gaming** con `apps=[]` y una categoria marcada mata el proceso de esa categoria y respeta el keeper. Antes esa ruta acababa en `kill_pack_apps([])` y mataba 0: **ninguna** linea de ella leia `target_categories` |
| 106 | `test_pack_con_categorias_supera_las_cuatro_guardas` | **TASK-063:** el pack anterior llega a la puerta en las **dos** vistas. Antes las dos guardas de apagado cortaban con "no tiene apps" antes de armar la confirmacion |
| 107 | `test_acordeon_se_renderiza_en_pack_no_gaming_con_espejo_deshabilitado` | **TASK-063:** el control existe para cualquier pack (no hay `if pack.is_gaming`), el catalogo sale del servicio, y el espejo deselecciona la gemela al marcar la otra. Es una guarda `ast` sobre el **cableado**, y por eso no se solapa con el 3-E (fila 124), que afirma el mismo invariante por **efecto** con la vista real montada. La premisa con la que se escribio este test --«el arnes no abre ventana y una casilla sin `CTk` no se puede instanciar»-- era **FALSA** y es la que hizo Lackaar el invariante nueve rondas: `test_headless_ui` y `test_main_window_navigation_transitions` montan root y vista reales. **Iteracion 2 (mutation-auditor):** el predicado miraba `text=` con valor `ast.Constant` y las casillas pasan `text=cat` (un `ast.Name`) y el boton `text=_texto_acordeon(...)` (un `ast.Call` con f-string dentro): un gate de 118 lineas envolviendo el acordeon pasaba. Ahora mira la CONSTRUCCION (`CTkCheckBox`, `_texto_acordeon`, `create_command`), que no depende del texto, y exige ademas que exista al menos un gate que vigilar. **Iteracion 3 (mutation-auditor, mutante U1_AND):** el gate se buscaba por **igualdad textual** (`el test del if es exactamente pack.is_gaming`), asi que `if pack.is_gaming and pack.default_action == "kill":` --un `ast.BoolOp`-- desaparecia del analisis y dejaba los 123 tests en verde con el acordeon gateado; y es PEOR que el gate simple, porque `default_action` nace en `"start"` y ese gate le esconderia el acordeon al propio pack de Gaming. Ahora la pregunta es **estructural**: el gate es cualquier `if` o ternario cuya CONDICION **contenga** la lectura de `is_gaming` (con `ast.walk`), valga sola, con `and`, con `or`, negada con `not` o pasada como argumento. Un test que solo reconoce una forma de gate es un test que la siguiente forma ciega. **Iteracion 4 (mutation-auditor, 6 SUPERVIVIENTES):** las dos anteriores seguian preguntando por la **forma** de la condicion, y eso ciega seis formas mas, todas medidas con los 123 en verde: `gaming = pack.is_gaming` + `if gaming:`, `p = pack` + `if p.is_gaming:`, `getattr(pack, "is_gaming", False)`, `self._es_gaming(pack)`, `pack.id != "gaming"` y el **guard clause** `if not pack.is_gaming: return` al principio de un metodo propio. Ademas eran **demasiado estrictas**: rechazaban codigo legitimo (una casilla propia del Gaming Mode dentro del badge `PRESET`, y un texto de aviso que dice "arrancar"), y el mensaje de fallo afirmaba algo que no habia pasado. Un test que obliga a aflojar garantiza que se afloje, asi que ahora afirma una **PROPIEDAD**: **(A0)** el espejo existe (si no, A1 y A2 mirarian el vacio); **(A1)** ninguna pieza del acordeon --la casilla con `command=create_command(...)`, el `def create_command` y su etiqueta-- cuelga de un `if`/`IfExp`/`while`/`try`, **sea cual sea la condicion**, y la lista que alimenta la rejilla no depende de `is_gaming` --eso se resuelve **por transitividad**, arreglo de la ronda 5--; **(A2)** ninguna funcion que dibuje una pieza vuelve antes si se cumple algo que **dependa de si el pack es el de Gaming**, que es la unica forma de gate que no es antecesor. Las dos se afirman por su AFIRMACION y no por su forma. **Iteracion 5 (mutation-auditor, seccion 11, tres cosas concretas):** **(a) A1b resolvia UN solo salto** y por eso veia pasar `cats_visibles = all_cats if pack.is_gaming else []` (un nombre mas entre la asignacion y el bucle), `if not pack.is_gaming: all_cats = set()` y el gate entero puesto en `refresh_packs` (`self._muestra_categorias = p.is_gaming`): tres formas medidas, con un pack normal quedandose con **0 de 3 categorias** y los 123 en verde. Ahora la cadena se sigue salto a salto y SIN limite de saltos, con conjunto de visitados; que nombres dependen de `is_gaming` se calcula a **punto fijo sobre todo el modulo**, no en una pasada, y ademas se ve la **escritura gateada** --un nombre escrito dentro de un `if` que depende de `is_gaming`--. Y la sonda que cerraba el agujero era `ordenar_categorias([c for c in all_cats if pack.is_gaming] if pack.is_gaming else [])`, que repite `is_gaming` dos veces y no lo escribe nadie: era **menos natural que el agujero**. **(b) A2 era demasiado fuerte y su mensaje mentia**: prohibia CUALQUIER `return` condicionado y rechazaba `if not pack: return`, `if not sorted_cats: return` e `if categorias: return` --el ultimo, el patron que la propia clase ya usa--, mientras su mensaje de fallo afirmaba estar midiendo una sola condicion. Ahora mira la condicion, y la mira por su **lectura directa** de `is_gaming`, no por el valor del que viene: eso se eligio MEDIDO, porque propagar el valor hacia A2 rechazaba `if not card.winfo_exists(): return` (guard de Tk legitimo: `card` nace de `border_width=2 if pack.is_gaming else 1`) y el precio de NO propagar es un techo declarado, el (e) de abajo. **(c) el techo declarado era mas estrecho de lo que es**: ahora nombra las seis formas que se MIDIERON vivas, incluidas las dos que el texto no citaba (el `.destroy()` posterior y la lista filtrada a dos saltos), la nueva (e) y el eje (f) de la ronda 7. Techo declarado, medido, y NO una regla mas: cazarlas seria inventarse un predicado que un dia rechazaria codigo legitimo, que es la trampa que este test lleva ocho rondas evitando. Que los gates legitimos (badge `PRESET`, boton de restaurar, texto, `es_pack_inerte(pack.is_gaming, ...)` y los dos ternarios del borde) sigan existiendo **no se asserta**: este test no dice nada de ellos. Lo que NO cubre, dicho para que la proxima ronda lo mida en vez de suponerlo: un gate en el **lugar de la llamada** --`if pack.is_gaming: self._render_pack_card(pack)`--, porque `refresh_packs` YA condiciona de legitimo ("el Gaming primero", "el resto sin repetirlo") y ninguna regla puede distinguir una cosa de la otra sin volver a ser un test de forma; y gatear la llamada a `.pack()`/`.grid()` que hace **visible** la rejilla (o el `.pack_forget()` del boton que la abre) dejando las casillas construidas --(b)--; un `.destroy()` **posterior** sobre la casilla ya construida, que A1 no puede ver porque la construccion ya esta hecha --(c)--; una lista filtrada que llega de **otra funcion por una llamada** (`cats = self._categorias_visibles(pack)`): la cadena sigue las ASIGNACIONES del fichero que dibuja, no lo que devuelve una llamada --(d)--; y un guard clause cuya condicion depende de `is_gaming` **por una lectura indirecta**, que es el precio medido de mirar la lectura directa en A2. El eje tiene **TRES** exponentes y los tres se MIDIERON vivos, no uno: un atributo que pone otra funcion (`self._flag = p.is_gaming`, `LIMITE_E`), un **alias local** (`_g = pack.is_gaming`, `ALIAS_GUARD`) y un **predicado en un metodo** (`self._es_gaming(pack)`, `GUARD_METODO`). Los tres caen por el motivo del eje y no por la palabra. Correccion de la ronda 9 sobre lo que decia la 14.5: `ALIAS_GUARD` **vive** con su forma natural y no se reproduce la muerte que alli se le atribuyo; lo que si se reproduce y sigue muriendo en `14599` (A2) es `GG2`, el guard clause de metodo propio con `if not pack.is_gaming: return` --(e)--. Ninguno de los seis es una de las trece formas medidas: las doce que envuelven la construccion las cubren A1 y A2, y la treceava murio de otro test **Ronda 7 (mutante `LC`):** la casilla construida dentro de una comprehension con el filtro `if pack.is_gaming` en la propia comprehension se dibujaba vacia para un pack normal con los 123 en verde: A1b buscaba el `For` ancestro, una `ListComp` no lo es, y el `continue` la descartaba SIN MIRARLA. Ahora una comprehension cuenta como bucle --sus `generators` son nodos `ast.comprehension`, cada uno con su `iter` y sus `ifs`-- y se miran TODOS los bucles que envuelven la casilla, no solo el mas interior (medido: resolver solo el interior dejaba viva la forma `LC_ANIDADA`, que el test de `5f96671` mataba). El techo gana un eje **(f)**, tambien medido: un bucle por encima de la construccion cuyo iterable sea una eleccion de `is_gaming` se rechaza, aunque solo cambie el numero de columnas; la misma decision escrita con `if` ya la rechazaba A1 antes de este cambio. **Ronda 9 (mutante `ASSERT_GATE`):** un `assert` delante de la seccion se cuela, y lo que lo explica es lo que lo cierra: una sentencia NO puede ser el antecesor de otra, asi que el `assert` es un HERMANO y la cadena de padres que mira A1 (`Call <- Assign <- For <- _render_pack_card`) no contiene ni un `Assert` --cero, medido con `ast`--. Poner `ast.Assert` en la lista de condiciones **no lo cazaba**: con ese token y nada mas el mutante seguia verde, tambien con el `assert` dentro del bucle. Se anadio **(A3)**: ninguna sentencia ejecutada ANTES de la construccion puede impedir llegar a ella, y solo se miran las que TRANSFIEREN el control (`assert`, `raise`, `return`, `continue`, `break`) y dependen de `is_gaming`; un `if` anterior no estorba, uno que construya lo mide A1 y uno que devuelva, A2. Salvedad que queda escrita: `_CONDICIONALES` y `_TRANSFIEREN` son **listas blancas de tipos de nodo**, cierran las formas que se miden y no la clase de problema. |
| 108 | `test_start_categories_arranca_y_cuenta_honestamente` | **TASK-063:** arranca lo resoluble y manda lo no resoluble a `failed`, **nunca** a `started`. El techo es real: la DB guarda categoria, prioridad y descripcion, y **ninguna ruta**. **Iteracion 2:** este test sobreescribe `_patrones_de_categoria` con nombres que ya traian `.exe`, asi que no via la linea que decide si la extension se anade; ese hueco lo tapa ahora la fila 123, con la DB de verdad |
| 109 | `test_la_barrera_roja_sigue_dentro_de_la_puerta_comun` | **TASK-063, EL LADRILLO DEL CICLO #14:** pack **no gaming**, `target_categories=[ROJO, verde]`, snapshot **con `svchost` real**: `svchost.exe` ausente de lo que llega a `kill_processes` y `skipped == 1`. **`killed` NO afirma nada aqui**: el doble `_ProcessServiceSpy.kill_processes` devuelve SIEMPRE `(2, 0, 0, 12.5)`, asi que los discriminantes son la lista CAPTURADA y `skipped` (que si calcula la puerta). Corregido el 2026-10-03: aqui deciamos `killed == 1` y `architecture.md` 11.1 decia `killed == 0`, dos cifras contradicorias que el doble no puede dar. Usa `svchost` y no un nombre inventado **a proposito**, porque `is_system_protected('svchost')` es `False`: el blindaje de nombres no lo salva y solo la categoria roja puede cazarlo. Ojo con lo que este test **no** cubre: si la barrera roja de `_pack_evaluable` (G1) desaparece **sola**, la suite sigue VERDE, porque el snapshot trae `svchost` con la categoria roja y la descarta tambien G5. Medido el 2026-10-03: la mutacion que lo caza es caer **las dos** a la vez, o la que cubre la fila 121, que pone el snapshot y la DB en desacuerdo (que es lo que puede dejar `load_db_async` desde su hilo). Corregido el 2026-10-03: aqui se afirmaba que este test caia solo. |
| 110 | `test_categoria_roja_en_start_categories_no_arranca` | **TASK-063:** una categoria roja marcada para arrancar da `started == 0`. El ejecutable de prueba esta en un temporal **valido** a proposito: sin la barrera arrancaria 1, y `svchost.exe` del sistema no serviria porque `System32` no es raiz de arranque |
| 111 | `test_conflicto_misma_categoria_gana_kill` | **TASK-063:** la misma categoria en las dos listas no arranca (`started == 0`) y **la misma categoria sin conflicto si arranca** (`started == 1`), que es la mitad que evita que el filtro se coma todas las categorias verdes |
| 112 | `test_keepers_ganan_a_las_categorias_en_pack_no_gaming` | **TASK-063:** un keeper cuya categoria esta marcada no muere. Mirar solo el numero de llamadas a `kill_processes` no lo notaria, porque la llamada sigue habiendo una |
| 113 | `test_kill_recursivo_desde_la_puerta_por_categoria` | **TASK-063:** el nieto de un proceso de la categoria marcada tambien muere, contra procesos reales. Una puerta que montara la lista y matara por su cuenta saltaria el kill recursivo de `kill_processes` |
| 114 | `test_execute_pack_acepta_pack_no_gaming` | **TASK-063:** `execute_pack` **no** lanza `ValueError` con un pack no gaming (sin puerta comun la feature no tendria por donde pasar) y `execute_gaming_pack` **si** lo sigue lanzando: son dos puertas con dos alcances, no una sin contrato |
| 115 | `test_apagar_un_pack_no_gaming_no_toca_last_closed_apps` | **TASK-063:** tras apagar un pack **no gaming**, `get_last_closed_apps()` sigue con la restauracion Gaming pendiente. Mira **la lista**, no el banner: sin la condicion aparece un banner fantasma y, si se pulsa, `restore_gaming_session()` vacia la lista antes de arrancar y **destruye** la restauracion pendiente |
| 116 | `test_portada_no_anuncia_gaming_inerte_a_un_pack_de_arranque` | **TASK-063:** un gaming con `default_action="start"` y `start_categories` marcadas no ve "Gaming inerte" (diagnostico de la puerta de apagar) y su worker ejecuta `start_categories` |
| 117 | `test_default_action_stop_sigue_siendo_error_de_escritura` | **TASK-063:** `Pack(default_action="stop")` levanta `ValidationError`. El encargo daba `"stop"` por bueno; este test congela que **no** lo es, para que nadie lo "arregle" abriendo el `Literal` |
| 118 | `test_la_vista_no_lee_process_db_ni_repite_el_catalogo` | **TASK-063:** ninguna vista menciona `process_db` ni repite los 8 nombres de categoria a mano, y el catalogo del servicio se ejecuta **de verdad** y trae las 9 categorias sin el centinela, en el orden de `CATEGORY_ORDER` |
| 119 | `test_el_texto_de_confirmacion_no_dice_apagar_0_apps` | **TASK-063:** con 0 apps y 3 categorias, la doble pulsacion no arma "apagar 0 apps": el numero lo pone `cuenta_a_apagar` (el filtro de la puerta), no `len(pack.apps)` |
| 120 | `test_el_estado_que_elige_el_usuario_se_persiste_de_verdad` | **TASK-062 (bug reportado por el usuario):** elegir si un pack **arranca** o **mata** sus apps no se guardaba, y ningun test lo miraba. La causa: `get_all_packs()` devuelve **copias defensivas** (`model_copy(deep=True)` sobre una cache de dos capas) y `save()` serializa `self._data`, que esa copia nunca toca; ademas `save()` no invalida la cache, asi que la UI seguia enseñando el valor viejo. El desplegable cambiaba en pantalla, se escribia el fichero con el valor viejo y al recargar volvia al anterior: *parecia* que funcionaba. **Habia CUATRO call sites con el patron**, y dos no tenian nada de cobertura: `change_default` y `remove_app_from_pack`; el cuarto —las **categorias automaticas** del pack Gaming, que decide que cierra el Gaming Mode— estaba en el mismo metodo que el primero. El test tiene dos mitades porque la mitad ejecutable no existe: `change_default` es un closure dentro de `_render_pack_card` y solo se alcanza por el `command` de un `CTkOptionMenu`, o sea con una ventana de Tk, y esta suite no abre ventanas. **A** prueba la **causa** con el `PackService` REAL sobre disco temporal (mutar una copia + `save()` tiene que perder el cambio; `update_pack()` tiene que persistir Y invalidar la cache), y **B** es una guarda `ast` que ata los cuatro call sites al metodo que persiste, citando tambien la llamada prohibida. Los dobles de test que modelaban `PackService` (`_PackServiceGrabador`, `_PackServiceMock`) devolvian los mismos objetos y no tenian `update_pack`: sus aserciones leian el `pack` que la vista recibia, que la vista nunca tocaba, asi que pasaban **con el bug puesto**. MATA: `update_pack` -> `save` en cualquiera de los cuatro; borrar el `update_pack` entero; `get_all_packs()` sin `deep=True`; `update_pack()` que deje de invalidar la cache |
| 121 | `test_barrera_roja_sola_con_el_snapshot_y_la_db_en_discrepancia` | **TASK-063 iteracion 2 (mata a S1):** el test 109 lleva `svchost` ROJO en el snapshot, de modo que G5 lo descarta por su cuenta y **quitar G1 no se nota**. Aqui el snapshot lo trae VERDE y la DB lo dice ROJO: el unico camino que puede pararlo es la barrera de categoria roja sobre `target_categories`. La discrepancia no es sintetica: `should_kill_for_gaming` recalcula con `_categorize` (que vuelve a la DB) mientras G5 lee la del snapshot, y `load_db_async` corre en un hilo que cambia `_db_map` al aterrizar. Afirma la LISTA que llega a `kill_processes` y no `skipped`, porque con la discrepancia no hay descartes de G4/G5. **Iteracion 3:** ademas de sus tres precondiciones, **congela la PREMISA** con `assert spy._categorize("svchost.exe") != spy.snapshot[0].category`. Sin esa linea el test podia volverse decorativo sin que nada se notara: si alguien "limpia" el fixture y deja snapshot y DB de acuerdo, el proceso lo descarta G5 aunque G1 no exista, y el test seguia VERDE con la barrera de categoria borrada (medido, mutante `T16_SIN_DISC`) |
| 122 | `test_el_filtro_de_la_puerta_no_escribe_en_el_pack_original` | **TASK-063 iteracion 2 (mata a S7):** `_pack_evaluable` filtra una COPIA y su docstring lo promete. El dano no se ve en la ejecucion (el filtro es idempotente, asi que la segunda llamada mata lo mismo) sino en el ESTADO: el `Pack` que la vista tiene cargado y que `update_pack` persiste se queda sin la categoria roja marcada y sin la de conflicto. El pack de la prueba lleva las tres cosas que el filtro cambia |
| 123 | `test_arranque_por_categoria_toma_los_nombres_de_la_db_real` | **TASK-063 iteracion 2 (mata a A5):** `_patrones_de_categoria` tiene que anadir `.exe` a los patrones que la DB guarda SIN extension, porque `_resolver_app` exige `.exe`/`.com` y rechazaria el nombre pelado sin llegar a mirar el fichero; sin eso, arrancar por categoria no arranca NADA. Los tests 108, 110 y 111 no lo veian porque cada uno sobreescribe `_patrones_de_categoria` **por instancia** con nombres que ya traian `.exe`: el arnes tapaba la linea. Corregido el 2026-10-03 (iteracion 3): aqui se atribuia a la clase `_ServicioDeArranque`, que NO la sobreescribe --su docstring dice que sobreescribe OTRAS dos (`_resolver_app` y `_lanzar`)--; los que la sobreescriben son los tres TESTS, **por instancia** con `svc._patrones_de_categoria = ...` (`test_start_categories_arranca_y_cuenta_honestamente` en `run_tests.py:14742`, `test_categoria_roja_en_start_categories_no_arranca` en `:14848` y `test_conflicto_misma_categoria_gana_kill` en `:14875`, derivado con `ast` sobre el fichero definitivo: son las tres lineas de la ASIGNACION `svc._patrones_de_categoria = ...` --sus tres `def` estan en L14726, L14835 y L14862, y en el fichero **no hay una cuarta** asignacion--; los numeros se caducan con cada refactor del fichero, los NOMBRES no, y por eso se citan los dos. Corregido en la ronda 7: las cifras de la ronda 4 (`14631 / 14740 / 14667`) eran falsas en las tres y apuntaban a un `def`, a un `def` y a un `f-string`; la ronda 6 lo detecto y aqui ya estan las de la ronda 7, medidas de nuevo sobre el fichero ya con el arreglo de las comprehensions. **Re-derivadas en la ronda 8** (+38 lineas por el texto del techo (a) y (f) del test #3), porque un numero de linea caducado es la misma clase de falsedad que una cuenta mal contada: se vuelven a medir con `ast` sobre el fichero DEFINITIVO y no a ojo. Medido el fallo en carne propia: la primera redaccion de esta cifra, ya "corregida", se quedo **una linea** corta porque la ultima frase del techo (f) anadio una linea mas despues de derivarla). Este pide los nombres a la DB cargada por `_load_local_db` de verdad y afirma el CRITERIO (que arranque), no que se llamara |
| 124 | `test_todo_pack_ofrece_el_catalogo_completo_en_apagar_y_arrancar` | **TASK-063 T-9, la otra mitad del invariante del acordeon, y esta lo afirma por EFECTO:** monta la vista **real** headless (`PackManagerView` de verdad sobre un `ctk.CTk()` retirado, sin `mainloop` ni `after`) y comprueba, por cada tarjeta y por cada categoria del catalogo real, **exactamente una** casilla con el nombre de la categoria y **exactamente una** con `«categoria (arrancar)»`. El estatico de la fila 120 pregunta *alcanzabilidad* sobre el codigo --«¿puede esta sentencia impedir la construccion?»-- y no se responde sin enumerar tipos de nodo: ocho rondas de mutacion lo midieron, cada una cerrando una familia y dejando viva la siguiente. Aqui no se mira la forma, se mira **que etiquetas hay**. **E0** (el catalogo tiene al menos una categoria) va primero, o E2 seria vacuo y el usuario no veria casillas con el test en verde; **E1** (una tarjeta por pack) mata el gate en el lugar de la llamada; **E3** relanza como `AssertionError` la construccion que revienta, para que un `assert` de puerta no se confunda con un fallo del propio test. **El total NO se escribe**: sale solo (`2 * len(catalogo)`) y medirlo en este host daria un numero magico que depende de la DB; por eso se cuenta *exactamente una de cada* por categoria. **Ronda 11 (mutation-auditor, seccion 16): E4 y E5, las dos aserciones que faltaban y que NO son una familia mas.** Con E2 en verde, dos mutantes que no son formas de gate pasaban los 124/124: `W_VAR_CRUZADA` (la casilla de ARRANCAR colgada de la variable de APAGAR: el usuario marca «arrancar navegadores» y la app **guarda «apagar navegadores»**) y `K_CATALOGO_CORTO` (una categoría verde real se cae del catálogo: 18 -> 16 casillas mientras `_categorize("chrome.exe")` sigue diciendo «Navegadores», o sea un proceso del usuario **sin casilla donde marcarlo**). Los dos se cierran mirando el estado, no enumerando formas, y por eso no entran en la capa estática. **E4** compara lo que hay contra lo que **debe** haber, derivado de las dos fuentes que `categorias_disponibles()` declara usar y que son independientes de la lista que devuelve: la DB cargada (`ps._db_map`) y `CATEGORY_ORDER`, menos el centinela importado de `_DEFAULT_META`. No escribe ni un nombre de categoría, así que añadir una categoría al producto no obliga a tocar el test (medido: la sonda `K_CATALOGO_EXTENDIDO`, que mete una categoría de verdad que solo la DB conoce, pasa con 10 y 20 casillas). Sin E4, E2 es **tautológico** sobre el contenido del catálogo: compara las casillas contra la misma fuente que las produce. **E5** afirma el **cableado** por comportamiento, que E2 no miraba porque contaba etiquetas: `E5a` dice que el estado marcado de las dos casillas es el espejo de las dos listas (`CTkCheckBox.get()` lee el estado real del widget, y ese estado nace de la variable a la que la casilla está atada), y `E5b` **pulsa** con `CTkCheckBox.toggle()` —lo que CustomTkinter dispara desde `<Button-1>`— y comprueba **qué lista crece**: arrancar guarda en `start_categories` y no en `target_categories`, apagar al revés, las dos listas no se pisan al tocar una categoría distinta, y el espejo se impone. La tarjeta se localiza **por estado y no por posición**, porque `refresh_packs` pone «gaming» delante y después los demás en orden de registro. **E0, la verdad:** no es cobertura y no se ofrece como tal —`run_tests.py:2511` (`categorias_disponibles_excluye_el_centinela`, el helper que comparten el test de migración del centinela y el del catálogo) ya afirma `assert cats`, y en la suite completa ese test se ejecuta **antes** y es el que muere primero. E0 se queda por ser la **precondición** que hace legible el test (y E2 no se ejecuta contra nada) y por dejar el 3-E autocontenido al correrlo dirigido; además está **subsumida por E4**, que es la que lleva la cobertura de verdad. **Corrección de una afirmación falsa que estaba en el docstring del #3 (fila 107) y aquí:** se decía que el techo (f) del estático mataba a `E_COSMETICA_IF` (`cb.grid(row=i // (2 if pack.is_gaming else 1), ...)`). **Medido con la suite entera: NO lo mata, y el 3-E tampoco.** El techo (f) declara «un bucle ENCIMA de la construcción cuyo ITERABLE es una elección de `is_gaming`» y su propio `COSMETICA_IF` es `if (2 if pack.is_gaming else 1) == 2:`, que cambia la **cantidad**; la forma escrita cambia el `row=` y no la cantidad, así que está **fuera** de (f) por el texto del propio techo. Los dos tienen razón en dejarla pasar: con ella las 18 casillas se siguen viendo, una por fila, y rechazarla sería el falso positivo del otro lado. La regla anti-rodadura que reparte las dos capas va en el docstring de este test y en el de la fila 107 |

> Los diecinueve van del lado **headless**, no del de backend, y es por donde se corrigen: todos
> tocan alguna vista, asi que van **despues** del marcador de `run_tests.py`. El reparto
> derivado por el check 7 de `validate_docs.py` es **112 backend + 44 headless** (derivado con
> `ast` el 2026-10-03 en TASK-063 iteracion 3; aqui decia 25, que era un numero renumerado a
> medias y se contradecia con su propia frase de "los dieciocho": 10 + 18 = 28, y luego 10 + 19
> = 29; TASK-061 lo subio a 32 con tres sondas de tooling puro **puestas despues** del marcador,
> y su iteracion 2 lo subio a 112 backend con **cinco mas ANTES** del marcador, porque son
> tooling puro y no abren ventana: `ast`, subproceso con repo temporal y llamada directa a
> `validar_repo`. TASK-066 subio el lado headless de 32 a **41** con sus nueve sondas, y el
> ciclo 999 lo subio a **44** con los tres guardianes de los supervivientes: las doce van
> **despues** del marcador y ninguna abre ventana. Ojo con esto, que es una trampa de lectura:
> **"tooling puro" ya no significa
> "lado headless"**. Las tres de TASK-061 iteracion 1 quedan del lado headless y las cinco de la
> iteracion 2 del lado backend, y las dos son tooling puro. El reparto puede dar el total correcto
> mientras el reparto miente, y por eso se declara en `STATUS.md` con la linea viva del marcador.

> #### TASK-070: `_reparto_de_tests` no parte `run_tests.py` una vez por sentencia
>
> `_reparto_de_tests` (`validate_docs.py`) es la funcion que produce el reparto de arriba, y hasta el
> 2026-10-06 buscaba el marcador con `ast.get_source_segment(fuente, stmt)` **dentro** del bucle de
> sentencias. Cada llamada **parte las lineas del fichero entero**: con 1,2 MB y 196 sentencias eso son
> 196 pases completos, o sea O(n²) **en el tamano del fichero**. MEDIDO: la derivacion tardaba
> **7,25 s** de los ~12,3 s del validador entero.
>
> El arreglo son **dos lineas**: `lineas = fuente.splitlines()` una vez fuera del bucle, y dentro
> `MARCADOR_HEADLESS in "\n".join(lineas[stmt.lineno - 1:stmt.end_lineno])`. MEDIDO despues, dos
> corridas seguidas en la misma maquina y sobre el mismo arbol: el validador entero baja de
> **12,27 s a 7,14 s**.
>
> **Tres cosas que no se pueden volver a derivar de la premisa:**
>
> 1. **La premisa de "tokeniza" era FALSA.** En Python 3.13 `ast.get_source_segment` usa
>    `_splitlines_no_ff`, no `tokenize`: `tokenize.generate_tokens` se llama **0** veces. La
>    consecuencia practica es O(n²) igual, porque partir 196 veces un fichero de 1,2 MB son 196
>    pases, pero el culpable no es el tokenizador.
> 2. **La busqueda NO se puede sacar del bucle.** El marcador aparece **dos veces** en
>    `run_tests.py`, y la segunda (dentro de `_run_tests_sintetico()`) esta **por encima** de
>    `cuerpo_main`. Un `visto = MARCADOR_HEADLESS in fuente` daria `antes = 0` y
>    `desde = <el total entero>`: toda la suite por delante del marcador, **con el total
>    igual**. Es el mutante M1, y lo mata la fila 191.
> 3. **`splitlines()` y el numerado de Python no son la misma cosa en general.** `str.splitlines()`
>    parte ademas de `\n` por `\v \f \x1c \x1d \x1e \x85 \u2028 \u2029`, y Python solo numera por
>    `\n`. MEDIDO en el `run_tests.py` real: **0 apariciones** de cada uno, luego el recorte es
>    exacto hoy. Si alguna vez apareciera, el slice apuntaria a otras lineas y habria que revisar.
>
> **Superviviente declarado, no tapado:** el mutante **M5** (ensanchar el slice una linea, a
> `lineas[stmt.lineno - 1:stmt.end_lineno + 1]`) **pasa** los dos tests, porque en `__main__` hay
> **0 solapamientos entre sentencias y 0 punto y coma**, luego un slice mas ancho devuelve lo mismo.
> Es una propiedad del fichero, no del algoritmo, y nadie lo vigila.
>
> El `_ProcessServiceSpy` subio a **nivel de modulo**. Los tests #1, #5, #8 y #15 necesitan el
> mismo doble de snapshot fijo, y un doble copiado tres veces diverge en silencio; ademas su
> `kill_processes` decide la tupla que varios asserts comparan, asi que un cambio ahi los
> mueve a todos. Es el precio de un doble compartido, y esta anotado donde esta definido.
>
> Los workers se ejecutan en el **hilo principal** con el contexto `_HilosSincronos`, que
> sustituye `Thread` por uno que corre el target en el acto. Sin eso, los tests #2 y #12 serian
> una carrera: el assert puede correr antes de que el worker haga nada y el fallo seria
> **intermitente**, que es peor que no tener test.



### Las tres cifras que caducan (TASK-067 T-5)

Regla que sale de una afirmación escrita a mano que nadie vigilaba, y que este ciclo midió
por tercera vez. **Una cifra escrita a mano caduca en el commit, no en el mes.**

1. **Toda cifra de veredicto escrita en prosa lleva su fecha y su "de aquel día".** Como ya
   hacen `docs/GITHUB-SETUP-CHECKLIST.md:581` y la sección correspondiente del agregado. Sin
   fecha, una cifra es una promesa sin ancla: el lector no puede distinguir "hoy son 126" de
   "fueron 126", y las dos se leen igual.
2. **Un guard que DERIVA la cifra de la fuente no caduca; uno que la CUENTA A MANO caduca en
   el commit.** MEDIDO: el "126 OK / 0 FAIL" que afirmaba la entrada 7 de
   `.taskmaster/CHANGELOG.md` era cierto antes de `d68bf8b` y se rompió **al commitear** —el
   journal no tenía el ciclo 54—, y ese rojo lo cerró `a82dca5` a mano. El total de tests ya
   está así (lo deriva el check 7 con `ast`); el número de `OK` del validador **no**, y por eso
   se rompe. **Ésta es la razón por la que el número de `OK` no se cita como cifra estable en
   ningún sitio de este repositorio, y por la que el check nuevo de `validate_docs.py`
   escribe `len(generador.SECCIONES)` —que sale de la fuente— en vez de un número copiado.**
3. **`commitlint` mira el RANGO DEL PUSH y la release la decide `.releaserc.json`**
   (`type:docs -> release:false`). Sin esa distinción se promete una release que no sale: el
   job `commits` sale verde y no se publica nada. Por eso el commit de un ciclo de
   trazabilidad es `chore`/`docs` y **no** se promete ninguna release.

**Y la afirmación que se retracta, con la medición que la retracta (D11).** D11 afirmaba que
"nada vigila la entrada de los changelogs". **Es FALSO.** MEDIDO hoy en cámara, sobre una
copia con `git clone` real: quitar el encabezado `## CYCLE-054` del changelog **de la raíz**
(`CHANGELOG.md:1`, que es donde está; en `.taskmaster/CHANGELOG.md` el encabezado es
`## [CYCLE-054]` y la sustitución no encuentra nada — MEDIDO, y por eso la primera cámara no
tenía nada que mutar) sube el validador de **0 FAIL a 2 FAIL**, con los dos motivos
literales de `_comprobar_ancla_del_changelog` (`validate_docs.py:833`): *"rd_journal.json
registra el ciclo 054 pero el changelog legible no tiene su entrada"* y *"sin entrada para
el/los ciclo/s 054, exigido por rd_journal.json y/o por el historial de commits"*. El ancla
es **externa** (`rd_journal.json`), y por eso borrar el ciclo de los dos changelogs no borra
el requisito: eso es lo que hace que el guard exista en vez de ser una promesa.

**Lo que sí queda de D11 no es un agujero del guard, es una cifra escrita a mano** — el
"126 OK / 0 FAIL" de esa misma entrada 7 —, o sea el punto 2 de esta sección. Y la cifra
"1 FAIL → 2 FAIL" con la que se registró la refutación se midió sobre otro estado del árbol;
**hoy el mismo experimento da `0 FAIL → 2 FAIL`**, y esa diferencia es la regla 1
funcionando.

### El validador tiene UN solo camino de validación (D1–D4, TASK-057 iteración 3)

Regla que sale de tres `FAIL` seguidos del `mutation-auditor` sobre el mismo código, y que se
aplica a **cualquier** test nuevo del validador:

1. **Asienta por `validar(root)` o por el subproceso. Nunca por una función privada.** La
   diferencia no es de estilo: durante dos iteraciones la suite llamó a
   `_comprobar_ancla_del_changelog` y a `_comprobar_ancla_de_commits` **pasándoles a mano los
   argumentos**, así que el cableado que suministra esos argumentos no lo probaba nadie. Medido
   sobre el producto real: con el parser de marcadores muerto *y* el cuarto argumento sin pasar,
   `python validate_docs.py` daba `108 OK / 0 FAIL`. El fix estaba en código muerto. D1 extrajo
   `validar(root)` para que el producto y los tests ejecuten la misma ruta **por construcción**.
2. **Las funciones privadas no son objetivo de tests nuevos, pero no por irrelevantes.**
   La redacción anterior de este punto ("son unitarias-no-contractuales") era **incorrecta** y
   creaba una trampa. `test_el_ancla_de_commits_no_depende_del_que_escribe_el_journal` asienta
   por las privadas pasándoles los argumentos a mano y **es igualmente contractual**: es el único
   guardián de tres invariantes que la tabla de escenarios **no nota** —
   **U1** (la unión no sustituye al journal: el árbol espejo con journal `{46,47}` e historial
   `{46}` tiene que exigir `0` errores, construcción que no cabe en una tabla que cambia de
   historial por fila), **P1** (ciclo ≠ tarea: el parser tiene que ignorar `TASK-046`; con ese
   mutante el repo real da `107 OK / 2 FAIL` en vez de `108 OK / 0 FAIL`) y **E1** (un ancla
   ilegible nunca da verde: tiene que informar el motivo). La regla es *prefiera `validar(root)`*,
   no *las privadas no importan*: un invariante que solo asienta llamando a la privada con
   argumentos inventados por el test se queda sin guardián si ese test se borra, y nada más se
   queja. Por eso el sitio natural de la fila (f) —el encabezado borrado con la prosa que lo
   suplanta— era la tabla y no ese test: la tabla se toca al instante, y el texto que lo
   desaconsejaba lo hacia imposible.
3. **Un parámetro opcional cuyo valor cambia el veredicto es un agujero.** `journal_cycles`
   tenía default `()`, y por eso mutarlo era un cambio de comportamiento silencioso. Sin default,
   es un `TypeError` en la llamada: el validador muere con traceback y el fallo es imposible de
   confundir con un criterio. Medido en el cierre del ciclo #47: el default restaurado **aislado**
   (con la llamada intacta) es una mutación **inerte** y ningún test puede matarla, porque no
   cambia ningún veredicto; lo que el default decide es si borrar el cuarto argumento de la
   llamada es un `TypeError` o un cambio de comportamiento. Por eso el mutante que se mide es
   *borrar el argumento*, no *restaurar el default*.
4. **Los escenarios son filas, no tests.** El esqueleto real (1,7 MB) se copia **una vez** por
   test y cada escenario reescribe solo el journal, el changelog y el `GIT_DIR`. Un hallazgo
   futuro cuesta una fila de `test_el_ancla_sobre_un_arbol_sintetico_tabla_de_escenarios`, no un
   test de 40 líneas con su propia copia del árbol. Por eso esto converge donde las iteraciones 1
   y 2 no: un test más por hallazgo tapaba el mutante visible y dejaba el mismo agujero un nivel
   más abajo.
   **Limitación conocida de esa tabla:** las filas comparten esqueleto y comparten helper, luego
   comparten punto ciego. Una fila solo mide la forma de árbol que construye. La fila (f), por
   ejemplo, tapona P2/P3/H2 **porque** su changelog lleva prosa con el número y sin su
   `## CYCLE-`; contra un árbol sin esa prosa las dos versiones del código darían el mismo
   veredicto y la fila pasaría sin medir nada. Por eso cada fila se documenta con el mutante que
   mata, y no solo con su nombre.
5. **Una atribución es una afirmación que hay que volver a medir.** Cerrado el ciclo #47, el
   informe decía en qué test muere cada mutante y **tres de esas atribuciones eran falsas**: o
   apuntaban al test equivocado, o callaban que el mutante tenía más de un guardián. "Muerte en
   el test X" y "muere primero en el test X" no son lo mismo, porque la suite tiene orden y el
   primero que revienta oculta a los demás. El informe de mutación lleva ahora una columna por
   cada hecho: dónde muere en aislamiento y dónde muere primero en la suite completa, con el
   recuento de guardianes. La fila (g) es el ejemplo del punto ciego que queda escrito: mata a
   E2 por el envoltorio compartido `_informe_del_validador_real`, no por su propia aserción, así
   que si ese envoltorio cambiara la cobertura de E2 se perdería sin que nada la notase.

El informe del `mutation-auditor` vive en
`openspec/changes/2026-10-01-validator-independent-anchor/mutation-report.md`, no en la
conversación: sin ese fichero un `FAIL` no es re-auditable por nombre.

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
| 125 | `test_la_puerta_del_mensaje_exige_un_ancla_resoluble` | **TASK-059 (AC-A1, AC-A2, AC-A3, mata a M1, M2, M3):** `ancla_del_mensaje(mensaje, ids)` es PURA (no lee ficheros ni llama a `subprocess`) y devuelve `(ok, motivo)`. Con un `ids` sintetico, un mensaje sin ancla se rechaza y el motivo nombra las TRES formas aceptadas. `T-9`, `T-1`, `C-9`, `TASK-` sin digitos y `MYTASK-059` NO pasan: `T-1`..`T-9` son ids de OTRO espacio (`openspec/changes/*/tasks.md`) que no existe en `tasks.json` y no se puede resolver, luego admitirlos es un ancla de mentira. `TASK-999` tiene la forma perfecta y tampoco pasa, porque la resolubilidad es lo que convierte el identificador en ancla y no en decoracion. Y `ids` VACIO degrada a la FORMA, nunca a "todo valido". El patron de ciclo de la puerta y el del validador se comparan **caracter por caracter**: son dos copias del mismo patron y lo unico que las ata es esa asercion |
| 126 | `test_la_puerta_se_coloca_despues_del_noop_y_antes_de_add` | **TASK-059 (AC-A5, mata a M4):** el ORDEN de las cuatro fronteras del wrapper es normativo y se afirma con `ast` sobre el `git_safe_commit.py` real, por indices de sentencia: `validar_repo` < `sys.exit` del NOOP < llamada a la puerta < `run_git` del `add -A`. Antes de `validar_repo`, un `GIT_DIR` invalido con cualquier mensaje saldria con 2 en vez de 3 ("tu invocacion esta mal" y "no pude ni comprobar" se confunden); despues del `add -A` rechazaria con el arbol YA stageado, o sea mutando el arbol para luego decir que no; antes del NOOP, un arbol limpio saldria con 2 en vez de `WOPT_NOOP` + 0. Se afirma ademas que la linea `WOPT_USAGE ancla-mensaje` es la penultima sentencia del bloque de rechazo (la ultima que imprime) y que el codigo de salida es 2 y no 1. Es `ast` y no subproceso porque `get_env()` impone `GIT_WORK_TREE = REPO_ROOT` sin condiciones: el arbol de trabajo no es controlable desde fuera del wrapper (limite 1 de la propuesta, dueno `TASK-061`) |
| 127 | `test_el_rechazo_de_la_puerta_dice_que_se_espera_y_por_que_importa` | **TASK-059 (AC-A6, mata a M5 y M6):** extremo a extremo por SUBPROCESO con `GIT_DIR` temporal y el arbol de trabajo sucio **por el propio test** (un fichero untracked que crea y borpa). Sin identificador: sale con 2, la linea `WOPT_*` es la ULTIMA de stdout, dice "se espera" y "POR QUE importa", nombra las tres formas, es ASCII puro y **el indice queda intacto** (rechazar despues de stagear seria peor que no rechazar: deja al actor creyendo que no ha cambiado nada). Con identificador: sale con 0, imprime `WOPT_COMMIT_OK` y el commit resultante LLEVA el testigo; como el indice se vacia al commitear, se mira `git log -1 --name-only` y no el indice |
| 128 | `test_las_plantillas_del_bucle_pasan_la_puerta_del_producto` | **TASK-059 (AC-C1, mata a M7):** se extraen del repo las plantillas literales de `git_safe_commit.py "..."` de `.agents/**` y se pasan por `ancla_del_mensaje` con los ids REALES de `tasks.json`. MEDIDO el 2026-10-04 antes de instalar la puerta: **0 de 5 pasaban**, e instalar la puerta sin tocar las plantillas mataba el bucle en su primer commit, con certeza y no con probabilidad. El marcador `TASK-NNN` de las plantillas se sustituye por un id que existe de verdad, porque la puerta exige RESOLUBILIDAD; y un mensaje que sea SOLO un marcador (`...`, `<mensaje>`, `[ID_TAREA]`) se salta a proposito, porque es una mencion del comando y no una plantilla que se copie y pegue. Hay un control negativo (la misma puerta rechaza un mensaje sin ancla) para que el test no pueda pasar por no hacer nada |
| 129 | `test_el_check_9_de_los_hashes_del_journal_sobre_un_arbol_sintetico` | **TASK-059 (AC-B1..AC-B5, mata a M8..M13):** el campo `commits` de `rd_journal.json` con las cinco reglas: R1 forma (`fullmatch` del elemento y NO `search`), R2 resolubilidad, R3 vocabulario cerrado de `causa`, R4 antidolar y R5 techos. Siete filas sobre el esqueleto REAL copiado una vez, con un `GIT_DIR` temporal y **commits REALES** de ese repo, para que "resuelve" sea un hecho de git y no una afirmacion del codigo. Los pares que matan: el mismo hash con texto libre FAIL y el mismo hash desnudo 0 FAIL (mata `search`); el mismo hash muerto sin declaracion FAIL y con `commits_perdidos` 0 FAIL; un hash declarado perdido que RESUELVE FAIL (R4, sin el la solucion degenerada es declarar como perdidas lo que no se quiere sanear). Los techos se **leen del producto** (`MAX_HASHES_PERDIDOS`, `MAX_CICLOS_SIN_HASH`), se exige que su comentario lleve la FECHA de la medidad de la que salen, y el techo cuenta DECLARACIONES y no repeticiones de un mismo hash. Ninguna expectativa se deriva del fichero que se valida: los numeros los fija la fixture |
| 130 | `test_el_check_9_se_cablea_en_el_camino_real_del_validador` | **TASK-059 (AC-B6, mata a M14):** el patron que ya pago tres veces (ciclos #47 y #49): los tests llamaban a las funciones privadas pasandoles los argumentos a mano, el cableado que suministra esos argumentos no lo probaba NADIE, y el fix se quedaba como **codigo muerto en el camino real**. Copia el `validate_docs.py` REAL a un arbol temporal con el esqueleto que `validar()` lee y lo ejecuta como SUBPROCESO, de modo que se ejercitan `main()`, `validar()`, la linea de cableado y el `sys.exit`. Contra un `commits` con texto libre tiene que salir con rc != 0, y la segunda mitad escribe el MUTANTE (el cableado sustituido por `pass`) y exige que el residuo desaparezca del informe: asi el test demuestra su capacidad de matar en vez de declararla. **TASK-087 (ciclo 70, ronda de cierre): el MISMO test crece con los tres huecos que dejo la auditoria del fix `f5bec54` (PARTIAL, 14 de 16 mutantes muertos) y el RECUENTO NO SE MUEVE (235 = 159 + 76). (A) K-8, el guard VACIOABLE: `validar()` podia dejar de llamar al check 11 y el validador daba 160 OK, 0 FAIL y SIN REGISTRO sin que nada lo notara; aqui se exige que el REGISTRO del check 11 aparezca en el informe y su propio MUTANTE (la llamada sustituida por `pass`) lo haga desaparecer, con el control positivo de que con todo cableado el REGISTRO esta. (B) los DOS limites que el docstring del gate NO declaraba (la evidencia commiteada puede NO ser el log real, K-10b; el sha NO se resuelve contra nada, K-12): se comprueba sobre el TEXTO de `validate_docs.py` y que la lista diga que NO es exhaustiva. (C) el emisor NO pisa la evidencia de los mutantes que no le pasas: se emite el veredicto de UN mutante de un catalogo de DOS y la evidencia del otro tiene que quedar BYTE A BYTE igual. **(D) TASK-090 (ciclo 71): el gate tiene que DISTINGUIR, no solo EXISTIR.** Lo de arriba vigila el CABLEADO del check 11, sus LIMITES y el emisor; NADIE vigilaba que el gate ACUSE. MEDIDO en camara desechable: con el CUERPO de `_comprobar_veredictos_de_mutacion` VACIO y el REGISTRO puesto, el validador daba **0 FAIL** sobre un catalogo que se contradice a si mismo (el agujero D-B) y la suite se quedaba en VERDE. Aqui el guard es de **PRODUCTO**: se monta un corpus SINTETICO en el esqueleto temporal (SEIS entradas de journal y QUINCE sentinelas, con sus catalogos, su journal y su evidencia) y se exige que el gate **acuse a los DOCE contradictorios** (cuatro del JUICIO del gate, cinco de sus PRECONDICIONES ESTRUCTURALES y tres mas: la entrada del LIMITE, el catalogo sin linea en el journal, el informe que se queda corto y los changelogs contra la evidencia) y **calle sobre los TRES coherentes** (D1); la **CONTRAPROUEBA** (D2) vacia el CUERPO del gate —con el REGISTRO puesto, que es lo UNICO que el guard de cableado mira— y exige que esa acusacion **desaparezca** y que el REGISTRO **siga**: sin D2 la D1 podria cumplirse por un motivo equivocado (un gate que acusa SIEMPRE tambien la cumpliria); y D3 restaura el esqueleto. El corpus tiene que ejercitar **todas** las ramas que el guard dice vigilar: con una sola contradiccion, un solo orden y una sola entrada de journal, cuatro mutantes del gate (M-94, M-95, M-99 y M-100) se comportan **igual que el gate sano** y el guard no tiene por donde verlos. **(D-bis) TASK-090 (segunda ronda del guard): las CINCO PRECONDICIONES ESTRUCTURALES DEL GATE.** El guard de (D) mide el JUICIO del gate (que acuse al contradictorio y calle sobre el coherente), pero el gate tiene CINCO ramas mas, que son sus PRECONDICIONES ESTRUCTURALES: el sha de la linea contra el del catalogo, el `asa` contra los tests definidos, el frame de la evidencia contra el `asa`, el bloque de maquina del informe contra el journal y el journal contra el catalogo. MEDIDO el 2026-10-22 (ronda 2 del `mutation-auditor`): con el corpus de (D), que solo ejercitaba el JUICIO, los cinco mutantes propios M-102..M-106 **sobrevivieron**, luego el corpus era estrecho y el guard no tenia por donde verlos (el mismo fallo de la ronda anterior, otra vez). aqui se anaden **cinco centinelas mas**, uno por rama, y cada uno es el caso que **solo** su rama puede caza (los demas estan en regla en todo lo demas: el sha del centinela del sha es el ajeno y el resto coincide; el asa del centinela del asa no existe y su evidencia muere en ese mismo asa; el frame del centinela del frame nombra otro test y todo lo demas esta en regla; el bloque de maquina del informe del centinela del informe lleva un sha que el journal no lleva; y el mutante del centinela del catalogo lo declara el journal y no lo declara el catalogo). Si una de las cinco ramas vuelve a morir, el `[FAIL]` de **su** razon desaparece y la celda que la vigila cae, con el motivo `EL GATE NO DISTINGUE` (el mismo de las otras tres, para que el log del mutante diga la verdad). El RECUENTO NO SE MUEVE: no hay ningun `test_*` nuevo. El RECUENTO NO SE MUEVE (235 = 159 + 76): no hay ningun `test_*` nuevo. **COSTE MEDIDO: 31,9 s del TEST (guard incluido), de los que ~9 s son las DOS corridas del validador sobre el esqueleto** (un 1,2 % de la suite de 735 s); el **coste marginal del validador NO cambia** (10,3 ms el check 11, medido antes y despues de este ciclo: el limite (f) son comments). **(E) TASK-090 (ronda 4): EL CHECK 12 TAMBIEN, Y NO LO VIGILABA NADIE.** MEDIDO el 2026-10-22 (ronda 4 del `mutation-auditor`): el check 12 (el paso de publicacion de la skill del motor) tenia CUATRO fallos y la suite no tenia **ni una** referencia a el (T-1): **C-9** su recorte era PROPIO y por LINEAS, luego una valla con prefijo `> ` (que es como esta la del propio SKILL.md) la leia como contenido y daba un **falso verde**; **C-6** el control del comentario HTML era de UNA linea y no tocaba la rama multilinea; **C-7** el check no estaba cableado en `validar()` y un validador mudo (ni OK, ni FAIL, ni SKIP) pasa por verde. El arreglo: el recorte es ahora el **UNICO del repo** (`_sin_la_capa_que_el_bucle_no_lee`, en `validate_docs.py`), que usan **tanto** el check 12 **como** el guard de la regla de rama (que lo LLAMA, no lo copia: dos copias de un recorte derivan), y los controles miden la valla con prefijo de cita y el comentario de VARIAS lineas. aqui, en la **misma** seccion (E) del MISMO test (el RECUENTO NO SE MUEVE: 235 = 159 + 76), se vigila: **(E1) el cableado**, en el codigo y con `ast` (una llamada, los CUATRO argumentos explicitos, sin defaults, y el check tiene que LEER con el recorte compartido); **(E2) el recorte**, medido sobre el del PRODUCTO (la valla con `> ` no es contenido, el comentario de VARIAS lineas no es contenido, la prosa de verdad si se conserva); **(E3) la ausencia de `.agents/`** (el check CALLA en un arbol sin `.agents/` y ACUSA en un arbol con `.agents/` y sin skill); **(E4) el recorrido real**, con la skill REAL en el esqueleto y el validador por SUBPROCESO (el check tiene que DECIR ALGO y no tiene que acusar); y **(E5) la contraprueba**, con la ORDEN metida en una valla con prefijo `> ` y en un comentario de VARIAS lineas (el check tiene que ACUSAR). MEDIDO: los cuatro casos **mueren** con este guard **(F) TASK-091 (ciclo 72): el gate tiene que LEER la `mutacion` del catalogo.** Lo de arriba vigila el CABLEADO, los LIMITES, el emisor, el JUICIO del gate y el check 12; lo que NO vigilaba es que el gate LEA el campo `mutacion`: MEDIDO, el gate leia `id`, `asa`, `motivo` y `sha_arbol_auditado` y **DESCARTABA** la `mutacion`, luego un catalogo que declara una mutacion que **NO EXISTE** (un `mutacion.fichero` que no es un fichero) pasaba el gate con **0 FAIL**, y lo mismo con un `ciclo: 999`. aqui el guard es de PRODUCTO, con un cambio SINTETICO **PROPIO** (que no toca NINGUNO de los QUINCE centinelas de (D)) y DOS centinelas PROPIOS cuyo ORDEN es NORMATIVO (el COHERENTE PRIMERO y el ROTO SEGUNDO, porque un gate que mire solo el PRIMERO --el mutante M-92, que ya existe en el catalogo-- tiene que quedar cogido por el SEGUNDO). Las CUATRO reglas que se vigilan (**R1**: la `mutacion` tiene forma; **R2**: el fichero que declara EXISTE y esta dentro del arbol; **R3**: el `cambio` del catalogo es el `change` de la entrada que lo ancla; **R4**: el `ciclo` del catalogo es el `cycle` de esa entrada) **NO CADUCAN** con el movimiento del codigo: comparan dos declaraciones que el repo ya hace y NO leen el CONTENIDO de ningun fichero. cada regla tiene su celda, porque una regla que nadie vigila no esta puesta: **F1** (R2), **F1-bis** (R1, con un tercer centinela cuya `mutacion` tiene la FORMA rota: `linea: 0`, la forma que el catalogo REAL tenia en M-121), **F2** (R4), **F2-bis** (R3), **F3** (la contraprueba: con la `mutacion` correcta el gate CALLA sobre los tres), **F4** (el catalogo REAL del repo, los 26 mutantes vivos, tiene que pasar el gate con **0 FAIL**) y **F5** (el limite **(g)**, que tiene que NOMBRAR las cuatro reglas que el gate SI comprueba) |
| 131 | `test_un_journal_ilegible_produce_exactamente_un_error_en_el_validador_real` | **TASK-059 iteracion 2 (mata a M15, y la midio la suite real):** con la suite REAL ejecutandose (el bloqueo de `pydantic-core` era del entorno, no del repo), el test preexistente de TASK-057 `test_el_journal_ilegible_informa_en_vez_de_reventar_el_validador` moria con `assert len(errors) == 1`: el check 9 anadia un SEGUNDO `errors.append` sobre un journal ilegible que el ancla del changelog de raiz ya habia acusado. Dos acusaciones para un hecho es ruido que entrena a ignorar el semaforo, y ese test afirma desde el ciclo #47 que **una causa produce un mensaje**: el fix va en el check, no en el test. Este fija la regla donde no existia, en el **camino real** por SUBPROCESO con el validador real copiado, porque comprobarlo solo sobre la privada deja el fix muerto en el cableado. Dos formas de ilegibilidad (contenido corrupto y **directorio** donde deberia estar el fichero, que en Windows da `PermissionError`, la clase exacta que el test de TASK-057 monkeypatchea) y una **mitad mutante** que devuelve el `errors.append` y exige que el numero de `[FAIL]` vuelva a 2, para que el test demuestre que MUERE con el fix |
| 132 | `test_los_ids_del_bolsillo_se_leen_y_la_puerta_es_fail_closed` | **TASK-059 iteracion 3 (mutacion del ciclo 52, mata a S8 corregido, S9 y el `\b` de salida de S6):** `ids_de_tareas` tenia **0 apariciones** en toda la suite, y su comportamiento estaba contradicho por tres fuentes (el docstring de `ancla_del_mensaje`, el aviso de `ids_de_tareas` y D5 de la propuesta) mientras el codigo hacia una cuarta cosa. MEDIDO: con `ids=set()`, `TASK-059` NO pasa, o sea que la puerta es **fail-CLOSED**, no fail-open como reporto la auditoria: con el tablero ilegible `TASK-` deja de aceptarse por completo y el bucle se para, mientras que las dos convenciones de ciclo siguen valiendo. Se eligio esa opcion (la alternativa es el punto ciego que TASK-059 cierra) y se corrigieron las tres fuentes. El test lo mide sobre una **COPIA del arbol** con el tablero corrupto —`REPO_ROOT` se deriva de la ruta del wrapper, luego es la unica via hermetica— y ademas, por subproceso, comprueba el `INFO` de degradacion, que sale **antes** de la `WOPT_*` y sin dejar nada stageado |
| 133 | `test_la_bandeja_no_amplia_la_excepcion_de_apagado` | **TASK-065 (LADRILLO del cambio, mata el atajo mortal):** meter los packs favoritos en el menu de la bandeja convertia la excepcion de TASK-025 —un solo clic apaga, justificada porque afectaba a UN pack— en un agujero de N packs, varios con `target_categories` activas. Misma forma que la sonda #16 de TASK-063: no mira COMO esta escrito el codigo, mira que un clic suelto no habilite nada. `puede_ejecutar` es False tras la 1.er pulsacion (que solo arma y pinta `✅ Confirmar`), True en la 2.a, y False en la 3.a porque la pendiente se consumio; ademas declara la ventana de 4 s y prueba que una pendiente CADUCADA deja de autorizar. El reloj es inyectado, asi que los 4 s se simulan |
| 134 | `test_arrancar_desde_la_bandeja_no_pide_confirmacion` | **TASK-065:** arrancar no es destructivo (TASK-023), asi que confirmar seria ruido. Las DOS mitades: el item de arranque dice `🚀 Pack` en reposo y **no dice "Confirmar" NUNCA**, ni siquiera con una pendiente armada de OTRO pack —que es el caso que importa, porque si el texto dependiera de "hay ALGUNA pendiente" en vez de "esta ESTA pendiente", el item se pintaria como "Confirmar" sin nada que confirmar—. Y el item de confirmar debe NOMBRAR el pack: sin el nombre, con varios favoritos el usuario no sabe que esta confirmando |
| 135 | `test_el_texto_del_item_y_el_cancelar_siguen_al_estado` | **TASK-065:** `Cancelar` solo aparece si hay algo que cancelar, y desaparece al cancelar y al caducar. El caso que mata al bug: una pendiente **caducada** sigue existiendo dentro de `DoubleTapGuard` (nadie ha llamado a `reset`), asi que un `is_pending()` a secas haria pintar un "Cancelar" pulsable y sin efecto. Fija ademas que cancelar **no** deja la puerta de ejecucion abierta |
| 136 | `test_pulsar_otro_favorito_descarta_la_pendiente_anterior` | **TASK-065:** el caso §3.5 de `DoubleTapGuard`, reutilizado tal cual en vez de reimplementado. Pulsar B con A pendiente descarta la de A, y por eso el item de A deja de pedir confirmacion mientras el de B la pide. Lo grave va al final: confirmar despues ejecuta **B**, y **A no puede ejecutarse** — si esto fuera True, un solo "Confirmar" mataria un pack que el usuario ya no tiene delante |
| 137 | `test_el_contrato_de_codigos_esta_atado_a_cada_linea_wopt` | **TASK-061 (AC-2, mata a S48-2):** sin subproceso y sin escritura, con `ast` sobre el wrapper **real** importado. Deriva la tabla `(WOPT_*, CODE_*)` de los 15 sitios de salida de `main()` y la exige contra la tabla escrita en el propio test: `WOPT_COMMIT_OK` 1, `WOPT_REPO_OK` 1, `WOPT_NOOP` 2 (la sobrecarga deliberada del 0), `WOPT_FAIL` 6 (la familia entera, no un caso), `WOPT_USAGE` 3, `WOPT_REPO_INVALIDO` 2. Y tres reglas mas: **ningun `sys.exit` sin linea `WOPT_*` que lo cierre** (mata al mutante que anade un `print` de mentiras), **las constantes valen 0/1/2/3** (mata al intercambio de dos valores, que la tabla no veria porque se deriva de los NOMBRES) y **`get_env()` no asigna `GIT_WORK_TREE` de forma incondicional** (mata la regresion de la paridad sin subproceso). |
| 138 | `test_un_fallo_de_git_no_sale_con_cero` | **TASK-061 (AC-1, mata a S48-2; el unico que prueba el RUNTIME):** repo y arbol **temporales**, arbol sucio con un fichero, identidad en el repo de la sonda y un `pre-commit` que sale con 1 via `core.hooksPath`. Exige `returncode == 1` (con `CODE_OK` puesto sale 0), `WOPT_FAIL commit` en stdout con la linea `WOPT_*` como ULTIMA, `WOPT_COMMIT_OK` ausente, y el indice con su propio fichero (para que el fallo sea de git y no de fixture). El testigo de no-contaminacion mira el indice y el arbol de `HEAD` del repo de sonda (que no pueden contener ninguna ruta del arbol del dueno), el `HEAD` del repo real antes/despues, y que no quede ningun fichero `_t061_*` en la raiz. El mensaje se ancla con `ciclo 999`, no con `TASK-061`, para no depender de `tasks.json`. |
| 139 | `test_el_cero_esta_sobrecargado_por_dos_desenlaces_y_solo_por_esos_dos` | **TASK-061 (AC-3):** tres filas sobre un repo y un arbol temporales. **NOOP**: arbol limpio -> `0`, `WOPT_NOOP` presente y **cero hashes** en stdout, afirmado de forma negativa y tipada (tras la linea `WOPT_NOOP` no aparece ningun `[0-9a-f]{7,40}`), que es lo que mata al mutante que imprime un hash en el no-op. **COMMIT_OK**: arbol sucio -> `0` y un hash que **RESUELVE** (`rev-parse --verify <hash>^{commit}`) y es prefijo del commit real, porque un hash con forma de hash y sin objeto es la misma mentira. **Paridad**: `GIT_DIR` sin `GIT_WORK_TREE` -> `2` y `WOPT_USAGE paridad-git`, con el indice y el `HEAD` de la sonda intactos. Esta tercera fila **falla sin mutar nada**: con el codigo anterior stageaba y commiteaba el arbol real dentro del repo de temporal y salia con `0`. |
| 140 | `test_la_puerta_de_paridad_va_despues_de_validar_repo` | **TASK-061 iteracion 2 (mata a M5):** la **POSICION** de la puerta de paridad, que hasta aqui no tenia guardian. `--verify` con `GIT_DIR` **inexistente** y **sin** `GIT_WORK_TREE` tiene que salir con **3** (`WOPT_REPO_INVALIDO`) y sin nombrar la paridad: el par esta asimetrico a proposito para que la puerta PUDIERA dispararse, y con la posicion correcta no lo hace porque el 3 gana al 2 (D2). Con la puerta antes de `validar_repo` sale con **2**. **Por que el test existente no lo caza:** `test_git_safe_commit_fail_safe` pone `GIT_WORK_TREE = root` en todas sus invocaciones, luego el par nunca esta roto ahi y la puerta nunca dispara; la justificacion que decia la regla 7 de este caso era FALSA y esta fila la sustituye |
| 141 | `test_la_puerta_de_paridad_tambien_cubre_el_modo_verify` | **TASK-061 iteracion 2 (mata a M6):** `--verify` con repo SANO y par **asimetrico** sale con **2** y `WOPT_USAGE paridad-git` como ultima linea, y **nunca** dice `WOPT_REPO_OK` (el diagnostico no puede afirmar que repo y arbol son usables si el par esta roto). Con el mutante `and not verify` sale con **0** y `WOPT_REPO_OK` mintiendo. El **control negativo** va despues y en la misma sonda: con el par ENTERO `--verify` sigue dando **0**, para que el 2 de arriba signifique "la asimetria se rechaza" y no "el wrapper esta roto" |
| 142 | `test_un_arbol_que_no_es_un_directorio_sale_con_3_y_lo_dice` | **TASK-061 iteracion 2 (mata a M7 y M8):** un `GIT_WORK_TREE` que **existe pero no es un directorio** (un fichero) tiene que salir con **3** y el motivo del **pre-chequeo** (`GIT_WORK_TREE no existe o no es un directorio`). El criterio **no** es el codigo, que sale 3 con y sin el pre-chequeo: es el **MOTIVO**, porque con `isdir` quitado (M7) o cambiado por `exists` (M8) `run_git` corre con `cwd` = un fichero y el wrapper responde `git no ejecutable`, un sintoma y no un diagnostico. Discrimina por contenido |
| 143 | `test_is_inside_work_tree_false_hace_rechazar_el_repo` | **TASK-061 iteracion 2 (mata a M9):** `rev-parse --is-inside-work-tree` que responde `false` tiene que hacer **rechazar** el repo (codigo 3), y con un `run_git` de mentira se comprueba la **reaccion** de `validar_repo`, que es lo que se prueba: la unica forma de que git diga `false` de forma fiable (cwd dentro del `.git`) depende de la version de git. El **control** va despues (`true` -> acepta), y sin el un `validar_repo` que rechazara siempre pasaria el criterio sin mirar el valor de git. Con M9 (invertir a `!= "false"`) el test muere en el criterio |
| 144 | `test_toda_linea_wopt_de_main_esta_en_la_tabla_y_cierra_una_salida` | **TASK-061 iteracion 2 (mata a M10):** la **asercion 1** del contrato de T-2, que la propuesta afirmaba y el test **no implementaba**: el `ast` de T-2 solo registra un marcador si detras hay un `sys.exit`, luego un `print` con `WOPT_*` que no cierra nada desaparecia del contador en silencio. Dos mitades: (a) el **conjunto** de marcadores que `main()` imprime tiene que ser exactamente la tabla del contrato, y (b) cada `print` con `WOPT_*` tiene que **cerrar un `sys.exit` en su bloque**, sin sentencias que no sean `print` entre medias. La (b) es la que mata a un mutante que **reutiliza** un marcador existente, donde la (a) no lo ve. **MEDIDO el 2026-10-05 (TASK-066):** esta fila tambien cazo la puerta de cabecera en su primer dia —`WOPT_USAGE cabecera-larga` y `WOPT_USAGE cabecera-regla` con un `sys.exit` COMPARTIDO por las dos ramas del `if/else` son dos lineas huerfanas— y obligo a cerrar cada `print` en su propia rama |
| 145 | `test_la_puerta_de_cabecera_rechaza_una_cabecera_de_135_caracteres` | **TASK-066 T-4 c1:** el wrapper REAL como subproceso sobre repo y arbol temporales, con el texto **exacto** de `82f52c2` (135 chars, el commit que tumbaba la corrida). Antes del fix no habia **ninguna** comprobacion de longitud: aceptaba, commiteaba, imprimia `WOPT_COMMIT_OK` y salia con **0**. Exige las tres cosas, que a la vez son falsas: codigo **2** (no 1: una puerta no ejecuta git, luego `WOPT_FAIL` seria indistinguible de un fallo de git), `WOPT_USAGE cabecera-larga` como linea ULTIMA, y **cero commits creados** (`rev-list --count HEAD` sigue en 1). El motivo tiene que decir **120 y 135**, o no hay forma de corregir el mensaje sin abrir el codigo. Mata a `LIMITE_SUBIDO_A_220` |
| 146 | `test_la_puerta_de_cabecera_rechaza_antes_de_stagear` | **TASK-066 T-4 c2 (mata a `PUERTA_TRAS_ADD`):** el criterio es **posicional** y se comprueba por **efecto**: tras el rechazo, `_rutas_stageadas` sigue vacio, `git diff --cached --quiet` sigue en **0** y el `status --porcelain` sale **identico** byte a byte antes y despues. Con la puerta despues de `add -A` el rechazo sigue dando 2 y el mismo mensaje —este test no lo vería— pero deja el indice modificado, que es el error que ya se cometio una vez con la puerta de ancla. El pre-vuelo necesita `GIT_WORK_TREE=arbol` en el `status`: la sonda deja repo y arbol en directorios DISTINTOS y sin el par el `status` ve un arbol limpio y el test pasa sin medir |
| 147 | `test_las_plantillas_del_bucle_pasan_la_puerta_de_cabecera` | **TASK-066 T-4 c3, la CONTRAPRUEBA:** las **cinco** plantillas copiables de `git_safe_commit.py "..."` de `.agents/**`, extraidas con la misma regex de TASK-059 y con el filtro ampliado a "placeholder + ancla" (`<mensaje> (TASK-NNN)` es la documentacion del argumento, no un mensaje copiable), se pasan por `clasificar_cabecera`. Sin este test una puerta demasiado fuerte atasca al bucle en su primer commit y **no se ve en ningun test que solo mire la regla**. **MEDIDO: la contraprueba encontre un conflicto real.** Dos plantillas eran `feat/fix: ...` y `feat/fix([COMPONENTE]): ...`, que **no parsean** —el `/` no es caracter de tipo para el `headerPattern`— luego CI las rechazaba con `type-empty` y `type-enum`: la puerta fiel a CI y las plantillas tal como estaban eran incompatibles. Se corrigieron las plantillas y **no** se relajo la puerta. El filtro decide **por forma**, nunca por el veredicto de la puerta, para que la contraprueba no sea tautologica |
| 148 | `test_la_puerta_de_cabecera_rechaza_subject_case` | **TASK-066 T-4 c4 (mata a `SOLO_LONGITUD`):** subject entero en mayusculas con longitud **valida** (<=120) -> rechazada, y la asercion mira la **REGLA** en el motivo, no solo el rechazo. Y el **control en la otra direccion**: un subject que solo **empieza** por mayuscula y lleva espacios (`T-9 afirma el invariante`) tiene que **PASAR**, porque es lo que hace commitlint, y el bucle lo usa en sus plantillas. **MEDIDO y corrige la premisa del plan:** `subject-case: [2, never, [upper-case, pascal-case]]` NO es "no empezar por mayuscula"; rechaza el subject entero en mayusculas y el PascalCase. Con el criterio real el rango historico tiene **siete** commits rojos, no ocho, y `92368ad` no incumple ninguna regla |
| 149 | `test_el_corpus_congelado_de_cabeceras_reales` | **TASK-066 T-4 c5, el que ata el host al runner:** el clasificador contra **once cabeceras reales congeladas con su SHA** —las **siete** largas de `41b8061..4d86908` y las dos de TASK-061 se rechazan por `header-max-length` comprobando que la longitud que MIDIO coincide con la de la fixture, cuatro limpias del mismo rango se aceptan, y dos tipos con barra se rechazan por `type-empty`. Congelado y **no derivado de `git log`**: la historia se mueve y el test debe seguir significando lo mismo dentro de tres ciclos. Sin el, un limite escrito a mano en el wrapper pasaria mientras `.github/workflows/release.yml` sigue diciendo otra cosa. Mata a `LIMITE_SUBIDO_A_220` por contenido |
| 150 | `test_la_salida_canonica_declara_la_rama` | **TASK-066 T-4 c6 (mata a `SIN_INFO_RAMA` y a `RAMA_DE_HARDCODE`):** dos mitades. (1) `INFO rama:` sale con el **valor real** de la rama del repo de la sonda, afirmado por contenido: si dijera un literal o `desconocida` con el repo legible, el test muere. Antes el wrapper no tenia ni una coincidencia de `branch`. (2) la rama es **AVISO y no rechazo**: en una rama de publicacion sale **codigo 0**, con `WOPT_COMMIT_OK` presente, un bloque `AVISO rama:` y la palabra `beta` nombrada. Esta segunda mitad es la que distingue el diseno de un `sys.exit`, que bloquearia el commit legitimo del dueno en la rama de release. Pre-vuelo en las dos: la rama tiene que resolver a un NOMBRE y el arbol tiene que estar sucio |
| 151 | `test_la_puerta_de_cabecera_usa_las_cuentas_de_la_config` | **TASK-066:** `clasificar_cabecera` es pura y **no** lee `.commitlintrc.json` a proposito —leerlo en caliente haria que en un repo sin config la puerta quedara muda y **verde**—, asi que sus numeros viven en dos sitios. Esta fila ata los dos: compara `LIMITE_CABECERA` con `header-max-length: [2, always, N]`, `TIPOS_ADMITIDOS` con `type-enum`, que las cuatro reglas de nivel 1 queden en nivel **2**, y que `subject-case` siga siendo `["upper-case", "pascal-case"]`. Sin ella, los dos sitios divergen en silencio y la puerta deja de ser la misma regla que CI justo cuando alguien toca la config |
| 152 | `test_la_regla_de_rama_esta_escrita_donde_el_bucle_la_lee` | **TASK-066 T-5, MITAD POSITIVA:** la norma esta en los **tres** ficheros (`SKILL.md` 0-bis, `openspec-dev/agent.md` Entorno, `AGENTS.md` punto 2 de Documentacion Continua) y por sus **dos** mitades, no "la palabra beta": `_FRASE_DESTINO` (el bucle comitea y empuja a `beta`) y `_FRASE_PROHIBICION` (`main` solo recibe `beta` por fast-forward). Exigir las dos es lo que mata a `REGLA_EN_UN_COMENTARIO` en su mitad positiva —"trabaja en beta" esta en el fichero y no es una regla, porque no dice que hacer con `main`— y exigir los tres es lo que mata a "escribi la regla donde nadie la lee". La busqueda normaliza por lineas y quita el `>` de las citas de bloque, porque el `>` de markdown es marca y no contenido |
| 153 | `test_ninguna_plantilla_de_commit_nombra_main` | **TASK-066 T-5, MITAD NEGATIVA, la que de verdad discrimina:** ninguna plantilla literal de commit de `.agents/**` ni de `AGENTS.md` puede nombrar `main` como destino. Se mira todo `.agents/**`, no solo los tres ficheros de la regla, y se miran tambien `git commit -m` y `git push`, porque la prohibicion es sobre el **destino**. Sin esta mitad el test pasa con un comentario nuevo que no cambia nada: es el mismo modo de fallo que el muro 131/135. Mata a `REGLA_EN_UN_COMENTARIO` por la via negada y a `PLANTILLA_CON_MAIN`, que es el mutante que de verdad devolveria el rojo, porque un ejemplo contradiciendo al contrato gana: es lo que se copia. **CUARTA FORMA, anadida el 2026-10-05 con su mutante medido:** el `git push ... main` **SIN comillas** se cuelaba por debajo porque `git\s+push[^|"\n]*(?:"([^"]*)")?` captura cadena vacia y el `if not texto.strip()` la salta. Se vigila, pero **solo dentro de una valla PLANTILLA** (la que lleva dentro un `git_safe_commit.py "..."` o un `git commit ... -m "..."`), porque el destino sin comillas es tambien el del comando **legitimo de T-3** (`AGENTS.md:85`) y un guard que acuse al dueno por su propia publicacion es peor que el hueco que tapa. Tres controles: (1) la forma sin comillas dentro de una plantilla sale como infraccion —MEDIDO, sin ella la suite sigue en VERDE—, (2) el bloque de publicacion legitimo **no** sale, y (3) el comando legitimo **sigue existiendo en `AGENTS.md`**, para que la excepcion no se pueda acortar en silencio |
| 154 | `test_la_puerta_de_cabecera_rechaza_un_tipo_fuera_de_la_lista` | **TASK-066 T-4, GUARDIAN H1 (mata a `TIPO_SIN_COMPROBAR`):** tres tipos fuera de `TIPOS_ADMITIDOS` (`wip`, `actualiza`, `merge`), de la forma que el parser de CI acepta como tipo para que lo que falle sea `type-enum` y no `type-empty`, y cada uno tiene que rechazarse **nombrando la regla en el motivo**. El caso muere por ESA asercion y no por el recuento de lineas `WOPT_USAGE` de otra sonda, que mediria el contrato de `main()`. La mitad final es el wrapper REAL como subproceso sobre repo y arbol en `%TEMP%`: `wip: ...` sale con 2, sin `WOPT_COMMIT_OK` y con la linea `WOPT_*` de ultima, porque el dano de H1 es el commit `wip:` que **sale** del wrapper y tumba despues el job `commits`, con `verify`, `release` y `build` detras por su `needs`. Pre-vuelo: la lista tiene >= 10 tipos y el caso cabe en `LIMITE_CABECERA`, para que lo que muera sea el tipo |
| 155 | `test_la_sonda_del_head_no_depende_del_desacople_del_vfs` | **TASK-066 T-4, GUARDIAN H2 (mata a `RUTA_FIJA_EN_LA_SONDA`):** El fix de `_head_del_repo_real()` no vigila nadie, y el mutante dejaba la suite EN VERDE sin el guardian. El test simula el **runner de GitHub** --donde `%LOCALAPPDATA%\woptimizer_git\.git` no existe-- con el truco que ya usa `test_el_ancla_de_commits_no_depende_del_que_escribe_el_journal`: `LOCALAPPDATA` a un temporal y `GIT_DIR` fuera del entorno, y exige el MISMO HEAD que con el entorno real. La muerte es el mensaje literal de "no se pudo leer el HEAD del repo real ni a la tercera" (corrida 37244051847), no una excepcion. Sin `skip`: dos pre-vuelos (HEAD legible, desacople presente) aseguran que mide, y el `finally` restaura el entorno entero porque un entorno envenenado hace fallar la sonda dos pasos despues, en el test equivocado. Exige el descubrimiento de `_entorno_git_del_repo()`, cuya candidata del `.git` del arbol admite **fichero puntero** `gitdir:` y no solo directorio (medido: en este host `.git` son 57 bytes de puntero, luego `isdir` lo descartaba). **MEDIDO y CORREGIDO el 2026-10-05, y retira un 🟡 que decia que este guardian era "de fuerza parcial aqui":** las dos mitades de ese 🟡 eran falsas. (a) La premisa de que la constante de modulo ya venia expandida en el import es FALSA, porque `_cargar_el_wrapper()` **re-ejecuta el modulo en cada llamada sin cache**: con `LOCALAPPDATA` en un temporal la constante sale ahi, luego el mutante alcanzable (el `expandvars` de `git_safe_commit.py:93`) **tambien muere en este host**. (b) "con `expandvars` al llamar muere por `NotADirectoryError`" es FALSA: un rc de git distinto de 0 no es una excepcion de Python, y lo que lo hace muerte util es el `raise AssertionError` del propio test. El unico caso que escapaba era una ruta escrita a mano que solo existe en la maquina del dueno y que **CI mata** porque alli no existe: un **mutante INERTE**, no un hueco. **El guard no se relaja** |
| 156 | `test_la_forma_t_menor_no_pasa_aunque_exista_su_task` | **TASK-066 T-4, GUARDIAN H3 (mata a `ANCLA_T_MENOR`):** la forma corta `T-NNN` tiene que rechazarse aunque `TASK-NNN` **exista** en el conjunto. Los seis tests de la puerta del mensaje no lo veian porque todos probaban `TASK-`, `CYCLE-` o `ciclo N`, y sus casos de forma corta (`T-1`, `T-9`, `T-12`) apuntaban a ids que NO estaban en el `ids` inyectado, luego relajar `_RE_TASK_ANCLA` a `\bT(?:ASK)?-(\d{1,4})\b` no cambiaba ningun veredicto: el caso que discrimina es al reves, una forma corta que resuelve a un id que SI existe (por eso el pre-vuelo exige que `TASK-061` resuelva). El rechazo tiene que ser el de SIN ANCLA del producto. Contraprueba en el mismo test: `TASK-059`/`TASK-061` siguen pasando, porque "rechazar `T-` entero" es un fix que nadie nota y deja al bucle sin poder comitear |
| 157 | `test_la_puerta_de_cabecera_rechaza_un_subject_vacio` | **Ciclo 999, PASO 4 BIS, S3 (mata a `if not _subject:` -> `if False:`), severidad ALTA:** la regla `subject-empty` **no tenia ningun test**, luego la guarda 4 de `clasificar_cabecera` (`.taskmaster/git_safe_commit.py:579`) se podia borrar y la suite seguia verde. El dano esta MEDIDO en tres pasos: la puerta aceptaba `clasificar_cabecera("fix(ciclo 999): \n\ncuerpo")` como `(True,'','')`, el **wrapper real salia con 0 y CREABA EL COMMIT**, y la sonda independiente de las seis reglas rechaza esa cabecera con `type-empty`, luego el job `commits` tumba la corrida y con su `needs` caen `verify`, `release` y `build` (no sale el `.exe`). Tres mitades: (1) la puerta clasifica como `subject-empty` y no como otra regla; (2) el **wrapper real** sale con 2, nombra la regla, **no crea ningun commit** y no stagea nada, que es el dano medido en el camino de verdad; (3) **contraprueba**: un mensaje de dos lineas con subject de verdad PASA, porque "rechazar toda cabecera con dos lineas" atasca el bucle. **La trampa, y por que el caso es de DOS LINEAS:** `parse_args` hace `.strip()` del mensaje entero (`git_safe_commit.py:299`), luego una cabecera de una sola linea que acaba en `": "` se queda en `"fix:"` y la puerta responde **`type-empty`** antes de mirar el subject. Con `"fix: "` este test no mediria nada |
| 158 | `test_el_git_dir_ajeno_no_pasa_la_verificacion_del_arbol` | **Ciclo 999, PASO 4 BIS, S8 (mata a la verificacion DECORATIVA):** `_entorno_git_del_repo()` forzaba `GIT_WORK_TREE=repo_root` antes de `rev-parse --show-toplevel`, y con el arbol forzado esa comprobacion pasa para **CUALQUIER** repo valido. MEDIDO: montando un repo ajeno y poniendo `GIT_DIR` a el, la funcion lo **devolvia** y `_head_del_repo_real()` leia `cef3e159e345` en vez de `9e83c5aeaa06`. El arreglo es comparar `--absolute-git-dir` contra la referencia leida del propio arbol con un entorno **limpio** (la unica forma de no circular), y este test es **host-independiente**: no simula el entorno sino que monta un repo ajeno de verdad. Tres mitades: (1) el repo ajeno se RECHAZA; (2) **control**: sin `GIT_DIR` en el entorno el helper sigue encontrando un repo, porque "rechazar todas las candidativas" no es el fix y dejaria la sonda sin repo; (3) **control**: el repo ajeno es sano y `rev-parse --absolute-git-dir` responde, para que (1) mida la decoratividad y no una fixture rota. Camara en `%TEMP%` y `os.environ["GIT_DIR"]` restaurado |
| 159 | `test_la_regla_de_rama_no_vive_en_un_comentario_ni_en_una_valla` | **Ciclo 999, PASO 4 BIS, S7 (mata a `BUSQUEDA_EN_CRUDO` y a `REGLA_EN_UN_COMENTARIO`):** la mitad positiva de T-5 normalizaba el fichero quitando `>` y uniendo lineas, y con esa normalizacion encontraba las dos frases de la regla **dentro de un comentario HTML** y **dentro de una valla ```` ``` ````**. O sea que probaba "las frases estan en el fichero", no "son contenido que el bucle lee". El filtro `_sin_la_capa_que_el_bucle_no_lee()` excluye esas DOS capas (y desde el 2026-10-22 **DELEGA** en el recorte del PRODUCTO, el mismo `_sin_la_capa_que_el_bucle_no_lee` de `validate_docs.py`: el check 12 usa el MISMO y no una copia, porque MEDIDO el recorte PROPIO del check 12 no veia la valla con prefijo `> ` y daba un falso verde) y **no excluye `#`**, porque en markdown `#` es un ENCABEZADO y las reglas empiezan con `>`, luego excluirlo abriria un agujero del mismo tipo. Tres controles, y sin ellos la guarda no miraria nada: descarta un comentario con las dos frases, descarta una valla con las dos frases, y **conserva** la cita de bloque con `>` y lo que hay **bajo** un encabezado con `#`. **MEDIDO y CORREGIDO el 2026-10-05, y este es el P1 del cierre:** el docstring decia que el tercer control "es el que impide el arreglo de *excluir tambien `#`*", y **no lo impide** — con el recorte tirando de las lineas que empiezan por `#` la suite sigue en VERDE, porque en los tres ficheros hay **cero** lineas que a la vez empiecen por `#` y lleven la regla. La mitad del `>` **si** muerde: tirando de las lineas `>` mueren los dos tests con el motivo literal *"la cita de bloque con `>` es PROSA que el bucle lee, y el filtro no puede descartarla"*. El arreglo fue el **texto**, no el filtro |
| 160 | `test_la_ruta_de_datos_no_sigue_al_ejecutable` | **TASK-069 T-2, TEST 1. EL aserto QUE ES el bug, escrito:** con `sys.frozen` a `True` y `sys.executable` en `<temp>\A\woptimizer.exe` se resuelve `data_dir()`, y despues en `<temp>\B\woptimizer.exe` se vuelve a resolver; **las dos tienen que ser iguales**. MEDIDO en este host: con la ruta anterior (`_app_dir()`) hay cuatro `profiles.json` con datos y el mismo concepto de pack ("sync") tiene **tres UUID distintos** segun la carpeta desde la que se arranco. El control del otro lado, con el MISMO ejecutable, da la misma ruta dos veces, para que el test no este afirmando que la funcion sea la identidad |
| 161 | `test_la_ruta_de_datos_va_al_apdata_forzado` | **TASK-069 T-2, TEST 2. La PERTENENCIA, con el destino decidiendo el test:** `%APPDATA%` y `%LOCALAPPDATA%` se fuerzan a un `mkdtemp()` antes de resolver y se exige que la ruta caiga DENTRO de ese temporal, luego no puede pasar por coincidencia de rutas de ESTA maquina. Se afirma ademas que el override por entorno tiene el **mismo nombre en el codigo y aqui** (`WOPTIMIZER_DATA_DIR`): un override que el test no puede encontrar no es un override, y sin el no habria forma de probar nada sin el perfil real. El `%TEMP%` de Windows esta DENTRO de `%LOCALAPPDATA%`, y por eso el criterio es la pertenencia al temporal y no la negacion del perfil |
| 162 | `test_la_ausencia_de_packs_avisa_donde_esta_el_candidato` | **TASK-069 T-1. El caso de la tarea, y su muerte sin el fix:** MEDIDO, hoy `load()` con `os.path.exists == False` salta todo el bloque de corrupcion, no toca ningun atributo y `mensaje_danado()` devuelve `None`, o sea que "el usuario perdio sus packs" era **indistinguible de "instalacion limpia"**. El test pone un `profiles.json` vago en el candidato y exige tres cosas: la AUSENCIA observable (`ruta_sin_packs`), el candidato nombrado (`packs_en_otra_ruta`), y un mensaje con **las DOS rutas**. La cuarta mitad mira el `woptimizer.log` REAL y exige que nombre el candidato con su ruta absoluta (Trampa #14, nada se traga en silencio) |
| 163 | `test_una_instalacion_limpia_no_avisa_de_nada` | **TASK-069 T-1, CONTRAPROUEBA. Mata al mutante `SIEMPRE_AVISAR`:** destino inexistente y NINGUN candidato con datos tiene que dar `mensaje_danado() is None`. Sin esta fila, el mutante que avisa siempre pasa el test de al lado y el caso legitimo y mayoritario --una instalacion nueva-- le ensena al usuario un problema que no tiene y presenta un Gaming de fabrica como si fuera una incidencia. La segunda mitad exige ademas que no se haya creado el fichero: `load()` sigue siendo de SOLO LECTURA con el destino |
| 164 | `test_el_diagnostico_no_toca_un_pelo_del_candidato` | **TASK-069 T-1, CONTRAPROUEBA. Mata al mutante `AVISAR_Y_NORMALIZAR`:** el `sha256` del `profiles.json` del candidato es el MISMO antes y despues de arrancar el servicio, y `os.listdir()` del directorio tiene el mismo numero de entradas. T-1 es un instrumento de medicion, y un instrumento que normaliza el sujeto para "asegurarse de que se lee" destruye la prueba y el dato |
| 165 | `test_la_migracion_copia_el_1_0_0_y_no_pierde_nada` | **TASK-069 T-3, EL TEST DE MIGRACION, con la forma REAL de la 1.0.0** (medida en `Downloads\profiles.json`: `gaming` con 5 `target_categories` y 2 `keepers`, mas el pack `8fefbc22` "sync" con SUS TRES apps absolutas). El destino se **relee desde disco** y se compara con el origen: un "migro bien" sin relectura no es una migracion. Se afirma que el Gaming conserva las **cinco** categorias y los **dos** keepers --cinco donde el usuario habia escogido dos, y keepers que son la lista anti-brick-- y que el ORIGEN sigue en su sitio. Un test que migra un `{"packs": {}}` vacio no mide la migracion: mide que se copia un fichero sin nada dentro |
| 166 | `test_la_migracion_deja_el_origen_intacto_byte_a_byte` | **TASK-069 T-3. LA FILA QUE MATA LA IRREVERSIBILIDAD.** El `sha256` del ORIGEN y el de su `.bak` son identicos antes y despues. Por que discrimina y no es un aserto mas: con el mutante `MOVE_EN_VEZ_DE_COPY` el origen ya no existe, el `sha256` no se puede leer y **esta** fila muere, mientras un "migro bien" FALSO pasa cualquier otro aserto del test de migracion porque los ids, las apps y las categorias estan todos en su sitio despues de mover. Sin esta fila, la irreversible pasa la suite entera. El `.bak` va aparte porque la migracion **no lo consulta ni lo pisa**: esa politica es de `_es_legible()` en el `save()` |
| 167 | `test_la_migracion_revierte_al_origen_si_el_destino_es_ilegible` | **TASK-069 T-3. LA PRUEBA DE REVERSION, y es un test APARTE a proposito:** con el destino YA POBLADO se lo corrompe a proposito (sin `.bak`, para que lo que se mide sea la reversion y no la recuperacion de TASK-030), se vuelve a resolver y se exige que la resolucion **cae al ORIGEN** y devuelve los MISMOS packs, con `fichero_danado` observable y los keepers anti-brick intactos. Sin separarla, "copio y me olide" y "se volver" darian el mismo veredicto. La ultima mitad exige que el destino corrupto **se quede en disco**: reventarlo ahi seria la irreversible que este ciclo vino a quitar |
| 168 | `test_la_migracion_no_escribe_fuera_del_temporal_forzado` | **TASK-069 T-3, CONTRAPROUEBA DE HERMETICIDAD. Mata al mutante `SIN_OVERRIDE_ENTORNO`:** el destino por defecto de la app tiene que caer DENTRO del temporal forzado por `WOPTIMIZER_DATA_DIR`, y `PROFILES_FILE` no puede volver a caer dentro del arbol del repo. Con ese mutante el test escribiria en el `%APPDATA%` de verdad y, en el peor caso, encima del `profiles.json` del dueno: un test que puede destruir la casa no es un test. **MEDIDO y corregido:** el criterio NO puede ser "la ruta no empieza por `%LOCALAPPDATA%`", porque `%TEMP%` de Windows esta DENTRO de `%LOCALAPPDATA%` y el guard morderia un blanco con el temporal que el propio test crea |
| 169 | `test_el_gaming_repuesto_se_declara_con_las_categorias_y_los_keepers` | **TASK-069 T-4. LA FILA QUE IMPORTA, y es de SEGURIDAD, no de UX:** un `profiles.json` SIN `gaming` se resuelve, `gaming_repuesto` es observable y el mensaje **nombra las cinco `target_categories` y los dos keepers** repuestos, uno a uno. MEDIDO: `_ensure_gaming_pack()` inserta `DEFAULT_GAMING_PACK` sin tocar ningun atributo, luego el mensaje es `None` y el test muere en la primera asercion. Por que importa: perder el fichero del usuario NO daba packs vacios, daba un Gaming Mode **mas agresivo** y la DESAPARICION de la lista anti-brick de TASK-023/030, que el codigo creia puesta. Un "se ha restaurado el gaming" generico no dice que se apaguen cinco categorias en vez de dos |
| 170 | `test_los_keepers_del_usuario_no_crecen_sin_declaracion` | **TASK-069 T-4, LA FILA DE SEGURIDAD. Con su control negativo:** con el gaming DEL USUARIO (2 categorias, `keepers: []`, que es el de `dist\profiles.json` de este host) presente, la lista efectiva sigue vacia y `gaming_repuesto` es `False` --sin ese control, la fila de al lado podria morir por una fixture rota y no mediria nada. Con el fichero delante y SIN su gaming, la lista CRECE de `[]` a la anti-brica del default, y lo que se exige es que el crecimiento sea **VISIBLE**: el atributo puesto y los dos keepers en el mensaje. Y no que el valor sea el antiguo: restaurar los keepers del usuario seria inventar una funcion de recuperacion que no existe y que no se ha pedido |
| 171 | `test_el_contrato_de_persistencia_no_promete_el_ejecutable` | **TASK-069 T-5. El guard del contrato, y muere POR CONTENIDO:** `docs/ai/architecture.md` y `docs/ai/data-models.md` tienen que decir `%APPDATA%` y hablar de `profiles.json`; volver a "junto al ejecutable" produce FAIL aunque el nombre del fichero siga presente. Es exactamente el fallo que el `mutation-auditor` de TASK-067 acaba de cerrar en el agregado `llms-full.txt` --guard por nombre, con el contenido caducado al 57,9 %--: con el guard por nombre el documento puede mentir entero y la sonda sigue verde. La CONTRAPROUEBA es la mitad que lo hace medir: una COPIA del documento con la linea mutada tiene que dejar de cumplir, y sin ella un guard que devuelve siempre `True` pasa en verde |
| 172 | `test_la_comprobacion_de_la_cuadra_es_de_verdad_una_comprobacion` | **TASK-069 T-3. NACE DE MEDIR UN SUPERVIVIENTE, y por eso tiene la forma que tiene.** MEDIDO: con la comparacion escrita en linea dentro de `_migrar_desde()`, el mutante `SIN_RELECTURA` --convertirla en `if False`-- **SOBREVIVIA a la suite entera**, porque en el camino feliz la copia siempre cuadra, luego el `if` no llega a ejecutarse nunca y su valor da igual. Una comprobacion que solo se puede matar en el camino que no se prueba no es una comprobacion. Por eso `_cuadra()` vive aislada como metodo estatico con la comparacion como UNICO contenido, y aqui se la ejercita sin disco. Cinco filas: un **control** de que dos `AppData` con los mismos packs cuadran (sin el, un mutante que devuelve siempre `False` tambien mata y el test no mide nada), la copia que pierde packs, la que tiene uno de mas, **la que tiene el MISMO numero con ids distintos** --la que de verdad discrimina, porque un mutante que compara solo `len` pasa las tres anteriores-- y el subconjunto |
| 173 | `test_el_guard_de_ausencia_ignora_a_la_instalacion_limpia_sin_revistar` | **TASK-069 T-1. Mata a `SIEMPRE_AVISAR` POR ASERCION, y existe por una medicion.** Con el mutante que quita el `return` de `if destino or not con_datos:`, el caso de instalacion limpia revienta con `IndexError: list index out of range` en `con_datos[0]`, y eso **no cuenta como muerte**: un `IndexError` no es una asercion del contrato, es un fallo de arnes disfrazado de veredicto. Aqui no hay lista que vaciar: se llama a la DECISION `elegir_ruta_de_datos()` con un predicado que dice "no hay packs en ninguna parte" y se exige la lista VACIA. Los otros dos lados evitan que la fila sea trivial: con el destino poblado no se busca nada, y con un candidato con datos se devuelve ESE y solo ese |

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

| 174 | `test_el_destino_manda_sobre_el_origen_si_el_destino_se_puede_leer` | **CIERRE DE PASO 4, SUPERVIVIENTE 1, Y EL UNICO QUE TOCA DATOS DEL USUARIO.** Mata a `REVERSION_ANTES_DE_MIRAR_EL_DESTINO`. El destino es donde el usuario guarda desde la 1.1.0 y el origen es una foto de la 1.0.0: si el origen llegara a pisar al destino, el usuario veria sus packs VIEJOS, daria por perdidos los nuevos **sin aviso** y el primer `save()` escribiria los viejos encima. **MEDIDO: en los 173 anteriores ningun test tenia a la vez un destino VALIDO y un origen con datos**, que es la unica combinacion en la que la precedencia se ve, y por eso el mutante pasaba la suite entera. TRES filas: (1) destino valido + origen valido gana el destino y no se escribe nada (`sha256` del origen y del destino, y `mtime` del destino); (2) destino valido + origen CORRUPTO gana el destino y la corrupcion del ORIGEN no se le atribuye al usuario (`fichero_danado is False`); (3) CONTRAPRUEBA, destino corrupto + origen valido gana el ORIGEN, porque sin ella "el destino manda" seria un test que prohibe la reversion |
| 175 | `test_un_data_path_inyectado_no_busca_la_ruta_antigua` | **CIERRE DE PASO 4, SUPERVIVIENTE 2. Mata a `GUARDA_CANDIDATOS_DESACTIVADA`, y es el guardian de una guarda de PRODUCCION.** Lo que se afirma es semantica de peticion: un `data_path` inyectado es "este fichero y ninguno mas". Sin `_candidatos_para`, el servicio arrastra la busqueda y se trae un fichero que nadie le pidio: MEDIDO en este host, `src/woptimizer/profiles.json` EXISTE, `_hay_packs_legibles` da `True` y trae los packs `7559c83a` y `gaming` de quien desarrolla en esta maquina. Aserciones de CONTENIDO: `candidatos == []`, el destino NO se crea, el origen conserva su `sha256` y el directorio solo contiene el `profiles.json`. CONTRAPRUEBA: con el destino REAL (`PROFILES_FILE`) la busqueda tiene que seguir viva, porque una guarda que apagara siempre pasaria el test entero. **Cierra ademas dos afirmaciones falsas:** el docstring de la guarda decia "ocho tests que afirman que load() no escribe" (cuenta que no se reproduce) y se midi que quitarla deja la suite en verde (tampoco se reproduce: sin ella muere el bloque de instalacion limpia de `test_load_no_escribe`) |
| 176 | `test_la_migracion_conserva_el_mtime_del_origen` | **CIERRE DE PASO 4, SUPERVIVIENTE 3. Mata a `COPY_NO_COPY2` (`copy2` -> `copy`).** `copy` copia el contenido y no los metadatos, luego el `profiles.json` del usuario llega al destino con la HORA DE LA COPIA: no se ve, no da error, y por eso es peor que una migracion rota, porque la base nueva parece correcta y es mas nueva de lo que deberia. Aqui la consecuencia se paga en la rotacion del `.bak`, que decide a partir de la marca de tiempo. La asercion mira el `st_mtime_ns` con un VALOR FIJO puesto con `os.utime` a una hora del pasado, de modo que "no se ha copiado" y "se ha copiado mal" son dos resultados distinguibles y no dos finales de prueba |
| 177 | `test_la_degradacion_a_la_ruta_del_ejecutable_se_avisa` | **CIERRE DE PASO 4, SUPERVIVIENTE 4. Mata a `DEGRADA_AL_EXE_SIN_AVISO`, que se sobrevivia porque la rama del `logger.warning` no la miraba NADIE.** Sin `%APPDATA%`, sin `%LOCALAPPDATA%` y sin override, `data_dir()` cae a `_app_dir()`, o sea devuelve los packs a la ruta atada al binario que T-2 vino a quitar. Se borran las tres variables del entorno (y se restauran en el `finally`) y se captura el REGISTRO: la asercion no es "ha habido un warning" sino que el aviso diga **las dos cosas accionables**, la variable que se ha buscado y la ruta a la que se ha caido con su valor real. Un aviso generico deja al usuario sin poder arreglarlo. **LIMITE DECLARADO:** es aviso de log y no estado de servicio, porque alcanzarlo exige un perfil de Windows sin las dos variables |
| 178 | `test_la_ruta_que_anuncia_el_diagnostico_existe_de_verdad` | **CIERRE DE PASO 4, SUPERVIVIENTE 5. Mata a `T1_AVISA_RUTA_EQUIVOCADA` y a `LOG_NOMBRA_RUTA_EQUIVOCADA`, que solo se habia medido en subconjunto y aqui se vuelve a medir en la suite completa.** Defecto REAL en HEAD: la fila de T-1 concatenaba el directorio con el nombre del fichero SIN separador y decia `...\legacyprofiles.json`, una ruta que NO EXISTE, y eso no se ve porque la asercion anterior leia el log ENTERO y la fila hermana de `_migrar_desde()` nombraba el mismo fichero bien escrito: **cinco tests pasaban con la fila de diagnostico rota**. Un aviso que manda a una ruta que no lleva a ninguna parte es PEOR que no avisar. El filtro es por `funcName` para que la asercion la satisfaga LA FILA, y el contenido se afirma en dos niveles: la ruta exacta (`os.path.join(legacy, "profiles.json")`) y que esa ruta **exista**. CONTRAPRUEBA: la ruta de la concatenacion NO existe, luego la comprobacion de existencia discrimina de verdad. El patron de extraccion no puede cortar en el punto de `".json"`: MEDIDO, `[^\s.;]+` partia el path en `profiles` y miraba un fichero imposible |
| 179 | `test_el_log_de_t1_nombra_el_destino_y_el_candidato` | **CIERRE DE PASO 4, SUPERVIVIENTE 6. Mata a `LOG_MUDA` (bajar la fila de T-1 a un aviso generico).** El criterio de T-1 es que el log nombre al CANDIDATO con su ruta absoluta, y ese criterio no tenia guardian: MEDIDO, bajar la fila a "Hay packs en otra carpeta" pasa los 173 porque ninguna asercion exigia que la fila dijera el QUE y el DONDE. Las dos rutas en la MISMA fila de la MISMA funcion, y por eso el filtro es por `funcName`: con la fila bajada, `_migrar_desde()` sigue nombrando el origen y un test que leyera el log entero pasaria en verde |
| 180 | `test_el_gaming_repuesto_a_ciegas_no_es_silencioso` | **CIERRE DE PASO 4, y el que NO nace de un mutante: es el fallo MEDIDO que la guarda de `_candidatos_para` estaba causando, y es el precio de dejarla puesta.** Con un `data_path` inyectado —destino que no es el de la app, con la busqueda apagada por construccion— el servicio llegaba a `_ensure_gaming_pack()`, reponia el Gaming de FABRICA con 5 categorias y 2 keepers, y `mensaje_danado()` devolvia `None`. Cero diagnostico para un Gaming de fabrica que el usuario no eligio, que es el mismo fallo de seguridad que la lista anti-brick desaparecida en silencio. Y NO se resuelve avisando siempre: la CONTRAPRUEBA del final exige que en la instalacion limpia, con la busqueda ENCENDIDA y sin nada que encontrar, `mensaje_danado()` siga siendo `None`, que es lo que mata al mutante `SIEMPRE_AVISAR` |
| 181 | `test_los_nombres_del_servicio_son_los_de_config` | **CIERRE DE PASO 4, SUPERVIVIENTE 7 (el del `importlib`).** Mata a la reintroduccion de una COPIA local de la decision o de un envoltorio propio alrededor de ella. El comentario que este test viene a sustituir afirmaba que la forma `from woptimizer.config import (a, b, c, d, e)` FALLA en este interprete con `services/pack_service.py` presente, y lo sostenia con una medicion: MEDIDO de nuevo, **no se reproduce** (CPython 3.13.8), y la linea 9 del mismo fichero —25 lineas por encima de aquel comentario— ya usaba ESA forma con tres nombres y nunca fallo. El `importlib` se ha ido porque era un rodeo para un bug inexistente, y no porque fuera incorrecto: ligaba el MISMO objeto funcion. Y lo que este test ata es la IDENTIDAD, que es lo que de verdad importa: el servicio usa la MISMA funcion que el contrato, no una copia suya, porque dos copias pueden discrepar sobre que ruta manda y esa discrepancia no se ve hasta que alguien pierde packs |
| 182 | `test_el_contrato_de_persistencia_se_declara_como_contrato` | **CIERRE DE PASO 4, SUPERVIVIENTES 8 y 9 (los dos documentales).** Mata a `DOC_AMILLA_MIENTRAS_DICE_APPDATA` y a `DOC_APPDATA_EN_ARCHITECTURA_SOLO`. El guard anterior era POR SUBCADENA y por eso no mordia: quitar la unica mencion de `%APPDATA%` mataba, pero reescribir la frase del contrato a "junto al ejecutable" y dejar una mencion decorativa mas abajo pasaba los 173. **El mutante PASA POR EL GUARD:** se escribe el documento mutado a `%TEMP%`, se LEE DE NUEVO y se le pasa al MISMO predicado que usa `validate_docs.py`, y se exige que lo acuse —una contraprueba que muta una cadena en memoria y comprueba que el reemplazo funciono NUNCA pasa el guard, y en ese hueco cabe un predicado que devuelve siempre `[]`—. El predicado es de CONTENIDO: exige que la ruta `%APPDATA%\woptimizer\profiles.json` Y la negacion de "junto al ejecutable" esten en la MISMA unidad de texto (vinneta con sus lineas de continuacion), con lo que se cae a la vez la mencion decorativa y la frase reescrita. Los dos mutadores se escriben a disco con su pre-vuelo: el 1 quita la ruta y ANADE la decoracion, el 2 conserva la ruta y quita la negacion |
| 183 | `test_el_check_del_contrato_usa_el_mismo_predicado_que_el_test` | **CIERRE DE PASO 4, y el que evita que los dos anteriores sean decorativos.** MEDIDO: hasta el cierre el guard vivia SOLO en `run_tests.py` y `validate_docs.py` no tenia ninguno de TASK-069, o sea que un documento reescrito se sostenia en verde mientras la suite corriera y caia en rojo cuando no: al reves de como funciona una guarda. La atadura se afirma por TEXTO con `inspect.getsource` —del predicado en `validar()`, que es donde vive el cableado, y de los DOS nombres de documento en la funcion DELEGADA, porque `validar()` solo cablea (D1) y buscar los nombres ahi seria exigirle logica que este repo se prohibe a proposito— y con un control de que un documento vacio no puede declarar el contrato |
| 184 | `test_la_rotacion_no_macha_el_bak_que_guarda_lo_unico` | **RONDA 2 DEL PASO 4, HALLAZGO 1, Y EL QUE TOCA DATOS DEL USUARIO.** MEDIDO: con el destino inexistente, un `.bak` previo del dueno con el pack `viejo01` y un origen con 3 packs, tras la carga el `.bak` seguia intacto y **tras el `save()` el `.bak` paso a ser copia del origen, byte a byte (sha identica), y `viejo01` desaparecio**. La rotacion es un anillo de UNA plaza y la migracion mete una TERCERA generacion en un anillo de dos: el recycled se come a la copia buena del dueno, que es lo UNICO que el usuario tiene si el destino se corrompe. Las cuatro filas: `viejo01` sigue **LEGIBLE** (no "existe": con un mutante que BORRA en vez de pisar, `os.path.exists` pasaria por la razon equivocada), el rescate contiene el contenido del `.bak` viejo y no una mezcla, **el `.bak` ANDA** (un fix de "no se rota nunca" dejaria al usuario sin red anti-brick para siempre) y el mensaje nombra el fichero. Y la CONTRAPRUEBA: con un `.bak` que no guarda nada unico no se crea fichero de rescate, que es lo que mata al mutante "apunta un fichero por cada guardado" |
| 185 | `test_el_gaming_repuesto_se_declara_tambien_si_el_origen_esta_corrupto` | **RONDA 2 DEL PASO 4, HALLAZGO 2. El mismo punto ciego de T-4 por otra puerta.** MEDIDO: con el destino ILEGIBLE **y el ORIGEN ALSO ilegible**, `gaming_repuesto` sale True con 5 categorias y los keepers steam/discord, el mensaje nombra la corrupcion y **no** la reposicion, y el `save()` siguiente deja el fichero del usuario con `["gaming"]`. El mutante que mata la rama de mensaje de T-4 quita el `extra` de OTRA rama y por eso sobrevive: es la clase de S7 de TASK-066, la regla escrita en un sitio y sin ejecutar en el otro. Tres filas: el motivo declarado aparece en el mensaje, la corrupcion **sigue** apareciendo (declarar mas no es tapar lo de antes) y cargar no escribe ni el destino ni el origen |
| 186 | `test_el_diagnostico_pasa_por_el_punto_unico_de_decision` | **RONDA 2 DEL PASO 4, HALLAZGO 3 (M4). Un hallazgo que no nace de un mutante construido sino de uno MEDIDO por el auditor.** `elegir_ruta_de_datos()` es el punto unico donde viven la regla de instalacion limpia y la decision de ruta de T-1/T-2, y `_diagnosticar_y_migrar()` tiene que pasar por ahi. MEDIDO: el mutante `M4_COPIA_LOCAL` lo envuelve con su propia copia y devuelve `(destino_, [])` cuando el destino es legible; la suite completa pasa en VERDE y con eso cualquier cambio futuro de la decision deja de llegar a la migracion sin que nadie lo note. Por que `ast` y no texto: el nombre tambien esta en el DOCSTRING del metodo, luego `inspect.getsource` + `in` lo daria por bueno y un comentario no ejecuta nada. Y la segunda fila mata el mutante por el otro lado:`_copia_local` no puede existir en esa funcion |
| 187 | `test_el_destino_que_gana_tiene_que_decir_que_hay_packs_que_no_vienen` | **RONDA 2 DEL PASO 4, HALLAZGOS 4 y 5. La PRECEDENCIA es correcta y esta escrita; lo que no estaba escrita era su CONSECUENCIA.** MEDIDO: (a) destino legible y VACIO con 3 packs en el origen -> gana el destino, no se copia nada, `migrado_desde` y `packs_en_otra_ruta` vacios, y el mensaje era el del Gaming: los 3 packs heredados no vuelven y NADIE LO DIJE; (b) destino con 1 pack contra 3 del origen -> gana IGUAL, la precedencia es ESTRICTA y el numero de packs NO entra, y antes no lo decia ni el log. El servicio NO fusiona ni copia: la precedencia es un contrato cerrado y lo que se anade es la DECLARACION. Tres filas: la precedencia se respeta y el origen queda intacto, el mensaje nombra la ruta **y cuantos packs y cuales** (un aviso que dijera "hay packs en otra ruta" sin decir cuales seria el mismo silencio con prosa), y la CONTRAPRUEBA de que con el destino teniendo todos los ids del origen `mensaje_danado()` es `None` |
| 188 | `test_la_puerta_de_arranque_no_tiene_literal_propio_ni_omision_sin_contar` | **TASK-068, T-3 (guard de contrato) y T-2 (invariante del `continue`), y el ladrillo del ciclo.** La premisa del encargo -«el boton Iniciar ignora `start_categories`»- era un MUTANTE que sobrevivia a la suite entera, porque el doble de la puerta declaraba `llamadas_categorias` y `arranque_categorias` y NINGUN test los leia (2, 2 y 2 ocurrencias, las tres de definicion o incremento), y `pack_normal` no tenia `start_categories`, luego el `if categorias:` no se tomaba nunca: **borrar el bloque entero de la suma dejaba los 183 en verde** —esa cifra era la de ENTONCES, y sin registrar que ya no es verdad el renglón se lee como una promesa viva—. **Medido el 2026-10-05, ese mismo borrado MUERE por asercion**: en la **fila 1** del ladrillo, *"la puerta de arranque tiene que ejecutar SUS DOS listas: el pack marcaba 1 categoria(s) y el doble recibio 0 llamada(s) a start_pack_categories…"* (`run_tests.py:10124`), log de 16 904 B cerrado en `AssertionError`. Dos mitades, cada una con su contraprueba sintetica porque un guard sin un arbol que deba rechazar se lee igual que un guard que mide: (a) **ninguna de las dos vistas puede escribir su literal del recuento**, exigido sobre `_codigo_ejecutable` (sin comentarios ni docstrings) para que un texto que explica la regla no pueda hacerse pasar por codigo, y exigiendo que las dos LLAMEN a `mensaje_arranque_pack` / `mensaje_banner_arranque`; (b) **todo `continue` del bucle de categorias de `start_pack_categories` tiene que estar precedido por un `failed += 1` en su propia rama**, lo que mata al `continue` pelado de HOY y tambien al cuarto que alguien anada manana: es la clase «un camino nuevo sin guardian». |
| 189 | `test_la_clausula_de_arranque_lista_todas_las_categorias_y_va_en_singular` | **TASK-068, ronda 2 del Paso 4: mata los DOS supervivientes REALES de la ronda anterior.** Medidos con 28 046 B de log y `ALL TESTS PASSED` con los 188 en verde: `N6_CLAUSULA_SOLO_NOMBRA_LA_PRIMERA` (`', '.join(cats)` -> `', '.join(cats[:1])` en `ui/feedback.py::clausula_categorias_arranque`) hacia que con `start_categories` de dos elementos el mensaje dijera *"(2 categorías: A)"* —cuenta dos y enseña uno— y `N7_CLAUSULA_PLURAL_ROTO` (`plural = "s" if n != 1 else ""` -> `"s"`) imprimía *"(1 categorías: …)"* con una sola. **La causa era una sola y no eran dos ausencias:** ninguno de los 188 montaba un pack con `start_categories` de DOS elementos, luego el recuento, el plural y el listado completo de la clausula estaban sin vigilar; las filas previas miran una sola categoria (`_CAT_ROJO` en T-2, `CATEG_INICIO` en T-3), y con una el `cats[:1]` es la lista entera y el plural correcto es el de una. **Tres filas sobre el mismo par de categorias (2, 1 y 0 omitidas), y el recuento lo pide el MOTOR:** las tres entran por `PackManagerView.start_pack` de verdad y `start_pack_categories` lo delega en `_ServicioDeArranque` con sus barreras y sus ramas de omision, asi que "las dos omitidas" es un hecho de T-2 y no un `(0, 2)` puesto a mano. (a) **dos omitidas**: el toast nombra **las dos** y dice `"(2 categorías:"`; (b) **una omitida**, que es la contraprueba y mata el plural, exige `"(1 categoría: "` y que la otra no aparezca; (c) **control negativo** sobre el MISMO pack de dos, donde lo contribution es 0 y el texto tiene que salir byte a byte el de exito, sin clausula. Sin (c), una clausula metida en la rama de exito pasaria las dos anteriores, porque solo probarian que no sale con UNA. **TESTIGOS, escritos aqui porque el parte del ciclo nombro el equivocado en tres muertes** (ninguna cambia un veredicto; lo que cambia es que un informe con el testigo mal se reaudita mal tres ciclos despues): `T1_TRASPASA` muere en la fila 3 del ladrillo, *"la lista de APAGADO viaja"* (`procs.target_categories == …`), no en la fila 2; el compuesto de la clausula muere en la fila 4, *"el texto dice la SUMA de los dos recuentos"* (`5 iniciadas, 1 con error`), no en su contraprueba; y `N2` lo mata la fila T-2, *"la omision tiene que CONTAR como fallo"*, no la fila 1 ampliada. Se nombran por fila y no por linea porque las lineas se mueven con cada insercion. |
| 190 | `test_el_reparto_de_tests_no_re_tokeniza_por_sentencia` | **TASK-070 T1: el reparto se deriva SIN re-partir `run_tests.py` por sentencia.** MEDIDO el 2026-10-06: `run_tests.py` pesa 1 246 407 B y su `__main__` tiene 196 sentencias; `ast.get_source_segment` se llamaba UNA vez por sentencia, y cada llamada parte las lineas del fichero ENTERO. **La premisa de la tarea decia que eso es `tokenize` y era FALSA**: en Python 3.13 `get_source_segment` usa `_splitlines_no_ff`, asi que `tokenize.generate_tokens` cuenta 0 HOY. El O(n^2) en el tamano del fichero si era real, que es lo que importa. Este test cuenta INVOCACIONES REALES con monkeypatch sobre las dos puertas (`ast.get_source_segment` y `tokenize.generate_tokens`, restauradas en `finally`: un `ast` envenenado rompe el resto de la suite, y aqui el resto de la suite es justo lo que mide) y exige **0**. **Sin temporizador, a proposito**: un conteo es exacto y un reloj se rompe en una CI mas lenta. Verde sin el arreglo no puede ser: antes contaba **196**, una por sentencia. Va **DELANTE** del marcador headless (posicion de registro 141) por un motivo MEDIDO, no de gusto: vigila la funcion que **deriva este reparto**, y detras del marcador su propia asercion se mediria contra un reparto que ya no existe. |
| 191 | `test_el_split_derivado_no_cambia_con_el_arreglo` | **TASK-070 T2: el reparto NO se mueve con el arreglo. Este es el que mata al arreglo EQUIVOCADO, no al fallo original.** Compara el **4-tuple** `(antes, desde, total, linea_marcador)` de `_reparto_de_tests` contra una implementacion de REFERENCIA que vive aqui (`_reparto_de_tests_via_source_segment`: el mismo bucle con `get_source_segment`, ~6 s, **solo de test** y nunca importada por `validate_docs.py`), sobre el **`run_tests.py` REAL**. Las CUATRO componentes y no el total porque **un reparto movido conserva la suma por construccion** (es sumar lo mismo en dos botes distintos): el mutante M1 `visto = MARCADOR_HEADLESS in fuente` devuelve `antes = 0` y `desde = <el total entero>` —toda la suite por delante del marcador— y **el total sigue cuadrando**, asi que un check que mire la suma no lo ve. Y por eso la comparacion va contra el fichero REAL y no contra un sintetico: un fixture no tiene `_run_tests_sintetico`, luego tiene **una** sola ocurrencia del marcador, y con una sola el mutante M1 pasaria todos los sinteticos. La tercera asercion (`>= 2` ocurrencias) es la que **sostiene la potencia del test**: si el fichero real se quedara con una, las dos implementaciones seguirian de acuerdo y este test dejaria de discriminar sin que nadie lo notase. **MATA** M1 (busqueda fuera del bucle), M2 (slice `lineas[lineno:end_lineno]`, que aqui devuelve `None` porque la sentencia del marcador es de una sola linea) y M4 (`break` despues de `visto`, que trunca `desde`). **NO mata M5** (slice una linea mas ancha): con 0 solapamientos y 0 punto y coma entre sentencias de `__main__` es indistinguible del correcto hoy, y se documenta como **superviviente**, no como cobertura. |
| 192 | `test_el_envoltorio_git_no_hereda_stdin_y_no_cuelga_en_desatendido` | **TASK-072 AC-2': el ENVOLTORIO REAL de git, con un padre desatendido de verdad.** Es el unico test de esta tabla que mata el defecto de `_git_de_fixture` (`run_tests.py:12745`), que corria `subprocess.run` SIN `stdin=` en sus **37** llamadas. **Por que el hijo y no una replica:** si el test copiara la llamada, mutar el envoltorio no lo tocaria y seria otro decorativo, que es el fallo que este ciclo vino a matar; el hijo hace `import run_tests` y llama a `_git_de_fixture` de verdad. **Por que un `os.pipe()` que el padre no escribe ni NO cierra:** con un `stdin` heredado que es una TTY —que es lo que este host le regala hoy— el bug NO se manifiesta, luego un test que dependa de esa casualidad no discrimina nada. MEDIDO el 2026-10-08: TTY heredada 140 ms y `DEVNULL` 141 ms, frente a **pipe abierto que no vuelve**. El hijo hace **DOS** comandos, `rev-parse --short HEAD` (NO lee stdin) y `cat-file --batch-check` (SI lo lee), y el assert exige que **ambos** volten: sin el segundo, un arreglo que pase `stdin` solo en un camino seguiria verde. **El timeout del padre es 60 s, NO los 10 s de la propuesta, y es una CORRECCION MEDIDA:** tres corridas del camino bueno dieron 8 896 / 6 850 / 1 704 ms, de las que solo 330-451 ms son las dos llamadas de git —lo que domina es el `import run_tests` (7 468 / 5 768 / 661 ms), porque el hijo carga CustomTkinter y pydantic—. Con 10 s este test daria un rojo POR LENTITUD en la primera pasada, que es el falso rojo que este repo ya pago en TASK-069. **Y el padre mata a mano al hijo en el `except`**, porque MEDIDO: `subprocess.run(timeout=...)` **NO acota** este cuelgue en este host (con `timeout=6` no habia revuelto a los 90 s); fiarse de el para limpiar dejaria un hijo vivo con el pipe abierto arrastrando al resto de la suite. Va **DETRAS** del marcador (git en `%TEMP%` + subproceso, ninguna ventana). **MATA** M1 (quitar `stdin=DEVNULL`). |
| 193 | `test_el_pre_vuelo_de_un_hash_muerto_distingue_existe_de_no_existe` | **TASK-072 AC-3: mata al `pre_vuelo` TAUTOLOGICO.** Los dos `pre_vuelo` de existencia que tenia el check 9 (`run_tests.py:20186` y `:20303`) usaban `git cat-file --batch-check`, que **lee los nombres por stdin**, sin pasarle `input=`. MEDIDO el 2026-10-08: rc 0 con stdout **VACIO** (`140 ms`), luego `HASH not in ''` era `True` para CUALQUIER hash: **no podian fallar**. Y el texto de sus aserciones ("existe de verdad") afirmaba lo contrario de lo que la operacion (`not in`) demostraba. El arreglo es el helper `_objeto_existe_en_fixture`, que decide por **ARGUMENTO** con `git cat-file -e <hash>` y **NO puede usar `_git_de_fixture`**: aquel responde `AssertionError` ante cualquier rc != 0 y `cat-file -e` responde **128** para un hash que sencillamente no existe, que es justo la respuesta legitima que el pre-vuelo quiere leer. MEDIDO: `<existe>` rc 0 en 177 ms, `<muerto>` rc **128** en 145 ms con `fatal: Not a valid object name`. Este test exige **LAS DOS** respuestas sobre la misma fixture —`HASH_REAL is True` y `HASH_MUERTO is False`— y el caso POSITIVO es lo que discrimina: sin el, un helper que devolviera `False` siempre pasaria el caso negativo, y uno que devolviera `True` siempre pasaria el positivo; con los dos, solo pasa el que responde a git de verdad. La tercera asercion (`HASH_REAL + "0" is False`) ata el **128** al `False` y no a un `AssertionError`. Va DETRAS del marcador. **MATA** M2 (`cat-file -e` -> `--batch-check` sin `input=`) y M3 (helper que devuelve `False` siempre). |
| 194 | `test_ninguna_llamada_de_cat_file_batch_check_se_queda_sin_input` | **TASK-072 AC-4: guard estructural sobre el `run_tests.py` REAL, con `ast` y no contando texto.** Exige **cero** llamadas que pasen `cat-file --batch-check` **sin** el keyword `input=`. Un `in` sobre el fuente daria el mismo veredicto con la lista partida en dos lineas, que es justo como volveria. **Ronda 2 de CYCLE-060 (VERDICT FAIL del `mutation-auditor` con 11 supervivientes): el guard de esta fila estaba ESCRITO pero no podia ver lo que vigila, y su contraprueba no lo ejercitaba.** MEDIDO por el auditor sobre la copia exacta de la deteccion: exigia `isinstance(argumento, ast.List)` y con eso veia **2 de las 7** formas de escribir la llamada prohibida (la lista, y la lista con `git` delante); `_tiene_input(fragmento)` —la contraprueba anterior— comprobaba que `ast` ve un keyword `input`, no que la deteccion funcione, asi que **`for argumento in []` dejaba la suite en verde**. **Arreglo:** `_argv_de_un_argumento` RESUELVE el argumento a sus tokens (lista, tupla, concatenacion de constantes, `["git"] + [...]`, variable enlazada y la cadena con `shell=True`) y `_llamadas_cat_file_batch_check` decide sobre eso. **Y la contraprueba ahora llama a la DETECCION REAL** sobre **diez** fragmentos y exige las **dos mitades** de cada uno (que la vea, y que el veredicto de `input=` sea el que corresponde), con un **control negativo** (`cat-file -e` NO puede salir) porque un guard que ve todo es una alarma que siempre suena. MEDIDO el 2026-10-08 sobre el fixture real: un nombre se resuelve por el **ultimo enlace anterior al uso**, no por "la ultima asignacion que aparezca al recorrer" —un `ast.walk` es un recorrido en ANCHURA y el `args = nodo.args` de la linea 7873 tapaba la lista de al lado de la llamada; sin esa regla, D4r seguia vivo y la contraprueba nueva lo caza sola. **Limite DECLARADO** (para que un limite no se lea como cobertura): ve la primitive cuando se pasa como ARGUMENTO o como cadena con `shell=True`; NO ve el fuente de un proceso hijo escrito con `fh.write(...)`, que es un PROGRAMA y no una invocacion. Va DETRAS del marcador. **MATA** M4, D1r-D7r y D6. |
| 195 | `test_el_helper_de_existencia_revienta_un_rc_indefinido_tras_tres_intentos` | **TASK-072 ronda 2 (S1 del auditor, mutantes B5, B7, A3 y B6): la rama de git-roto era FAIL-OPEN y no la ejecutaba nadie.** `_objeto_existe_en_fixture` decide existencia por el rc de `cat-file -e`: 0 existe, 128 no existe, **cualquier otro rc no es una respuesta sobre el objeto sino un fallo de git**. Con `return False` en esa rama, un git roto se traducía a "el objeto no existe": el falso verde exacto, en la unica rama sin test. Y el agravante esta MEDIDO en este repo (`validate_docs.py:490-493`): un directorio vacio que no es repositorio **tambien devuelve 128**, luego la disyuntiva solo es correcta si git esta vivo. **Como se fuerza:** sustituyendo `subprocess.run` en el modulo durante la llamada y restaurandolo en `finally` — inyeccion y no copia del helper, porque una replica no la tocaria al mutar. **Lo que mide:** (1) un rc fuera de {0,128} **revienta** y con el `stderr` LITERAL en el mensaje, porque sin diagnostico no se distingue "repo vacio" de "git roto" (mata B5); (2) **exactamente TRES** llamadas (mata B7: con `for _intento in (1,)` hay 1, y el `spawn EPERM` transitorio de este host —el motivo DECLARADO del reintento— se come la respuesta); (3) `stdin=DEVNULL` en las tres (mata A3, que era inocuo solo porque `cat-file -e` no lee stdin); (4) el argv `['git','cat-file','-e',hash]` (mata B6, con el que la eleccion de primitive queda verificada y no solo afirmada); (5) **dos rc no-cero y uno bueno DEVUELVEN la respuesta correcta** en vez de reventar, y el 128 legitimo tras dos fallos da `False` y no excepcion. Va DETRAS del marcador (git en `%TEMP%`; `subprocess.run` inyectado). |
| 196 | `test_el_envoltorio_de_git_reintenta_tres_veces_un_fallo_transitorio` | **TASK-072 ronda 2 (S4 del auditor, mutante A2): "tres intentos" no lo verificaba nadie, en NINGUNO de los dos envoltorios.** Con `for _intento in (1,)`, todo seguia en verde, y AC-1 ("son 3 llamadas y las 3 heredan") solo se comprobaba leyendo el codigo. Inyecta dos rc no-cero seguidos y uno bueno, y exige que la llamada **DEVUELVA la correcta** —no que reviente—: un reintento que solo se demuestra con el fallo no demuestra que reintenta. Comprueba ademas el numero real de llamadas (**tres**), que el argv es el mismo comando las tres veces con `git` delante, y que **las tres pasan `stdin=DEVNULL`**, con lo que AC-1 pasa de "se lee en el codigo" a "esta medido". La segunda mitad exige que tres fallos seguidos **reventen con el `stderr` literal**. Misma tecnica que la fila 195 (`subprocess.run` inyectado y restaurado en `finally`). Va DETRAS del marcador. |
| 197 | `test_el_check_9_conserva_su_pre_vuelo_de_existencia` | **TASK-072 ronda 2 (C2r del auditor): el pre-vuelo del check 9 se podia BORRAR ENTERO y la suite seguia en verde** (medido, con el subconjunto lento: 268,5 s de las cuatro llamadas a `validar()`). Nada vigilaba que siguiera ahi. El caso positivo que se anadio al lado delataria una fixture rota, pero **la asercion del pre-vuelo en si no estaba vigilada**, y esa es la que dice "la fixture distingue el hash muerto del real" antes de que el check mida nada. **Mira la POSICION y no el recuento**, y por eso: el caso negativo del bucle de `MUERTOS` (mas abajo en la misma funcion) tambien es un `is False` sobre el helper, luego contar no lo distinguiria del pre-vuelo. Lo que le da el nombre es ejecutarse **ANTES del primer `asentar()`**: si no, el check 9 ya ha validado contra una fixture que nadie ha comprobado. Se exigen las **dos mitades** en esa zona (el `is False` del hash muerto y el `is True` del real): con una sola, o un helper que devuelve `False` siempre o uno que devuelve `True` siempre pasarian el otro caso. Test de `ast` puro sobre `run_tests.py`: ~2,4 s, sin git, sin disco y sin ventana, DETRAS del marcador. |
| 198 | `test_el_wrapper_no_versiona_desde_un_cwd_ajeno_ni_un_arbol_ajeno` | **TASK-072 ronda 3: LAS DOS ALARMAS DE UBICACION del wrapper, con dos controles.** MEDIDO: tres veces en la historia de este repo un subagente ha escrito un commit en el HISTORIAL REAL con un arbol que no era el suyo (ciclo 56/TASK-069 y dos veces el 2026-10-08, la ultima `a5de331`, confeso y revertido por el propio auditor). No lo causo el agente: lo causo `.taskmaster/git_safe_commit.py`, que es la puerta que existe para que nadie versione sin ancla. MEDIDA la causa, cuatro lineas suyas: `REPO_ROOT` se deriva de `__file__` pero `LOCAL_GIT_DIR` es una CONSTANTE ABSOLUTA (`%LOCALAPPDATA%\woptimizer_git\.git`), luego no admite hermeticidad: invocado desde una copia en `%TEMP%` escribe en el repo real con el arbol de la camara, y su propio `--verify` lo certifica con `WOPT_REPO_OK`. **Por eso hay DOS alarmas y no una, y la del cwd sola NO cerraba el caso medido**: en `a5de331` el cwd estaba DENTRO del arbol de la camara. (A) `cwd` fuera de la raiz -> 2 `WOPT_USAGE cwd-fuera-de-raiz`, con `--allow-cwd-externo` como salida que suena en el log; (B) repositorio y arbol que no se corresponden -> 3 `WOPT_REPO_INVALIDO`, sin salida: el repo declara cual es su arbol (`core.worktree` o un remoto que sea una ruta local existente, MEDIDO en el repo real de este proyecto) y lo que se versiona tiene que ser ese. **Los dos controles son la mitad que hace que esto sea una prueba y no un adorno**: desde la raiz con el par entero el wrapper tiene que COMITEAR DE VERDAD (0, `WOPT_COMMIT_OK`, el HEAD de la sonda movido y el fichero dentro del commit) y, cuando el arbol SI es el declarado, tambien; sin ellos, un wrapper que siempre saliera con 2 pasaria el test entero y el bucle se quedaria sin poder versionar. **Hermetico por construccion**: las cuatro invocaciones llevan `GIT_DIR` y `GIT_WORK_TREE` temporales, luego **ninguna puede escribir en el repo real ni aunque el test este mutado**; por eso la sonda NO reproduce `a5de331` con el `GIT_DIR` real (seria pedirle al test que pueda contaminar el historial para comprobar que no lo contamina) sino con la misma clase de incoherencia sobre un repo desechable, y el testigo es `_head_del_repo_real()`. Mata el mutante que borra la alarma del cwd (A daria 0 y commitearia) y el que borra la del par (C daria 0 y commitearia el arbol equivocado). Va DETRAS del marcador: cuatro subprocesos del wrapper y git en `%TEMP%`, sin ventana. |
| 199 | `test_pack_model_is_protected_strict_bool` | **TASK-071: modelo Pack y coherencia booleana estricta.** Verifica que `Pack.is_protected` tiene valor por defecto `False`, acepta `True` explícito y rechaza cualquier coerción laxa (`"true"`, `"1"`, `1`, etc.) lanzando `ValidationError` por `strict=True`. |
| 200 | `test_pack_service_ensures_default_protected_pack_and_cannot_delete` | **TASK-071: ciclo de vida de PackService e inmutabilidad del pack protegido.** Verifica que `PackService` asegura `DEFAULT_PROTECTED_PACK` (`id="protected_apps"`, `is_protected=True`) en memoria ante instalaciones limpias o json sin pack protegido, normaliza `get_protected_apps()`, prohíbe el borrado de `protected_apps` con `ValueError`, y lo excluye de `get_user_packs()` y colisiones de creación. |
| 201 | `test_protected_apps_survive_kill_processes_and_gaming_pack` | **TASK-071: supervivencia de apps protegidas en el backend de terminación.** Verifica que los procesos en `get_protected_apps()` son ignorados en `ProcessService.kill_processes` (incrementando `skipped` y sin matarlos), que `GamingService.execute_pack` no ejecuta el pack protegido retornando `(0, 0, 0, 0.0)`, y que `GamingService._seleccion` suma apps protegidas a los keepers efectivos salvándolas de cualquier categoría destructiva. |
| 202 | `test_process_manager_view_hides_protected_apps_and_dropdown` | **TASK-071: invisibilidad de aplicaciones protegidas en ProcessManagerView.** Verifica que los procesos en `protected_apps` son filtrados en `_render_list()` (no generan checkboxes ni filas en la tabla visual de procesos) y que el pack protegido no aparece en el desplegable de asignación a packs. |
| 203 | `test_pack_manager_view_and_dashboard_protected_pack_ui_contracts` | **TASK-071: contratos de interfaz en PackManagerView y DashboardView.** Verifica que la tarjeta del pack protegido se renderiza adecuadamente sin botones de inicio ni de borrado, y que `DashboardView` excluye el pack protegido de los botones de ejecución rápida en la portada aunque `is_favorite` esté activado. |
| 204 | `test_publicar_en_el_bucle_no_programa_si_la_vista_ya_murio` | **TASK-073 + TASK-078 (SV1):** publicar en el bucle de Tk desde un hilo secundario sin propagar el `RuntimeError`. El defecto que caza **no es "salta una excepción", es "se la tragó"**: un test que comprueba que no revienta sale **VERDE con el guard quitado**, porque el `except` hace justo eso. Por eso afirma sobre CONTENIDO, con un doble que REGISTRA cada `after`: caso A (la vista murió) exige `handle is None` y convierte la propagación del `RuntimeError` en un `AssertionError` con el defecto escrito —**el `llamadas == []` de este caso mide AL DOBLE, no al guard, y su mensaje lo dice**—; caso B (la vista vive) exige `llamadas == [(0, cb, (1, 2))]` y el handle centinela, y mata al otro extremo —el helper que se traga todo y nunca programa nada, que con A solo pasaría en verde; caso C separa "se intentó y falló" de "no se intentó"; caso D mata el **probe `winfo_exists()`**: lo que mide es que el helper **no lo consulta**, porque si lo hiciera y la consulta fallara se tragaría el acierto y no publicaría nada. *(Corrección TASK-078 de una medición falsa: el `RuntimeError` de una llamada Tcl desde un hilo secundario ocurre en el mundo **sin bucle principal**, no "incluso con la ventana viva"; con `mainloop()` vivo `winfo_exists()` devuelve 1 con la vista viva y 0 con el widget destruido, sin lanzar. El probe sigue sin ser la solución, por tres razones medidas.)*; caso E ata `Confirmable._publicar_en_el_bucle` a la MISMA función con un doble que además **registra de dónde se llamó al `after`** —**TASK-078: con un doble vivo, delegar y reimplementar por su cuenta son indistinguibles, y el mutante A2a pasaba en verde**—, con contraprueba del propio predicado (el mismo doble, llamado directo, no registra la delegación) y con el caso de la vista **muerta** por la misma función pura. El doble es una clase real del test, no una copia de la lógica. **MATA** el `try/except` ausente, el `return None` siempre, el probe de existencia, la delegación reimplementada y la puerta reimplementada a `self.after`. |
| 205 | `test_ninguna_vista_programa_after_a_mano` | **TASK-073 + TASK-078 (SV1 y SV2): la puerta de vuelta, y con CONTRAPRUESTA propia.** `ast` sobre **cuatro** ficheros —las tres vistas de `src/woptimizer/ui/views/` **más `ui/confirmation.py`**, donde vive la puerta—: cero `self.after` a mano (los diez call sites migrados a `self._publicar_en_el_bucle`). Una detección de "cero ocurrencias" **que no observa nada deja la suite verde para siempre**, que es el fallo real de `test_ninguna_llamada_de_cat_file_batch_check_se_queda_sin_input` (TASK-072): la detección existía, no veía, y `for argumento in []` dejaba todo en verde. Así que aquí la misma detección se aplica a tres fragmentos sintéticos y se exige que **separe**: marca `self.after(0, f)`, NO marca `self._publicar_en_el_bucle(0, f)` (control negativo: un guard que marca todo no guardaba nada), y un worker conforme con el resto de llamadas queda limpio. **SV2: además exige que el conjunto vigilado no esté vacío y sea exactamente el declarado** —"cero infracciones sobre cero ficheros" es indistinguible de "cero infracciones de verdad", y con la lista vacía el mutante D1b salía con `ALL TESTS PASSED.`—; la contraprueba del detector no lo tapa, porque probar que el detector detecta no es probar que se le pidan ficheros. **SV1: y comprueba por nombre de método que `Confirmable._publicar_en_el_bucle` no programa por su cuenta**, con contraprueba de que el mismo detector baja a los cuerpos de los métodos. `ui/tk_thread.py` se mira **LEYÉNDOLO** (nunca importándolo: `test_double_tap_guard` prohíbe cualquier `woptimizer.*` en `confirmation.py`). Además vigila la **frontera de capas del fichero nuevo**: `ui/tk_thread.py` no puede importar `psutil`, `json`, `subprocess`, `services`, `models`, `customtkinter` ni `tkinter`. **TASK-078: el mensaje de ese guard escribía `proibido_tk` y el rojo moría por `NameError`**; corregido, ahora muere por `AssertionError` nombrando el infractor. **TASK-079 (R4b): esa frontera de capas comparaba `module.split('.')[0]`, o sea el PRIMER SEGMENTO, así que con la forma de import que escribe este repo (`from woptimizer.services import process_service`) daba `woptimizer`, que no estaba en la lista de prohibidos y dejaba la puerta importando `services` con la suite en verde** —el "killed" que TASK-078 dio al mutante F1b fue FALSO: murió por el `NameError` del typo, no por la aserción—. Ahora compara la RUTA COMPLETA (`modulo.alias` incluido, para `from woptimizer import services`) y prohíbe `woptimizer.services…`, `woptimizer.models…` y las raíces `psutil`, `json`, `subprocess`, `customtkinter`, `tkinter`, `services` y `models`; con **cinco controles sintéticos** sobre las formas que el repo escribe y un control negativo sobre `typing`. El guard gemelo de `confirmation.py` (`run_tests.py:1851`) hace lo mismo pero lleva `woptimizer` en la lista, y eso es intencionado: ese fichero es una máquina de estado sin dependencia ninguna del paquete (importa a su hermano por ruta relativa), así que la red más gruesa es la correcta ahí y **no se toca**. **TASK-079 (R2b): el conjunto que este guard ABRE se deriva del DISCO (`glob` sobre `ui/views/*.py`), no de una lista escrita a mano** —antes el `glob` solo servía para comparar, y borrarlo entero dejaba la suite en verde porque nada dependía de él—; con la derivación, una vista nueva que no esté en `ESPERADOS` hace morir el guard nombrándola, y una derivación vacía hace morir el recuento. **MATA** reintroducir un `self.after` en cualquier vista **o en la puerta**, vaciar el conjunto vigilado, y ensuciar la puerta con una importación de sistema o de JSON. |
| 206 | `test_la_paridad_gana_al_repo_invalido_en_los_dos_modos` | **TASK-074 (AC-4): el `2` de la paridad precede al `3` del repo en LOS DOS MODOS.** Cuatro celdas medidas: `commit` + par roto + repo roto → `2`; `--verify` + par roto + repo roto → `2`; `commit` + par entero + repo roto → `3`; `--verify` + par entero + repo roto → `3`. Las dos primeras son el sujeto y las dos últimas el **control**: sin ellas, un wrapper que devolviera `2` siempre pasaría las dos primeras sin medir nada. Afirma sobre CONTENIDO: la última línea no vacía tiene que empezar por la línea canónica de cada celda y la línea canónica **opuesta** tiene que estar **ausente** (el `2` y el `3` son excluyentes y decir los dos sería un diagnóstico que se contradice). **MATA** el mutante `R4-k` (`if paridad_rota and ok:`), que hunde las dos celdas del par roto a `3`, y el mutante `R4-n` (`if paridad_rota and not verify:`), que mata la columna de `--verify`; juntos demuestran que la sonda mira **las dos columnas de modo**, porque si mirase una sola uno de los dos sobreviviría. Cámara desechable en `%TEMP%` con `GIT_DIR` inexistente y `_head_del_repo_real()` intacto antes y después. |
| 207 | `test_la_puerta_de_paridad_va_despues_de_validar_repo_por_estructura` | **TASK-074 (AC-5): la posición de la puerta de paridad, medida con `ast`.** MEDIDO el 2026-10-18: con el reordenamiento de `main()`, el mutante `M5'` (mover `if paridad_rota:` por encima de `validar_repo`) pasa a ser **EQUIVALENTE** —`validar_repo` no imprime ni escribe, luego ni `stdout` ni el código de salida cambian— y ninguna sonda de comportamiento puede cazarlo. Antes de TASK-074 el mutante `M5` era visible solo de rebote, porque la sonda que se llamaba `...va_despues_de_validar_repo` medía en realidad la posición respecto al `if verify and not ok`, no respecto a `validar_repo`: su nombre y lo que medía no coincidían. Sin subproceso ni escritura: compara tres números de línea del árbol de `main()` (1) la puerta **después** de la asignación `ok, fallo_repo, git_dir = validar_repo(env)`, (2) la puerta **antes** del `if verify and not ok:` —lo que mata también la reversión del arreglo de TASK-074— y (3) que el cuerpo de la puerta diga `paridad-git`, porque una puerta muda con `if paridad_rota: pass` cumpliría el orden sin rechazar nada. **Contraprueba:** si el bloque, el `validar_repo` o el `if verify and not ok:` no aparecen, el test **falla** con el motivo literal; no hay rama que devuelva éxito por no haber encontrado nada (patrón «una comprobación sin contraprueba no es una comprobación», tercera vez en este repo tras los ciclos 60 y 62). |
| 208 | `test_la_resolucion_del_repositorio_tiene_un_solo_punto` | **TASK-075 (AC-1 y AC-3): UN punto de resolución del repositorio, para los DOS consumidores de git.** La derivación estaba **duplicada, con código idéntico**, en `_comprobar_ancla_de_commits` (check 5b) y `_hashes_que_existen` (check 9), y el encargo que pedía desacoplarla citaba la línea 300-302, que no existe. Con la duplicación, un `--git-dir` honrado en uno solo deja al otro con el default: el flag «funciona» y el validador da **154 FAIL** (medido). Dos mitades: **(a) estructural, con `ast`**, ninguno de los dos consumidores puede llamar a `expandvars` y los dos reciben un `Repositorio`, y `validar()` lo resuelve exactamente una vez —sin ella, reintroducir la derivación sería un cambio equivalente hoy y una bomba de reloj mañana—; **(b) de comportamiento**, con `WOPTIMIZER_GIT_DIR` al repo que tiene el commit y `GIT_DIR` al que no, el check 9 tiene que leer el primero: si leyera el entorno acusaría el hash que el repo nombrado sí tiene, y el mutante de AC-3 muere por el **contenido** del FAIL («NO resuelve») y no por un `returncode`. **Contraprueba:** con `--git-dir` al repo equivocado el mismo árbol **sí** acusa, así que la fila que pasa no pasa por accidente. |
| 209 | `test_el_flag_git_dir_cambia_el_veredicto` | **TASK-075 (T-2 y AC-3): `--git-dir` llega a `validar()`, no solo al parser.** Validador **real como subproceso** (única forma de medir `main()` → `argparse` → `validar` → los dos checks de git). Dos repos que se diferencian **solo** en el commit que ancla el ciclo; con `GIT_DIR`, `WOPTIMIZER_GIT_DIR` y `LOCALAPPDATA` fuera del entorno no queda de dónde caer al default, así que si el veredicto cambia es porque el flag se ha usado. Un test que llamara a `_leer_los_argumentos` probaría el parser y nada más, y el mutante que acepta el flag y no lo propaga a `validar()` lo dejaría en verde. **Contraprueba:** el informe tiene que decir `origen: --git-dir`, que es la prueba de que la ruta llegó hasta la resolución. |
| 210 | `test_un_git_dir_que_no_sirve_falla_con_su_ruta_literal` | **TASK-075 (T-3, AC-4 y AC-5): lo que se dice a mano tiene que servir o FALLA.** Tres estados de un subproceso cada uno, y los tres son la misma clase: ruta **inexistente**, directorio que **existe y no es repo**, y repo **sin commits** (`rev-parse --verify HEAD` responde 128, «Needed a single revision»; `cat-file --batch-check` respondería `missing` para todo y acusaría ~100 hashes muertos de mentira). El criterio es `rev-parse --verify HEAD` y **NO** `os.path.exists()`, que da verde sobre el directorio vacío (mutante de AC-5), y es el mismo que usa `git_safe_commit.validar_repo` para que los dos componentes no puedan discrepar sobre qué es un repositorio. **Contraprueba:** ningún `[OK]` puede nombrar el repositorio que no sirvió, y el `[FAIL]` tiene que llevar la ruta **literal** que se dio. |
| 211 | `test_sin_ancla_de_git_no_se_parece_a_un_verde` | **TASK-075 (T-4 y AC-6): lo SALTADO sale como `[SKIP]` o no vale nada.** Medido sobre el **informe impreso**, porque un `[SKIP]` con formato de `[OK]` se ve en la pantalla, no en el tipo de retorno. `validar()` devuelve **tres listas** y lo saltado a propósito solo puede entrar en una: el muro es estructural, no un prefijo de texto. Tres líneas `[SKIP]` exactas (repositorio, historial, R2/R4), **ningún** `[OK]` con `SALTAD`, el resumen tiene que acabar en `, 3 SKIP`, y la línea `SIN COMPROBAR` del caso degradado **no** puede reutilizarse aquí: un fallo del entorno ya acusado y una orden del operador son dos hechos distintos. Además el código de salida es 0 —es lo que permite correr los demás checks— y por eso el informe tiene que ser inequívoco. **Contraprueba:** los checks que no usan git tienen que seguir corriendo, o el flag sería una excusa para no validar nada. |
| 212 | `test_el_informe_nombra_el_repositorio_del_anclaje` | **TASK-075 (T-5): el informe dice DE QUÉ repositorio leyó, con la ruta literal.** El único criterio del bloque que necesita aserción sobre la **cadena**: al borrar la línea de `ok` el veredicto no cambia, luego `errors == []` lo dejaría verde y lo que se rompe es la **auditabilidad**. MEDIDO: con `GIT_DIR` puesto a mano, dos informes idénticos podían venir de dos repositorios distintos, y con un `GIT_WORK_TREE` ajeno el informe no decía ni eso —y cambiarlo **no** cambia qué ficheros se validan (`root` sale de `__file__`), luego es información pura y por eso tiene que estar escrita. La línea lleva la ruta, su origen y el `GIT_WORK_TREE` respetado. **Contraprueba:** sin el flag, `saltados` tiene que ir vacío y ninguna línea de `ok` puede llevar `SALTAD`. |
| 213 | `test_el_motivo_de_la_exclusion_de_ci_esta_medido_y_escrito` | **TASK-075 (AC-8): la exclusión es correcta y el MOTIVO escrito es el medido.** MEDIDO: hasta el 2026-10-18 el motivo de `.github/workflows/release.yml` era `%LOCALAPPDATA%`, que es la atadura **menor** de las dos, y la fila de `STATUS.md` que lo resumía remitía a `docs/ai/sandbox-rules.md`, que **no mencionaba el CI en ninguna de sus 1339 líneas**. Una remisión a un documento que no existe es una mentira útil: el que la lee deja de buscar. Cuatro guards: (1) el cuerpo del job `verify` **con los comentarios fuera** no puede mencionar `validate_docs.py` —mata el mutante de TASK-080, que añadiría el paso; (2) el motivo viejo está fuera; (3) el nuevo trae la cifra y la fecha; (4) la sección de `sandbox-rules.md` existe y está **por encima de la línea 61**, porque `validate_docs.py` cita sus líneas 55-56 **por número** y una fila insertada por encima las desplaza sin avisar. **Contraprueba:** el test mide la **posición** de la sección, no su presencia, y de paso hace que la remisión de `STATUS.md` sea verdad por contenido y no solo por fichero existente. |
| 214 | `test_una_sola_declaracion_de_flags_de_pyinstaller` | **TASK-076 (AC-1): los flags se declaran UNA vez y los demas la INVOCAN.** No es un test de paridad, y el motivo esta MEDIDO: `force_build.py:11-16` y `.github/workflows/release.yml:208` eran identicos byte a byte **antes** de este cambio, luego compararlos habria salido en verde sin mirar nada. Tampoco sirve un modulo `FLAGS` que los dos importen: seguirian siendo dos listas, y si una copia de la otra la igualdad se cumple sola. El guard exige que `release.yml` y `build.bat` **no contengan** ningun flag de la lista, que no llamen a PyInstaller directamente y que invoquen `python force_build.py` **con el interprete delante** (`force_build.py` a secas no ejecuta nada en Windows, mutante R1-c). **Contraprueba:** el mismo detector tiene que ver la llamada directa cuando se la ponen delante. |
| 215 | `test_los_assets_que_lee_la_app_llegan_al_ejecutable` | **TASK-076 (AC-2): el guard que discrimina, porque su expectativa sale de `src/`.** Escanea `src/woptimizer/**/*.py` y recoge cada ruta bajo `assets/` que la app LEE (`process_service.py:347` -> `assets/process_db.json`; `app.py:23` y `:269` -> `assets/woptimizer.ico`), y exige que la unica declaracion las meta dentro del ejecutable. Las dos derivaciones no se pueden simplificar una contra otra, que es lo que hace tautologica una comparacion de `force_build.py` consigo mismo. **Mata el mutante R2-a** (borrar `--add-data assets;assets`), que es LITERALMENTE lo que hacia `build.bat:27` y que no mataba nadie: `config.py:11-14` hace que `_data_dir()` sea `sys._MEIPASS` en frozen, luego sin ese paquete el `.exe` arranca sin base de datos de procesos y sin icono. **Contraprueba:** `assets;data` (R2-b) y `--add-data assets` sin destino (R2-c) tienen que salir en negativo, y un escaner que no encuentre ninguna ruta tiene que FALLAR en vez de dar cobertura vacia. |
| 216 | `test_la_doc_no_vuelve_a_re_listar_los_flags` | **TASK-076 (AC-3): el ejemplo de la doc deja de ser una cuarta declaracion.** El bloque de `docs/ai/sandbox-rules.md:19-27` era la lista CORTA de cinco flags, sin `--add-data assets;assets`: un ejemplo ejecutable sin el paquete es un `.exe` sin assets publicado como si lo llevara. El alcance del guard es la SECCION 2, no el fichero entero, y la distincion tiene motivo: la seccion 3 **nombra** `--uac-admin` y `--add-data` como requisito, y nombrar un requisito no es declararlo. Mutante R3-a: la lista corta vuelve y el guard la ve. **Contraprueba:** la seccion 3 tiene que seguir nombrando los dos flags, porque sin `--add-data` desaparece del doc el unico sitio que explica por que hace falta el paquete. |
| 217 | `test_las_citas_de_sandbox_rules_siguen_siendo_ciertas` | **TASK-076 (AC-4): las cuatro afirmaciones que citan `sandbox-rules.md:55-56` no se pudren en silencio.** MEDIDO: `_declara_el_codigo_sobrecargado` (`validate_docs.py:1935`) compila el patron con `re.MULTILINE` sobre el cuerpo entero y **no mira numeros de linea**, luego insertar una fila por encima de la 55 no pone el validador en rojo: lo que se rompe es que `validate_docs.py:1429`, `validate_docs.py:1924`, `run_tests.py:30671` y `sandbox-rules.md:1133` quedan mintiendo. El guard afirma sobre CONTENIDO (las lineas 55 y 56 tienen que SER las dos filas del `0`, con la cabecera dos lineas mas arriba), no sobre que la cadena `55-56` siga presente, que no cambia nunca. Mutante R4-a. Comprueba ademas que las cuatro citas siguen ahi y que la seccion del motivo de CI sigue por encima de la 61. |
| 218 | `test_el_spec_no_vuelve_a_ser_la_fuente_de_verdad` | **TASK-076 (AC-5): `woptimizer.spec` existe pero no puede ser la fuente.** MEDIDO: esta en `.gitignore:29` (`*.spec`) y no aparece en `git ls-files`, luego es un residuo que PyInstaller regenera en cada build. El job `build` hace `actions/checkout` + `pip install -e ".[dev]"`: compilar con `--spec woptimizer.spec` (mutante R5-a) deja al runner sin ese fichero y **rompe el unico build que publica releases**. Centralizar en el `.spec` exigiria quitar `*.spec` del `.gitignore`, y es otro cambio con otro contrato: aqui se ata que nadie compile por `--spec` y que el fichero siga sin versionar. |
| 219 | `test_los_guards_de_flags_no_necesitan_yaml_ni_ejecutan_nada` | **TASK-076 (AC-6): los siete guards de este bloque son de TEXTO y no de proceso.** MEDIDO, `pyproject.toml:15-19` solo declara `pytest` y `pyinstaller`: un guard con `yaml.safe_load` pasaria en este host y reventaria en el job `verify` con `ModuleNotFoundError`, o sea el rojo llega al sitio donde ya no se puede arreglar. Mutante R6-a. Tampoco pueden lanzar subprocesos (suite headless, sandbox con `spawn EPERM`). La comprobacion es sobre el **AST** de las siete funciones por nombre, no sobre su texto, para que el nombre de la dependencia no se cuente a si mismo como evidencia, y afirma la PREMISA: si un dia `pyproject.toml` declara PyYAML, este guard hay que reescribirlo. |
| 220 | `test_la_linea_base_de_flags_se_deriva_del_fichero_real` | **TASK-076 (AC-7): la linea base se MIDIO, y se mide del fichero real.** La premisa del encargo se comprobo con un comparador sobre los tres ficheros antes de tocar nada: `force_build.py` y `release.yml` eran identicos y `build.bat` era el divergente. Este test ata esa medicion para que el registro no diga "los dos eran distintos" cuando medidos eran iguales. **Contraprueba (mutante R7-a):** la derivacion depende de la ruta que se le pasa, asi que una copia en `%TEMP%` con otra lista tiene que dar OTRA derivacion; si leyera de una copia o de una constante incrustada, las dos darian lo mismo y este control lo mata. |
| 221 | `test_la_politica_eol_cubre_todo_script_de_consola_que_existe` | **TASK-077 (AC-1): la politica EOL cubre lo que HAY, leida sobre BYTES.** MEDIDO antes del test: `build.bat` estaba en LF puro en el arbol local -- 39 `\n` y 0 `\r` -- pese a que su regla efectiva es `eol=crlf`. Ese cambio es invisible para `git status` y para `add -A` (el filtro `clean` normaliza CRLF->LF y sale el MISMO objeto del indice), o sea que se pierde en el checkout sin que nadie lo decida. **Por que NO se apoya en `git ls-files --eol`:** MEDIDO, en CI `actions/checkout` aplica los atributos en el checkout fresco, luego ese comando reporta `w/crlf` este sano o no el repo. No es un falso rojo, es un **verde falso**, y es la direccion peligrosa. Cuatro afirmaciones: (a) la regla base se **DERIVA** de `.gitattributes` y vale `lf`; (b) toda extension de script de consola **presente** tiene regla efectiva `crlf`, **y el conjunto presente no es vacio** (sin esa segunda mitad, borrar el ultimo `.bat` deja el bucle sin nada que mirar y el test verde); (c) los **bytes**: hay `\r\n` y no hay ni un `\n` suelto -- **hoy falla por la asercion**, no por no encontrar el fichero; (d) el contenido **normalizado** (`\r\n`->`\n`) no conserva ningun `\r`, que caza la clase `3012c48`. Sin PyYAML y sin `subprocess`. |
| 222 | `test_el_guard_de_eol_rechaza_lo_mismo_que_acepta` | **TASK-077 (AC-2): CONTRAPRUESTA del guard de EOL.** Cuarta vez aqui del patron "una comprobacion sin contraprueba no es una comprobacion" (ciclos 60 y 62). Sin este test, el anterior se puede vaciar entero: un evaluador que devolviera la lista de fallos vacia **SIEMPRE** daria OK en las tres celdas y AC-1 seguiria verde. Camara en `%TEMP%` con el `.gitattributes` REAL y scripts sinteticos: un `.bat` en CRLF tiene que dar **OK**, un `.bat` en LF tiene que dar **FAIL**, y con la regla `*.bat` **borrada** un `.bat` presente tiene que dar **FAIL por cobertura**. El tercero es el que distingue "no hay regla" de "hay bytes malos": sin el, un resolvedor que devolviera `crlf` para todo pasaria los dos primeros. El mensaje del fallo tiene que hablar de BYTES y no de cobertura, para que quien lo lea sepa que arreglar. |
| 223 | `test_build_bat_propaga_el_codigo_de_salida_de_force_build` | **TASK-077 (AC-3, absorbe S3 de `STATUS.md:64`): `build.bat` sale con el codigo de fallo.** MEDIDO de extremo a extremo antes del fix: con `force_build.py` saliendo con 7, `build.bat` salia con **0**. ⚠️ **CORREGIDO el 2026-10-18:** esta fila decia que "la causa era doble" y el `mutation-auditor` lo REFUTO con medicion. El `0` lo producia el `exit /b 0` incondicional de `:fallo`, **no** la falta del `call`: el log del ciclo 65 sale con `Construyendo...` y `[ERROR] Fallo la compilacion` IMPRESOS, o sea que el control volvio al `.bat`. Los dos `call` son un guard legitimo y load-bearing, pero el sintoma ya estaba medido y explicado por otra causa. Camara con el `.bat` REAL y un stub de `python.cmd` en `%PATH%`. **Cinco celdas, y solo la primera es el sujeto:** (A) compilacion que sale 7 tiene que dar 7 y sin decir `EXITO`; (B) compilacion que sale 0 **sin crear** el `.exe` tiene que dar != 0 -- sin esta, un `.bat` que devolviera != 0 SIEMPRE pasaria A; (C) compilacion correcta tiene que dar 0; (D) PyInstaller ausente tiene que dar != 0 **Y no borrar el `dist\woptimizer.exe` que ya funcionaba, Y nombrar la falta de PyInstaller en el motivo impreso** -- ver la nota de la celda D mas abajo; (E) los **dos `call`**, medidos por la AUSENCIA de la linea que deberian imprimir (`Construyendo...` y `Fallo la compilacion`), porque quitar el `call` del paso 3 **no cambia el rc** (sigue dando 7, el del shim): un guard que solo mirase el codigo dejaria pasar ese mutante. `stdin` va a `NUL` porque la salida `:sin_pyinstaller` tiene un `pause`. **CELDA D, ENDURECIDA el 2026-10-18 (mutante `S3b`, que SOBREVIVIO verde):** el `rc != 0` lo cumplia el mutante igual, porque sale 1 en las dos variantes. Lo que si lo distingue son tres aserciones de CONTENIDO: el `.exe` preexistente **sobrevive** (sin el `if errorlevel 1` del paso 1 el flujo llegaba al `del` y se llevaba el ejecutable del usuario), la salida contiene `PyInstaller no esta instalado`, y **no** contiene `Fallo la compilacion` (el motivo impreso tiene que describir la causa real; el mutante caia en el `:fallo` comun y mandaba a mirar un log que no existia). |
| 224 | `test_la_camara_de_build_bat_detecta_la_regresion` | **TASK-077 (AC-4): CONTRAPRUESTA de la camara de `build.bat`.** Sin este test, AC-3 pasaria con **cualquier** variante de `build.bat`: una camara que acepta cualquier codigo mide lo mismo que no medir (mutante `S2`). Se repone el cierre historico (`exit /b 0`) sobre el texto REAL del repo, en una copia de `%TEMP%`, y tiene que **volver a dar 0** con la compilacion fallando. **Lleva ademas CONTROL POSITIVO, y no es cosmetico: MEDIDO, sin esa celda el mutante `S2` -- una camara que devuelve `returncode = 0` SIEMPRE -- SOBREVIVIO**, porque cumplia "la regresion vuelve a dar 0" sin medir nada. El `.bat` sano, en la misma camara y con el mismo stub, tiene que dar 7. ⚠️ **El helper de la camara esta partido en dos a proposito:** el que la dibuja copiaba tambien el `build.bat` real y **pisaba el mutante con el fichero sano** al reutilizarlo desde la contraprueba, que pasaba por el motivo equivocado; ahora hay `_dibujar_build_bat` (copia el `.bat`) y `_dibujar_stub_de_python` (solo el shim). No se quitan los dos fallos a la vez porque **no se pueden distinguir**: sin `call` en el paso 3 el rc es el del shim, luego el mutante de `call` mide su propia celda (E) y este el del cierre. El repositorio no se toca: el mutante vive y muere dentro de la camara. |
| 225 | `test_el_guard_de_eol_no_deja_que_un_homonimo_tape_a_otro` | **TASK-077 (AC-5): dos `.bat` homonimos NO se pisan entre si.** Mutante `N3x` del propio `mutation-auditor`, y el que puede dar **VERDE FALSO**: `_fallos_de_politica_eol` acumulaba `presentes[nombre] = ruta`, un diccionario por `basename`, luego el ULTIMO que recorre `os.walk` **pisa** al primero y el primero **deja de mirarse**. MEDIDO: un `build.bat` en CRLF en un subdirectorio tapaba al `build.bat` de la raiz que estaba en LF, el evaluador devolvia `[]` y el guard daba OK con el repositorio incumplido. Dos celdas en camara de `%TEMP%` con el `.gitattributes` REAL: (1) raiz en **LF** y `herramientas/` en **CRLF** tiene que dar **FAIL nombrando el de la RAIZ**, y el mensaje tiene que separarlos por su ruta; (2) **CONTROL POSITIVO**, los dos en CRLF tiene que dar **OK**, porque sin el un evaluador que fallara SIEMPRE pasaria la primera sin medir nada. Quinta vez en este repo que sale el patron "dato derivado escrito a mano". |
| 226 | `test_la_cita_del_ultimo_byte_de_build_bat_no_se_caduca` | **TASK-077 (AC-6): lo que `.gitattributes` dice de `build.bat`, se mide contra el fichero.** MEDIDO: `.gitattributes` afirmaba que el ultimo byte de `build.bat` es `0x30` y es `0x31` -- el propio arreglo de TASK-077 anadio una linea al final (`exit /b 1` donde estaba `exit /b 0`), **movio el byte que su propia documentacion citaba como evidencia y el texto no se reviso**. El digito NO se copia a mano en el test: se **extrae** con `re` de la frase `su ultimo byte es \`0xNN\`` y se **compara** con el byte real del fichero, de modo que el dia que alguien anada una linea al `.bat` el guard se pone rojo en vez de dejar el documento mintiendo en silencio. Una asercion exige que la frase este **exactamente una vez** (si el `.gitattributes` la reformula, el guard avisa en vez de quedarse sin comprobar nada) y otra que el fichero **no** termine en `0x0A`: es la afirmacion de fondo que el digito sostiene, la "ULTIMA LINEA SIN salto terminador" del banco de medidas. Sin PyYAML, sin `subprocess` y sin ventana. |
| 227 | `test_ningun_guard_enumera_el_arbol_de_src_que_ya_esta_en_el_sistema_de_ficheros` | **TASK-081 (R4/AC-5): el guard de FORMA que cierra la clase, no el caso.** Con `ast`, sobre `run_tests.py`, `validate_docs.py` y `verify_ui_syntax.py`: ninguna clase, funcion ni sentencia de modulo puede contener una lista o tupla de **dos o mas** literales de ruta bajo `src/woptimizer/**.py` sin derivar el alcance con `rglob`/`glob`/`iterdir`/`os.walk`. Cada hallazgo se nombra con **fichero y linea** en el mensaje, que es lo que lo hace deuda VISIBLE en vez de agujero invisible. **DENUNCIA, NO REPARA**, y esa distincion es el sujeto: las enumeraciones pre-existentes NO entran en una lista muda de permitidos, porque una lista de permitidos es la misma trampa por la que `verify_ui_syntax.py` lleva fallando desde el 1 de octubre. La unica tolerancia es el **docstring del propio guard**, con las dos frases exigidas -- (a) por que existe la enumeracion y (b) que la retira -- y con texto de verdad detras (30 caracteres como minimo, en la misma linea): un marcador pegado y vacio se rechaza igual que una enumeracion a pelo. **MEDIDO al escribirlo que el encargo se equivoco en el numero:** hay **DOS** tuplas de cuatro rutas en `run_tests.py`, `test_no_literal_colors_in_views` y `test_hit_targets_minimum`, y la segunda no venia en el encargo; las dos quedan escritas. `_copiar_el_esqueleto_del_validador` tambien lleva su justificacion escrita aunque **queda FUERA del alcance de este guard** (R5 acota a literales de ruta de `src/` y su tupla son ficheros de raiz): un `ast.walk` NO cuenta como derivacion --recorre el arbol de sintaxis, no el de ficheros-- y contarlo haria pasar por justificadas dos guards que no derivan nada. Contraprueba de **cuatro celdas** sobre codigo sintetico: lista sin justificar se denuncia, alcance derivado se calla, lista justificada se tolera, justificacion con marcador pero SIN TEXTO se denuncia. La cuarta es la que impide comprar el verde con dos etiquetas pegadas. **MATA** `M-W`. |
| 228 | `test_la_verificacion_de_sintaxis_deriva_su_alcance_y_no_lo_enumera` | **TASK-081 (AC-1): el sujeto se deriva y no esta escrito a mano.** `verify_ui_syntax.py` no contiene ninguna lista o tupla con dos o mas literales de ruta bajo `src/woptimizer/**.py`, comprobado con **`ast`** y no con busqueda de texto: un `rglob` escrito en un comentario tiene que pasar, y solo el arbol lo distingue de una llamada. Y la derivacion tiene que estar **REALMENTE USADA**: hay un `for` que recorre lo que produce el `rglob`, directo o a traves de un helper local (`ficheros = modulos_del_arbol()`); sin esa segunda mitad el mutante `M-R` --la lista de diez rutas de vuelta con `rglob` escrito y muerto-- pasa la primera asercion, porque el `rglob` estari alla. Un `rglob` presente y sin usar es **SIN COBERTURA** y tiene que morir. **Contraprueba del detector en las dos direcciones**: la lista literal sintetica se denuncia y la derivacion se calla; sin esto, un detector que devolviera `[]` siempre cumpliria las dos aserciones sin mirar nada. **MATA** `M-L` (la tupla literal de diez rutas) y `M-R`. |
| 229 | `test_la_verificacion_de_sintaxis_agrega_un_modulo_nuevo` | **TASK-081 (AC-3): un modulo NUEVO, no listado por nadie, se detecta. El unico AC que no puede sobrevivir sin el arreglo.** MEDIDO antes del arreglo: un `src/woptimizer/ui/views/ajustes_view.py` roto daba **exit 0, VERDE**. Un fichero que aparece hoy no puede estar en ninguna enumeracion, porque ayer no existia -- ese es el caso M4, y es el que se va a dar el dia que alguien anada una vista. La camara copia `src/` REAL y el script REAL a `%TEMP%` y anade el modulo con error de sintaxis; se exigen las **dos** mitades del veredicto, `exit 1` **y** que la salida **nombre** el modulo (un rojo que obliga a ir a buscar a mano no dice que esta mal, dice que hay que mirarlo). Y el sujeto es el **PRODUCTO** -- el subproceso de verdad --, no el texto: por eso no se puede falsear con un comentario ni con un `rglob` sin usar, que es justo lo que haria inutil una comparacion `rglob` contra `rglob`. |
| 230 | `test_la_camara_de_sintaxis_ui_distingue_sano_de_roto` | **TASK-081 (AC-4): CONTROL POSITIVO de AC-3. Sin el, AC-3 no significa nada.** El mismo arbol (`src/` real + un modulo **sano** anadido) tiene que dar **exit 0**. Es el control que falto en el ciclo 66 y por eso el mutante `S2` sobrevivio alli: una camara que devuelve exit 1 SIEMPRE cumple AC-3 sin mirar nada, que es un rojo que no significa ni "el codigo esta mal" ni "el codigo esta bien". Las aserciones de esta celda son de **CONTENIDO**, no solo de codigo de salida: la linea `ALCANCE_DERIVADO=N` se imprime **una vez**, tiene que coincidir con los `.py` que la camara tiene en disco, y el modulo sano anadido tiene que aparecer **nombrado** en la salida -- si el recuento sube sin nombrarlo, el guion esta contando otra cosa. **MATA** `M-C` (una camara que devuelve exit 1 siempre). |
| 231 | `test_el_recuento_de_modulos_de_sintaxis_es_derivado` | **TASK-081 (AC-2): la cifra que declara `STATUS.md` es la que el script IMPRIME.** El panel decia «10 modulos» -- escrita a mano -- y el changelog ha dicho «8 de 8», «9 de 9» y «10» en tres ciclos: tres cifras para el mismo conjunto y ninguna atada al conjunto. Aqui la cifra sigue escrita en el documento porque el panel la necesita para ser legible, pero deja de ser una CONSTANTE: se deriva, y el test la ata a lo que el script **imprime ejecutandolo de verdad** sobre el repo real (`exit 0` exigido). Tres mitades para que no sea un espejo de si mismo: el numero impreso tiene que ser **UNO** y tiene que coincidir con los `.py` que hay en disco; la fila de `STATUS.md` que habla de `verify_ui_syntax.py` tiene que ser **UNA** y declarar **UNA sola** cifra con la forma `N modulos`; y esa cifra tiene que ser la derivada. **DECISION, y por que la cifra no se borra del documento:** la alternativa --dejar el panel sin numero-- hacia que `M-S` no tuviera nada contra lo que morir y que el panel se quedara mudo el dia que se anadiera un modulo. Una cifra atada a su derivado avisa con el numero bueno al lado del malo; una cifra ausente no dice nada. Es el mismo patron que `validate_docs.py` ya usa con el recuento de la suite. **MATA** `M-S` (volver a «10 modulos» como cifra fija). |
| 232 | `test_el_conjunto_de_vistas_tiene_una_sola_fuente_de_verdad` | **TASK-082 (AC-1): el conjunto de vistas tiene UNA sola fuente de verdad.** Con `ast` y como REGLA DE MODULO: el detector recorre TODAS las funciones de `run_tests.py` y no tiene ningun conjunto de sujetos escrito a mano. La DECLARACION se DERIVA (es la enumeracion COMPARADA con el derivado) y la funcion que deriva tambien; el helper que deriva NO puede devolver la DECLARACION (su `return` sale del disco); y NINGUNA funcion recorre una enumeracion escrita a mano del conjunto de vistas. La tolerancia es la JUSTIFICACION ESCRITA en el docstring del infractor --(a) por que existe y (b) que la retira--, no una lista de permitidos. **MATA** Q2 y Q2b (el detector miraba dos guards, o ninguno, y la suite lo daba por bueno), M-V4 y M-V5 por forma. |
| 233 | `test_una_vista_nueva_se_audita_aunque_nadie_la_apunte` | **TASK-082 (AC-2): una vista NUEVA se audita aunque nadie la apunte.** Se EJECUTA el guard de workers sobre una camara en `%TEMP%` con `src/` real y una vista nueva, y se exigen las dos mitades del veredicto: el codigo de salida Y que la salida NOMBRE la infraccion. Tres veredictos: la vista con la infraccion da ROJO que la nombra; la MISMA sin infraccion da VERDE (control positivo: sin el, un guard que siempre da ROJO cumpliria el AC); y la MISMA en el disco y SIN declarar da ROJO que nombra la vista nueva. El tercero es el que mata a M-V5 por PRODUCTO y no por efecto colateral: con la derivacion falsa la comparacion es tautologica, no hay rojo, y la vista nueva deja de auditarse sin que nadie lo note. **MATA** M-V1 y M-V5. |
| 234 | `test_el_derivado_de_vistas_es_el_disco_y_abre_algo` | **TASK-082 (AC-3): el derivado ES el disco, y abre algo.** El derivado se compara con un `os.listdir` del directorio de vistas --OTRA API que la del helper (`glob`), para que las dos derivaciones no den el mismo resultado por casualidad--; el derivado NO esta vacio y cada nombre es un fichero de verdad (un derivado vacio es "cero infracciones sobre cero ficheros"); y un derivado VACIO da ROJO, medido en camara (se vacian las vistas y el guard tiene que caer). **MATA** M-V3. |
| 235 | `test_el_hash_muerto_se_deriva_por_construccion_y_no_por_concatenacion` | **TASK-083 (AC-4): el tripwire que vigila la CONSTRUCCIÓN del hash muerto.** Con `ast` sobre la suite, dos reglas DERIVADAS del código: (1) NINGÚN `BinOp(Add)` puede concatenar una expresión que parece un hash (`hash`, `sha`, `digest`, `hex`, `short`) con un literal hex de 1 a 8 dígitos — con el arreglo, **0 hallazgos**; si alguien vuelve a `hash_real + "0"`, el guard da ROJO nombrando **fichero y línea** (MEDIDO en cámara desechable: `run_tests.py:23605: hash_real + '0'` — el `23605` es la línea de la CÁMARA, no la del repo: en el repo ese patrón ya no existe porque el arreglo está aplicado). (2) El hash bajo prueba tiene que VENIR de la derivación por construcción (`_hash_muerto_por_construccion`), que tiene que estar VIVA (la llama alguien) y LLEGAR al uso de hash bajo prueba; un literal fijo en su lugar da ROJO (`la derivación por construcción no la llama nadie`). El guard se prueba A SÍ MISMO con casos SINTÉTICOS: un `sha real + dígito` que SÍ existe queda FUERA de los dígitos libres, uno que NO existe da 0 hallazgos, y sin ningún dígito libre la derivación REVIENTA (nunca una lista vacía en silencio). **Es un `test_*` CONTADO a propósito** (lección A-C68-1: un guard que nadie cuenta se puede borrar sin que nada se entere). |


---

## El veredicto de mutación es comprobable (TASK-087, ciclo 70)

Desde el ciclo 70 el veredicto por mutante **deja de ser prosa**. Antes lo
escribía a mano el `mutation-auditor` en el `mutation-report.md`, y nadie
podía volver a comprobarlo: MEDIDO, **borrar el veredicto del journal daba
0 FAIL** y **borrar el `mutation-report.md` entero daba 0 FAIL**, mientras que
borrar una *fila* del journal daba 1 FAIL. La fila estaba vigilada; el
veredicto y el informe, no.

Ahora el veredicto es una **línea canónica** que un programa escribe y que el
validador **re-deriva** desde la evidencia commiteada:

```
WOPT_VEREDICTO <mutante> <MUERTO|SOBREVIVIENTE|NO MEDIDO> <sha>
```

### Los tres estados

| Estado | Condición mecánica | Qué hace el bucle |
|---|---|---|
| **MUERTO** | el log está en ROJO, el test que murió —derivado del *frame* del *traceback*— es **exactamente** el `asa` declarado, y el motivo literal de la aserción contiene el `motivo` declarado | el fix está verificado |
| **SOBREVIVIENTE** | la suite completa terminó en VERDE (`rc=0` y la última línea es `ALL TESTS PASSED.`) | el fix **no** está verificado: es un FAIL |
| **NO MEDIDO** | todo lo demás: log cortado, murió otro test, el motivo no nombra la infracción, o dos corridas del mismo mutante dan veredictos distintos | el mutante **se encola como tarea** y el ciclo sigue a Paso 1 |

El texto íntegro del contrato está en `.agents/agents/mutation-auditor/agent.md`
—la fuente de verdad del agente— y la parte automatizable en el código:

| Pieza | Dónde | Qué hace |
|---|---|---|
| Emisor | `.taskmaster/veredicto.py` | del catálogo + las colas de los logs deriva el estado y escribe la línea canónica y la evidencia |
| Gate | `validate_docs.py`, **check 11** | **re-deriva** cada veredicto desde la evidencia commiteada y falla si la línea no cuadra |
| Catálogo | `openspec/changes/<id>/mutaciones.json` | lo declara **quien muta**: el `asa` (el `test_*` exacto que tiene que morir) y el `motivo` |
| Evidencia | `openspec/changes/<id>/evidencia/<mutante>.cola` | la cola del log (desde el `Traceback` hasta el final, o las últimas 200 B si no hay traza) |

El gate **deriva** el conjunto de sujetos (las entradas del journal con
`cycle >= 70`, y el cambio de cada entrada por su campo `change`), así que
**no se puede vaciar**: borrarle la línea a una entrada, o borrar el informe
del ciclo, es un FAIL.

### Por qué el gate vive en `validate_docs.py` y no en la suite

El journal y los changelogs se escriben **después** del Paso 4, luego un
`test_*` de la suite solo vería el veredicto del ciclo **anterior**. Y añadir
un `test_*` obligaría a subir el recuento a 236 y a mover cinco declaraciones
escritas a mano. El gate va en el validador, el **recuento se queda en
235 = 159 + 76**, y las cinco declaraciones no se mueven.

### Lo que el gate NO prueba

Que el `asa` declarada sea la guard **semánticamente** correcta para esa
mutación: el log dice *quién murió*, nunca *quién debía*, y la spec no
contiene el nombre de la función. Lo que sí prueba es que el veredicto es
**re-derivable** desde la evidencia commiteada, y que **no se puede escribir
sin la línea canónica**.

Y los otros tres, MEDIDOS (ciclo 70, mutantes K-10b y K-12), que el docstring
del gate declara con su motivo:

- **Que la evidencia commiteada SEA el log real.** La evidencia la escribe
  quien muta y el gate no comprueba el **fichero** del frame del traceback:
  una evidencia fabricada con el frame en otro fichero la acepta y deriva
  MUERTO → **0 FAIL**. El gate prueba la **coherencia** con la evidencia
  commiteada, no la **verdad** del log.
- **Que el `sha` del árbol auditado exista.** El sha se copia tal cual de la
  línea canónica y **no se resuelve** contra ningún objeto de ningún
  repositorio: un sha inventado → **0 FAIL**. El sha commiteado de M-3
  (`e8111158…`) es el del **árbol auditado** (la cámara donde se midió), que
  no es el repo real: identifica el árbol **medido**, no el repo.
- **Que los changelogs lleven las líneas.** Se comprueban si están, pero su
  ausencia no es un FAIL (el journal y el informe son los dos anclajes).
- **Que el gate no esté CIEGO** (límite **(f)**, ciclo 71). MEDIDO: con el
  **cuerpo** de `_comprobar_veredictos_de_mutacion` **vaciado** y el REGISTRO
  puesto, el validador daba **0 FAIL** sobre un catálogo que se contradice a sí
  mismo y la suite se quedaba en **VERDE**: el cableado seguía vivo y el gate
  no miraba nada. El validador, **por sí solo, NO detecta un gate ciego**; lo
  que lo detecta es la **suite**, con un guard de **producto** (sección (D) de
  la fila 130).
- **Que el TEXTO declarado (`mutacion.original`) siga en el fichero** (límite
  **(g)**, ciclo 72). MEDIDO: el `original` declarado es un bloque contiguo en
  **22 de los 26** mutantes y está en la **línea** declarada en **1 de 26**, y
  comprobarlo costaría **62,3 ms** contra **46,2 ms** disponibles. Los tres
  motivos, medidos, están en su sección.

Esa lista **NO es exhaustiva**: es la de los límites **medidos** hasta ahora
(ciclos 70 y 71: K-1..K-17 y D-B; ciclo 72: el límite (g)). Un límite que nadie
ha medido sigue sin declararse, y declararlo sin medirlo sería escribir una
promesa que nadie ha comprobado. Lo que sí es exhaustivo es la lista de lo que
el gate **prueba**, que sale del código y no de la prosa.

### El guard sobre el guard (K-8)

El gate era un guard **desenchufable**: `validar()` podía dejar de llamar al
check 11 y el validador daba 160 OK, 0 FAIL y **sin REGISTRO** — nadie lo
notaba. Es la clase exacta que este repo lleva dos ciclos persiguiendo. El
cableado del check 11 se ata ahora en el mismo test que ata el del check 9
(`test_el_check_9_se_cablea_en_el_camino_real_del_validador`, fila 130): con
todo cableado el REGISTRO aparece, y con la llamada sustituida por `pass` el
test se pone rojo.

### El gate tiene que DISTINGUIR (D-B, ciclo 71)

El guard anterior vigilaba el **cableado** del gate, no lo que el gate **DICE**.
Y el contenido no lo vigilaba nadie: MEDIDO, con el **cuerpo** del gate vaciado
y el REGISTRO puesto, el validador daba **0 FAIL** sobre un catálogo que se
contradecía a sí mismo y la suite se quedaba en **VERDE**. El guard nuevo (D)
es de **producto**: monta un corpus **sintético** en el esqueleto temporal y
exige que el gate **acuse** a sus contradictorios y **calle** sobre sus
coherentes (D1); la **contraprueba** (D2) vacía el **cuerpo** del gate —con el
REGISTRO puesto, que es lo único que el guard de cableado mira— y exige que esa
acusación **desaparezca** y que el REGISTRO **siga**. Sin D2, D1 podría cumplirse
por un motivo equivocado (un gate que acusa **siempre** también la cumpliría);
por eso el **orden** de las aserciones es normativo: la primera que salta es la
que deja su mensaje al final del log, y ese mensaje es el `motivo` que el gate
re-deriva.

**EL CORPUS TIENE QUE EJERCITAR TODAS LAS RAMAS QUE EL GUARD VIGILA.** Con una
sola contradicción, un solo orden y una sola entrada de journal, cuatro
mutantes del gate se comportan **igual que el gate sano** y el guard no tiene
por dónde verlos (MEDIDO en la auditoría del ciclo 71: **M-94**, **M-95**,
**M-99** y **M-100** sobrevivían). Por eso el corpus lleva:

| Pieza | Qué ramo del gate ejercita |
|---|---|
| **DOS entradas** de journal, con las contradicciones en la **SEGUNDA** | el gate que solo mira la PRIMERA entrada (M-95) no ve ninguna |
| la contradicción en los **DOS sentidos**: declarada SOBREVIVIENTE con evidencia MUERTO, y declarada MUERTO con evidencia SOBREVIVIENTE | el gate que decide por la DECLARACIÓN y no por la EVIDENCIA (M-99) solo ve el primero |
| el contradictorio al **PRINCIPIO** de su catálogo y el coherente al **FINAL** | el gate que mira solo el último (M-94) y el que mira solo el primero (M-92) |
| un sentinela con el **motivo equivocado** (su evidencia obliga a NO MEDIDO) | el gate que no comprueba el motivo (M-100) lo certificaría MUERTO |
| **DOS** sentinelas coherentes | el gate que **acusa en lo que no puede** (M-91) |

**LA TERCERA RONDA (TASK-090, ciclo 71): CUATRO RAMAS MÁS QUE EL CORPUS NO
EJERCITABA.** MEDIDO el 2026-10-22 (ronda 3 del `mutation-auditor`): con el
corpus de arriba, los cuatro mutantes propios **M-108**, **M-109**, **M-110** y
**M-112** **SOBREVIVIERON**. Los cuatro son ramas que el gate **COMPRUEBA** y
que el corpus **NO EJERCITABA**: el fallo era del corpus, no del gate (el mismo
patrón de las dos rondas anteriores, otra vez). El corpus lleva ahora **SEIS**
entradas de journal y **QUINCE** sentinelas (tres coherentes y doce
contradictorios), y estas cuatro ramas tienen un centinela cada una:

| Centinela | Qué ramo del gate ejercita | Por qué ese centinela muere si la rama vuelve a morir |
|---|---|---|
| `M-FIX-LIMITE` | la entrada del journal que está en el **LÍMITE** (el ciclo 70, el origen del contrato) tiene que estar **MIRADA** | su veredicto **se acusa**: el gate tiene que haberla **JUZGADO**. Un gate que filtra el journal con `>` en vez de `>=` no la examina, y el guard solo comprobaba su **silencio** |
| `M-FIX-SIN-LINEA` | el **catálogo** declara un mutante que el journal **NO** lleva en línea canónica | es el **espejo** de `M-FIX-FUERA` (que es al revés: una línea del journal que no está en el catálogo). Sin su acusación, un veredicto puede **desaparecer** de lo publicado sin un solo FAIL |
| `M-FIX-INFORME-CORTO` | el journal lleva una línea canónica que el **informe** del ciclo **NO** lleva | el segundo testigo puede quedarse **corto** sin que nadie lo note. OJO con la semántica, que es contraintuitiva: la mutación que lo mata es `!=` → `del_informe - del_journal`, y esa diferencia se queja de lo que el informe tiene de **MÁS**, luego un informe con una línea de más la acusa **igual**: el caso que la mata es el **inverso** |
| `M-FIX-CHANGELOG` | los **DOS changelogs** contra la evidencia commiteada | su línea canónica va en los changelogs con un estado **DISCREPANTE** del que obliga la evidencia: la copia legible del veredicto puede **contradecir** a la evidencia commiteada |

Y el **REGISTRO** tiene que contar las **seis** entradas del corpus: un gate que
no examinase la del LÍMITE contaría menos. Cada celda exige el `[FAIL]` **DE SU
RAZÓN**, que es lo que la distingue: si el gate acusara por otra causa, el texto
no estaría y la celda caería.

**COSTE MEDIDO:** 31,9 s del test completo (guard incluido), de los que ~9 s son
las dos corridas del validador sobre el esqueleto (una con el gate sano y otra
con el cuerpo vaciado), un **1,2 %** de la suite de 735 s. El corpus se amplía
**dentro de la misma corrida**: las aserciones extra no cuestan nada, y el
coste **no se multiplica**. El A/B **intercalado** contra HEAD (el corpus
viejo) da **9,73 s** frente a **10,09 s**: un delta de **−0,36 s**, dentro del
ruido del host (las muestras individuales van de 8,80 a 11,09 s). El coste
**marginal del validador no cambia** (10,3 ms el check 11, antes y después: el
límite (f) son comments).

### El gate tiene que LEER la `mutacion` (TASK-091, ciclo 72)

El gate leía `id`, `asa`, `motivo` y `sha_arbol_auditado` del catálogo y
**descartaba** el campo `mutacion`. MEDIDO: un catálogo que declara una mutación
que **no existe** —un `mutacion.fichero` que no es un fichero— pasaba el gate con
**0 FAIL**, y lo mismo con un `ciclo: 999` (un catálogo haciéndose pasar por el
de otro ciclo). Es el mismo agujero del ciclo 71 (D-B) con otra forma: el gate
miraba el *juicio* y no miraba la *declaración*.

Ahora el check 11 lee la `mutacion`, con **cuatro reglas que NO CADUCAN**:

| Regla | Qué comprueba | Frecuencia |
|---|---|---|
| **R1** | la `mutacion` es un objeto con `fichero`/`original`/`sustituto` no vacíos, `original != sustituto` y `linea` un entero `>= 1` | por mutante |
| **R2** | el fichero que declara **EXISTE** y resuelve **dentro** del árbol | por mutante |
| **R3** | el `cambio` del catálogo es el `change` de la entrada del journal que lo ancla | por entrada del journal |
| **R4** | el `ciclo` del catálogo es el `cycle` de esa misma entrada | por entrada del journal |

Ninguna lee el **contenido** de un fichero: R2 hace un `os.path.isfile` (un
`stat`) y las otras tres comparan dos declaraciones. MEDIDO en este host: **0,88
ms** las cuatro juntas para los 26 mutantes vivos (R1 0,011 ms; R2 0,872 ms —
26 `stat`, ~33 µs cada uno, que en Windows con el filtro de VFS no es gratis—;
R3+R4 0,0003 ms). El margen del gate es de **0,5 %** del validador, luego el
margen que queda es de **9,4 ms** en este host (4,83 s de validador → 24,2 ms de
presupuesto, 14,8 ms de margen consumido): **cabe de sobra**.

**Cada regla tiene su celda**, porque una regla que nadie vigila no está puesta
(la lección del ciclo 71, repetida): **F1** (R2, con el centinela **ROTO**),
**F1-bis** (R1, con un tercer centinela cuya `mutacion` tiene la **FORMA** rota:
`linea: 0`, la misma forma rota que el catálogo real tenía en M-121), **F2**
(R4, con el `ciclo: 999`), **F2-bis** (R3, con el `cambio` de otro cambio),
**F3** (la contraprueba: con la `mutacion` correcta el gate **CALLA** sobre los
tres), **F4** (el catálogo **real**) y **F5** (el límite **(g)**). El orden de
los centinelas es normativo: el **ROTO va SEGUNDO**, para que un gate que mire
solo el primero (el mutante **M-92**, que ya existe en el catálogo) quede
cogido.

**El límite (g): el TEXTO declarado NO se comprueba.** El gate comprueba que la
`mutacion` esté **declarada** y con forma, que su fichero exista y que el
catálogo sea el del ciclo y del cambio que dice ser, pero **NO** que el texto
declarado siga en ese fichero. Tres motivos **medidos**:

- **CADUCIDAD.** El `original` declarado era un bloque **contiguo** en **24 de los
  26** mutantes antes de este ciclo y es **22 de los 26** ahora: este ciclo
  rompió el texto de tres recetas (M-90, M-92 y M-94, que apuntaban al cuerpo
  del gate y a su bucle de mutantes) y la migración de M-121 lo volvió
  contiguo. Y el texto está en la **línea** declarada en **1 de 26** (solo
  M-107): exigirlo en la línea daría FAIL sobre **25 de los 26**.
- **COSTE.** Comprobarlo cuesta **62,3 ms** (26 mutantes, 5 ficheros, 1,891 MB
  leídos, caché por ruta + búsqueda `in`) y el presupuesto del gate es del
  **0,5 %** de los 11,28 s del validador = **56,4 ms**, con un margen actual de
  **10,2 ms**: disponibles **46,2 ms**, luego **NO CABE**.
- **SEMÁNTICA.** La RECETA caduca, el VEREDICTO no: el veredicto es un hecho
  sobre el árbol **auditado** (`sha_arbol_auditado`) y no se invalida porque el
  código se mueva después. Un FAIL por eso convertiría el gate en una bomba de
  relojería (habría que re-declarar mutantes históricos cada vez que se mueve el
  código), que es justo lo que este encargo prohíbe.

**La migración del catálogo real (AC-3).** El catálogo del repo tiene **26
mutantes vivos** y no todos pasaban R1/R2. MEDIDO (censo con las mismas reglas
del gate): **solo M-121** fallaba, y por las dos razones a la vez —su
`mutacion.fichero` era `"run_tests.py + validate_docs.py"` (dos rutas en una,
que no es un fichero) y su `linea` era `0`—. Con el gate nuevo, el validador daba
**1 FAIL** sobre el propio catálogo del repo. La **migración mínima** declara una
receta **aplicable**: el bloque **contiguo** de `run_tests.py` (líneas
23354-23365) que neutraliza las DOS cosas que M-121 neutraliza —la celda
(D1-ter)(d) del LÍMITE y la aserción de `'entradas cubiertas'`, que son líneas
consecutivas— por un `pass`. La **segunda mitad** del mutante (que además
aplica M-109 sobre `validate_docs.py`) **no cabe** en un único `mutacion` (el
campo declara un fichero): queda **declarada** en la nota de la entrada, con su
receta en la entrada de M-109, y la ronda 6 del `mutation-auditor` tiene que
aplicar las dos.

### El check 12 tambien tiene que estar cableado (C-9, C-6, C-7, T-1)

El check 12 (el paso de publicacion de la skill del motor) llego tarde y nacio
**desvigilado**: MEDIDO el 2026-10-22 (ronda 4 del `mutation-auditor`), la suite
no tenia **ni una** referencia a el (T-1), y sus **ocho** mutantes propios
sobrevivian. Los cuatro fallos, con su mecanismo medido:

- **C-9, el falso verde.** El recorte del check 12 era **PROPIO** y por
  **LINEAS**: solo reconocia una valla si la linea **empezaba** por ```` ``` ````,
  asi que una valla con prefijo `> ` --que es exactamente como esta la valla del
  propio `SKILL.md`-- la leia como contenido operativo. La skill podia dejar de
  mandar publicar y el check decia que si. El guard de la regla de rama (fila
  159) usa un recorte **por REGEX** y SI la excluia: los dos recortes **NO** eran
  el mismo, contra lo que decia el docstring del check 12.
- **C-6.** El control interno del comentario HTML era de **UNA** linea, luego no
  tocaba la rama multilinea: un comentario `<!-- ... -->` de VARIAS lineas se
  filtraba y el control no lo veia.
- **C-7, el check sin cablear.** Si `_comprobar_el_paso_de_publicacion` no
  estaba cableado en `validar()`, el check **no decia nada**: ni OK, ni FAIL,
  ni SKIP. Un validador mudo pasa por verde.
- **T-1.** La suite no vigilaba ninguno de los tres.

**EL ARREGLO.** El recorte es ahora **UNICO** y vive en el producto
(`validate_docs.py`, `_sin_la_capa_que_el_bucle_no_lee`): lo usan el check 12 Y
el guard de la regla de rama, que lo **llama** en vez de copiarlo (dos copias
de un recorte derivan, y aqui se derivaron: la copia del check 12 no via la
valla con `> `). Los controles del check 12 miden ahora la **valla con prefijo
de cita** y el **comentario de VARIAS lineas**, y se miden **con el mismo
recorte** que el cuerpo del check.

**EL GUARD** es la seccion (E) de la fila 130, con cinco cosas: el **cableado**
(con `ast`: una llamada, los cuatro argumentos explicitos, sin defaults, y el
recorte compartido), el **recorte** (medido sobre el del producto), la
**ausencia de `.agents/`** (el check CALLA sin `.agents/` y ACUSA con
`.agents/` y sin skill), el **recorrido real** (la skill REAL en el esqueleto,
el validador por SUBPROCESO: el check tiene que **decir algo**) y la
**contraprueba** (la ORDEN dentro de una valla con `> ` y de un comentario de
VARIAS lineas: el check tiene que **acusar**).

**MEDIDO en camara desechable (2026-10-22), los cuatro casos MUEREN:**

| Que se rompe | Por que muere el guard |
|---|---|
| el recorte deja de excluir la valla con prefijo `> ` (C-9) | la asercion del recorte lo dice por su nombre, y la contraprueba no ve la acusacion |
| el recorte deja de excluir el comentario de VARIAS lineas (C-6) | la asercion del recorte lo dice por su nombre, y la contraprueba no ve la acusacion |
| `validar()` deja de llamar al check 12 (C-7) | el `ast` ve **0** llamadas, y el check no dice NADA en el informe |
| el check calla en un arbol con `.agents/` y sin skill | el check tenia que acusar y no acuso |

**COSTE MEDIDO**: el test completo pasa de 31,9 s a **43,8 s**: las dos
corridas nuevas del validador sobre el esqueleto (la skill real y la
contraprueba) son ~9 s. El RECUENTO NO SE MUEVE (235 = 159 + 76): no hay
ningun `test_*` nuevo.

### El emisor no pisa la evidencia ajena

Emitir el veredicto de un mutante **no puede destruir** la evidencia
commiteada de los que no se le han pasado: el emisor escribe la evidencia
**solo** de los mutantes con corrida, y los demás conservan la que tenían
byte a byte. MEDIDO (auditoría del ciclo 70): antes, emitir el veredicto de
uno reescribía la evidencia del otro con «no hay ninguna corrida», y con el
mutante pisado declarado NO MEDIDO el gate no se enteraba (verde por omisión).
El mutante sin corridas sigue recibiendo su línea canónica (NO MEDIDO: sin
evidencia no hay veredicto), pero **sin** evidencia escrita: el gate exigirá
la evidencia commiteada y su ausencia es un FAIL, que es lo correcto.

### Por qué no se repite la suite N veces

Repetir cuesta **N × 734,9 s por mutante** (N=3 → **8,0 h por ciclo**), y
repetir **sin** exigir consistencia **empeora** el veredicto falso:
`1-(1-p)^N` con p=1/16 da 6,25 % (N=1) → **17,6 % (N=3)** → 27,5 % (N=5).
El killer-check cuesta **cero** corridas extra: el harness ya captura el log.
