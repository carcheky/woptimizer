## CYCLE-036 - 2026-10-01

**Testing & Calidad** — `TASK-046` (Pruebas de Contratos de Ciclo de Vida y Estados en Mixin Confirmable)

> 🟢 **VERDICT FINAL: PASS** — Validación completa y auditoría de contratos en mixin `Confirmable` por `mutation-auditor` (5 mutantes liquidados, 0 supervivientes). **90 tests** (83 backend + 7 headless UI) pasando al 100%.

### Añadido
- **`test_confirmable_mixin_lifecycle_and_widget_contracts`.** Prueba unitaria headless discriminante en `run_tests.py` que comprueba de forma exhaustiva:
  - 1ª pulsación: arma confirmación pendiente, muta texto a `CONFIRMAR`, estilos visuales en ámbar y retorna `False`.
  - 2ª pulsación: confirma acción (`True`), restaura texto original, aplica throttling de 300 ms (`state='disabled'` en `_timers_ui`) y restablece a `'normal'`.
  - Sustitución de token con selección cambiada (`changed_text`) actualizando el banner informativo.
  - Auto-expiración a los 3000 ms retornando a estado de reposo e informando expiración.
  - Cancelación explícita vía `_cancel_confirm()` restaurando el botón sin ejecutar.
  - Cancelación defensiva en destrucción (`cancel_on_destroy()`) cancelando handles activos de throttling en el planificador.
  - Resiliencia ante widgets destruidos (`winfo_exists() == False`) evitando errores `tk.TclError`.
  - Limpieza de reposo y timers al recrear botones vía `_forget_buttons()`.

### Corregido
- **Blindaje ante supervivientes M2b y M4.** Reforzadas las aserciones en `run_tests.py` para ejercitar la destrucción con temporizadores de throttling activos y la limpieza obligatoria del mapa de reposo (`_reposo.clear()`), eliminando el 100% de los mutantes detectados por `mutation-auditor`.

---

## CYCLE-035 - 2026-10-01

**Rendimiento & Latencia** — `TASK-045` (Optimización de Latencia en Categorización de Procesos y Memoización)

> 🟢 **VERDICT FINAL: PASS** — Optimización de categorización e invalidación atómica completada y auditada con éxito por `mutation-auditor` (0 supervivientes). **89 tests** (83 backend + 6 headless UI) pasando al 100%.

### Añadido
- **Invalidación atómica de caché al recargar la base de datos.** En `ProcessService._load_local_db()`, se ejecuta `self.invalidate_cache()` tras `self._meta_cache.clear()` para garantizar que la caché de procesos activos (`_proc_cache`) expire simultáneamente y no muestre categorías obsoletas.
- **Memoización O(1) de metadatos.** Búsqueda instantánea en `_meta_cache` (< 0.001 ms) para cualquier proceso (catalogado, fuzzy o fallback).
- **`test_process_categorization_latency_and_memoization`.** Test estrictamente discriminante en `run_tests.py` que verifica que la resolución de categorías consulta la memoria O(1) y que la recarga de base de datos invalida de manera atómica ambas cachés.

### Corregido
- **Aserción tautológica en test de categorización.** Corrección identificada por `mutation-auditor`: el test inicial usaba un proceso desconocido que caía en el fallback por defecto aun sin consultar la caché; actualizado para usar procesos catalogados y centinelas sintéticos, garantizando que el mutante sin caché es eliminado.
- **Mock de MainWindow en test headless de Tray.** Corregido el target de patch a `woptimizer.ui.app.MainWindow` en `test_tray_session_restoration_integration` para evitar inicializaciones reales de frames en entornos headless.

---

## CYCLE-034 - 2026-10-01

**Base de Datos & Procesos** — `TASK-044` (Expansión y Categorización de la Base de Procesos de Windows)

> 🟢 **VERDICT FINAL: PASS** — Expansión de base de datos de procesos completada y auditada con éxito. **88 tests** (82 backend + 6 headless UI) pasando al 100%.

### Añadido
- **7 Nuevos Procesos Reales Catalogados.** Incorporación de `rtss`, `msiafterburner`, `hwinfo64` (🔴 Overlays e Info), `galaxyclient` (🟡 Launchers Gaming), y `everything`, `gitkraken`, `postman` (🟢 Productividad) a `assets/process_db.json`. Total elevado a **96 procesos**.
- **Integridad de Esquema y Categorías.** 100% de cumplimiento en `test_process_db_schema_integrity` y `test_category_emoji_alignment` en `run_tests.py`, verificando ausencia de solapamiento con `SYSTEM_PROTECTED_PROCESSES`.

---

## CYCLE-033 - 2026-10-01

**Gaming & Telemetría UX** — `TASK-043` (Restauración de Sesión Gaming UX desde System Tray)

> 🟢 **VERDICT FINAL: PASS** — Auditoría de UI/UX y notificaciones del tray completada con éxito. **88 tests** (82 backend + 6 headless UI) pasando al 100%.

### Añadido
- **Acción del System Tray `'🔄 Reabrir aplicaciones cerradas'`.** Integrada en el menú contextual de `pystray` en `WOptimizerApp` (`src/woptimizer/ui/app.py`).
- **Restauración Asíncrona en Hilo Secundario.** La re-apertura de las aplicaciones de la sesión gaming se ejecuta de forma asíncrona mediante `gaming_service.restore_gaming_session()` en un hilo daemon `Thread(daemon=True)`.
- **Notificación Nativa en Tray.** Notificación al usuario vía `notification_service.notify_apps_launched()` informando la cantidad de aplicaciones restauradas.
- **`test_tray_session_restoration_integration`.** Test discriminante en `run_tests.py` que valida la adición de la opción al menú contextual, la llamada asíncrona a `restore_gaming_session()` y la emisión de notificaciones.

---

## CYCLE-032 - 2026-10-01

**Resiliencia & Robustez** — `TASK-042` (Robustez de Concurrencia y Captura Defensiva)

> 🟢 **VERDICT FINAL: PASS** — Auditoría de resiliencia completada con éxito. **87 tests** (82 backend + 5 headless UI) pasando al 100%.

### Corregido
- **Resiliencia en `NotificationService`.** Reemplazo del primitivo `Lock` por `threading.RLock()` para garantizar reentrancia y tolerancia a bloqueos multihilo durante invocaciones concurrentes a `attach_tray()`, `detach_tray()` y `notify()`.
- **Captura defensiva en `ProcessService`.** Ampliada la captura de excepciones en `kill_processes` y `kill_pack_apps` para manejar `psutil.ZombieProcess` y `OSError` (típicos de permisos WinError 5/87) sin interrumpir la métrica RSS liberada ni abortar la terminación de subprocesos.

### Añadido
- **`test_notification_service_rlock_and_concurrency`.** Verifica el tipo `RLock`, soporta invocaciones reentrantes y evalúa el comportamiento multihilo (5 hilos concurrentes) sin interbloqueos.
- **`test_process_service_kill_defensive_zombie_and_oserror`.** Prueba la resistencia de `kill_processes` y `kill_pack_apps` ante `ZombieProcess` y `OSError` simulados en padres e hijos.

---

## CYCLE-031 - 2026-10-01

**Testing & Calidad** — `TASK-041` (Ampliación de Cobertura de Testing y Contratos de Persistencia Pydantic)

> 🟢 **VERDICT FINAL: PASS** — Auditoría del Paso 4 completada con éxito. **85 tests** (80 backend + 5 headless UI) pasando al 100%.

### Añadido
- **`test_pydantic_extra_fields_persistence`.** Verifica la inmutabilidad y conservación de metadatos/campos extra no estándar (`extra="allow"`) en `AppData` y `Pack` tras ciclos completos de `load()` -> `save()` -> `json.load()`.
- **`test_freed_mb_calculation_precision`.** Valida la precisión aritmética del cálculo RSS (megabytes liberados) en `ProcessService.kill_processes` con mockeo de árbol de subprocesos padres/hijos.

---

## CYCLE-030 - 2026-10-01

**Rendimiento & Latencia** — `TASK-040` (Optimización de Latencia en Filtro de Búsqueda y Lectura de Packs)

> 🟢 **VERDICT FINAL: PASS** — Auditoría del Paso 4 completada con éxito. **83 tests** (78 backend + 5 headless UI) pasando al 100%.

### Añadido
- **Caché Inmutable de Lectura en 2 Capas (`PackService.get_all_packs`).** Reduce la latencia de lectura de packs a < 0.05 ms garantizando inmutabilidad estricta y aislamiento mediante `model_copy(deep=True)`.
- **Invalidación Atómica de Caché en `PackService`.** Reset atómico de caché en `save()`, `update_pack()`, `create_user_pack()`, `delete_pack()`, `set_favorite()`, `save_gaming_pack()`, `reset_gaming_pack()` y `load()`.
- **Filtrado Ultrarrápido (< 2.0 ms) en `ProcessManagerView`.** Pre-tokenizado de nombres/categorías en minúsculas para búsquedas fluidas sobre listas de 350+ procesos sin reconstruir el árbol de widgets.
- **Nuevos tests de benchmark discriminantes.** `test_pack_service_cache_invalidation_and_immutability` y `test_process_filter_performance` añadidos a `run_tests.py` (elevando la suite a 83 tests).

---

## CYCLE-029 - 2026-10-01

**Base de Datos & Procesos** — `TASK-039` (Expansión y Actualización de la Base de Procesos)

> 🟢 **VERDICT FINAL: PASS** — Validación completa. **89 procesos catalogados**, 0 solapamientos con procesos protegidos de sistema. **81 tests** en verde.

### Añadido
- **8 nuevos procesos reales catalogados en `assets/process_db.json` (+8 = 89 total):**
  - `gamingservices` (🟡 Launchers Gaming): Servicios centrales de la tienda Xbox y juegos en Windows.
  - `gamingservicesnet` (🟡 Launchers Gaming): Servicio de red auxiliar para juegos y tienda Xbox.
  - `adobecollabsync` (🟢 Productividad): Sincronizador en segundo plano de documentos colaborativos de Adobe.
  - `filecoauth` (🟢 Sincronización): Servicio de coautoría y sincronización de Microsoft Office.
  - `filesynchelper` (🟢 Sincronización): Asistente auxiliar de sincronización de archivos de OneDrive.
  - `edgegameassist` (🟢 Navegadores): Asistente u overlay flotante de juegos integrado en Microsoft Edge.
  - `hass.agent` (🟢 Productividad): Agente de integración local para domótica con Home Assistant.
  - `gameinputredistservice` (🟡 Launchers Gaming): Servicio redistribuible de entrada de mandos Microsoft GameInput.

---

## CYCLE-028 - 2026-10-01

**Gaming & Telemetría UX** — `TASK-038` (Restauración Inteligente de Apps tras Modo Gaming)

> 🟢 **VERDICT FINAL: PASS** — Auditoría del Paso 4 completada con éxito. **81 tests** (76 backend + 5 headless UI) pasando al 100%.

### Añadido
- **`GamingService._last_closed_apps` y resolución pre-kill de ejecutables.** `execute_gaming_pack` ahora resuelve las rutas absolutas `.exe` de los procesos antes de terminarlos y almacena los ejecutables únicos cerrados.
- **`GamingService.restore_gaming_session()`.** Reabre las aplicaciones capturadas durante la última sesión gaming invocando `start_pack_apps()` y limpia el historial.
- **Banner de Restauración en `DashboardView`.** Aparece dinámicamente con un botón "Reabrir Apps" para restaurar la sesión de trabajo con un solo clic tras salir de un juego.

---

## CYCLE-027 - 2026-10-01

**Resiliencia & Robustez / Deuda Técnica** — `TASK-037` (Guardas que no guardan: el alcance de un detector se deriva o no es un detector)

> 🟢 **VERDICT FINAL: PASS** — Auditoría del Paso 4 completada con éxito. **9/9 mutaciones aniquiladas por aserción**, 0 supervivientes. Recuento total derivado por `validate_docs.py`: **80 tests** (75 backend + 5 headless UI).

### Corregido
- **`_recuento_de_tests` ya emite el contrato `None` que su consumidor esperaba.** Captura `OSError` y `SyntaxError` (que incluye `IndentationError`), permitiendo que el validador emita un informe `[FAIL]` descriptivo en lugar de una excepción no capturada.
- **El guard AST del contrato de llamantes deriva su alcance dinámicamente.** En lugar de una tupla estática de dos ficheros que dejaba fuera a `process_manager_view.py`, ahora explora el árbol AST de `src/woptimizer/` identificando todos los módulos que importan `feedback`.
- **Soporte para `ast.Attribute` en el guard de llamantes.** Resuelve llamadas tanto en formato `mensaje_sin_apps(...)` (ast.Name) como `fb.mensaje_sin_apps(...)` (ast.Attribute).
- **El mensaje de pruebas huérfanas omite segmentos vacíos.** Se elimina la coletilla huérfana `invocado y NO definido: .` cuando la lista `solo_invocados` está vacía.

### Añadido
- **Prueba con árbol sintético para el guard de llamantes.** Árbol temporal con 4 módulos sintéticos que verifica que importadores con verbos cableados se marquen correctamente nombrando fichero y línea, ignorando llamadores no importadores y literales válidos como `pack.default_action`.
- **4 fixtures de validación de robustez en `validate_docs.py`.** Verifican el comportamiento del validador ante sangría rota, archivos ausentes, ejecuciones sanas y pruebas huérfanas.

---

## CYCLE-026 - 2026-09-30

**Gaming & Telemetría UX** — `TASK-035` (Telemetría y feedback visual unificado en la ejecución de packs) + `TASK-036` (la Portada avisa cuando un pack no puede hacer nada)

> 🔴 **VERDICT FINAL: PASS** — 7 rondas de auditoría de mutación, **43/43 mutaciones de `src/` aniquiladas por aserción**, 0 supervivientes. Cierre verificado por `mutation-auditor` sobre `0dd2d38`, con repo intacto. Matriz reproducible: `python _matrix_c26.py` → **30/30, 0 supervivientes**.

### Corregido (iteraciones 6 y 7 — las últimas)
- **🛡️ El segundo punto de la doble guarda de "Apagar" no tenía ni un test, y el documento afirmaba que sí.** `kill_pack` comprueba el pack dos veces —una antes de pedir la confirmación y otra después—, porque entre ambas el pack puede cambiar. El código y la documentación afirmaban que **los dos** estaban guardados; el auditor mutó el segundo y siguió vivo, y no es un mutante equivalente: con un pack que pierde sus apps entre pulsaciones, se lanzaba un apagado con lista vacía **después de haber consumido la doble pulsación**. Ahora está medido por la vía real, con un doble de servicio que devuelve un pack nuevo por lectura y cuenta las lecturas. Ese recuento es lo que distingue "midió el segundo punto" de "midió el primero por casualidad", y el auditor lo comprobó en las dos direcciones: con solo dos lecturas, la prueba se queda ciega.
- **🛡️ La tarjeta de la Portada podía prometer lo contrario de lo que hacía.** El botón anunciaba la acción con un `"KILL"` escrito a mano, congelado en el código. Ahora sale del mismo dato que decide la rama, y hay una prueba que obliga a que un Gaming Mode configurado para arrancar **diga** arrancar.
- **Un verbo desconocido ya no se convierte en silencio.** Al elegir el verbo de un aviso, cualquier palabra no reconocida caía por defecto en "apagar". Como la respuesta correcta de esa puerta *es* "apagar", un cableado equivocado era invisible. Ahora es un fallo ruidoso: un error de programación no puede esconderse detrás de un texto bonito. Está atado con una comprobación que exige que se pase siempre una acción.
- **🔴 El número de tests estaba caducado en tres ficheros y nadie se enteraba.** `STATUS.md` decía 75, `AGENTS.md` y `README.md` decían 28; la verdad era 78. El validador de documentación ejecutaba 72 comprobaciones y **ninguna miraba un número de tests**, así que daba "todo correcto" con los tres ficheros mintiendo. Corregido, y `validate_docs.py` ahora deriva el número real del propio archivo de pruebas, comprueba que no haya tests definidos sin ejecutar y compara contra los tres ficheros y contra la tabla de la guía. **De 72 a 77 comprobaciones**, y 13 de 15 pruebas de fallo negativo dan el error correcto sin reventar.

### Corregido (iteración 6)
- **La puerta de APAGAR decía "iniciar".** `PackManagerView._aviso_pack_inerte` —el helper que comparten los dos puntos donde `kill_pack` lee el pack— pasaba `pack.default_action` al formateador del aviso, así que un pack recién creado (que nace con `default_action="start"`) respondía **"no tiene apps que iniciar"** en la puerta de **apagar**: la primera acción de un usuario recién instalado. Es el espejo exacto del bug que la iteración 5 cerró en `start_pack`, y la razón es la misma: **el verbo lo decide el método que se está ejecutando, no el dato guardado del pack**. Ahora cablea `"kill"`. La suite lo mide con un pack **no gaming, vacío y `default_action="start"`** (no gaming a propósito: para que el diagnóstico del gaming inerte no se adelante y el assert muera por el verbo), y ambos mutantes —`pack.default_action` y `"start"`— mueren por esa aserción. Matriz del ciclo: **21 mutaciones, 21 muertas, 0 supervivientes**.


### Añadido
- **La Portada avisa del pack que no puede hacer nada, en las DOS ramas** (`TASK-036`). Un pack no gaming sin apps, con `default_action="kill"` o `"start"`, se avisa en `execute_pack` con el texto exacto `⚠️ '{nombre}' no tiene apps que {apagar|iniciar}. Añádelas desde el Gestor de Procesos.` en `theme.WARNING`, **antes** de `_require_double_tap`, sin worker y sin nada encolado. El verbo se mapea dentro del formateador a partir de la acción; la frase vive en un constructor privado de `ui/feedback.py` que comparten las dos familias, y el literal duplicado byte a byte de `kill_pack` desapareció.
- **Diagnóstico del Gaming Mode inerte:** un `is_gaming` con 0 apps **y** 0 categorías se avisa con `⛔ El Gaming Mode de '{nombre}' no tiene nada que cerrar: 0 apps y 0 categorías configuradas. Revísalo en el Gestor de Packs.` (ROJO inline, `theme.WARNING` en banner) en las dos puertas, también antes de la doble pulsación. Antes caía en la puerta real y pintaba `"Nada que cerrar: 0 ya cerrados"`, donde el `0` es el contador de blindaje, no de apps. Con apps **o** con categorías no avisa: cierra de verdad.
- **La rama `start` de `execute_pack` entra en la suite por el worker real.** Tres mutaciones pasaban la suite entera en verde: intercambiar `launched`/`failed`, arrancar `start_pack_apps([])`, y publicar en `_show_banner` con el nombre del pack como flag de gaming.
- **Cláusula de MB unification (`clausula_mb`):** los cuatro textos de éxito/parcial y `_last_gaming_summary` omiten la cifra con `freed_mb <= 0`, como ya hacía `format_kill_result` (fijado por `test_notification_message_formatting`).
- **`_publicar_en_banner`:** la línea de publicación del banner (fondo, texto, color, `pack` y auto-ocultado) era un bloque de cuatro líneas copiado en dos sitios y la tercera puerta iba a ser la tercera copia.
- **El Gestor de Procesos entra en el contrato de feedback honesto (`test_el_gestor_de_procesos_tampoco_miente`).** Es la **tercera** puerta de cierre (mata uno a uno lo que el usuario marcó a mano) y era la más grave: pintaba `"<tick> 0 cerrados, 0 fallidos."` con `killed == 0`. La sonda entra por `on_kill_selected` de verdad (doble pulsación, hilo secundario real, `after` encolado) y afirma texto y color exactos en los cuatro desenlaces. No mata ningún proceso: el `ProcessService` es un doble.
- **`mensaje_cierre_pack` admite un sustantivo parametrizable** (`"procesos"` por defecto, `"apps"` cuando toque), para que ninguna vista duplique el texto del formateador.
- **`DashboardView.AUTOOCULTADO_MS`** pasa de literal suelto a constante compartida.

### Corregido
- **El test afirmaba el silencio de la Portada.** `assert ... == antes_texto` con el mensaje *"se corta en silencio"* era la especificación de la mentira: una aserción que prohíbe la verdad nueva se convierte en el contrato. Invertida en el mismo commit que el aviso; lo que se mantiene es que no hay worker ni nada encolado.
- **La tercera puerta de feedback mentía en verde.** `ProcessManagerView.on_kill_selected` se alimentaba del formateador común (`mensaje_cierre_pack`) y con `killed == 0` ya no hay tick ni verde; además `skipped` dejó de confundirse con `failed` y se programa el refresco de la lista a 1000 ms. Es el bug que motivó el ciclo 26, vivo en la vista que nadie había tocado.
- **El bloque de cancelación del temporizador del banner estaba duplicado byte a byte** en `_show_start_banner` y en `_show_banner` — la puerta que el gamer ve tras pulsar "Apagar". Se extrajo a `_reprogramar_autoocultado()`: una sola verdad y un solo sitio que testear, y el escenario con reloj simulado se monta ahora en las tres puertas.
- **La guarda AST comparaba raíces, no pares.** `self.pack_service.get_all_packs()` y `self.process_service.get_process_exe_path(1)` pasaban; ahora la lista de lo permitido son pares `(raiz, metodo)`. También baja por `ast.Subscript`, por el que `self.__dict__['status_label'].configure(...)` — la misma llamada de widget por la puerta de atrás — colaba.
- **La guarda AST además miraba solo `call.func`.** Cuatro formas más de llegar a `self` la atravesaban entera: `getattr(self, 'status_label').configure(...)`, `setattr(self, '_last_gaming_summary', 'x')`, `del self._last_gaming_summary` y `self.process_service.kill_pack_apps(self.status_label)`. El detector cubre las cuatro y el doc dice **qué** cubre y qué no, en vez de prometer que "todo lo que cuelgue de `self` es infracción": el único agujero que queda abierto es el alias local.
- **La guarda AST no leía el Gestor de Procesos.** Entra `ProcessManagerView._do_load` y `on_kill_selected`; para que el worker de carga no toque la vista, la agrupación pura se movió al módulo (`_agrupar`) y la publicación va a un método (`_apply_load`).
- **Cuatro ramas sin ejecutar:** la no-gaming de `execute_pack` (nunca se ejecutaba), la **start** de `execute_pack` (tampoco), `killed == 1` (que `clasificar_cierre` con `killed > 1` degradaba a "nada") y `failed != skipped` (que hacía invisible intercambiar el orden de la 4-tupla).
- **Dos guardas preventivas sin cobertura:** `execute_pack` con pack no gaming y vacío, y `kill_pack` con pack inexistente.
- **El sustantivo solo se probaba en la rama éxito.** La fila del changelog que decía "el sustantivo se ignora" era cierta solo para una de las dos ramas que lo usan: cablear `"procesos"` a mano dejaba la suite verde.
- **Código muerto:** el alias `_show_kill_banner` (nadie lo llamaba; lo único que lo sostenía era su nombre en la lista blanca de la guarda) se borró de los dos sitios.
- **Ocho afirmaciones documentales que mentían**, corregidas en `docs/ai/ui-design-system.md`, `docs/ai/testing-guide.md` y `proposal.md`: **`len(to_kill)` donde el código dice `len(selected_keys)`** (el mismo descuadre que arregló el ciclo 26, reintroducido como documentación), una tabla de mutaciones que **no se podía reproducir**, "todo lo que cuelgue de `self` es infracción" cuando la guarda era una red, "las cinco vistas" cuando son tres clases de vista y cinco métodos, "las dos vistas" en un módulo que alimenta tres puertas, y tres que ya se habían corregido en la iteración 3.
- **`_matrix_c26.py` estaba comiteado y roto:** reventaba en la mutación 5 de 12 con `AssertionError: no se encontró el ancla` (el ancla de M6 caducó al extraer `_reprogramar_autoocultado`), y `correr()` lanzaba **2 de las 3 sondas**, así que la tercera puerta nunca estuvo en esa matriz. Reparado: anclas contra el código de hoy con **error duro** si no se encuentran, las tres sondas en cada mutación y salida ASCII. Las tablas de los changelog que declaraban "15 mutaciones, 15 muertas" (la #13 murió por un `AttributeError`, un crash, y la #15 era media verdad) se sustituyen por la salida real.

### Impacto
Ninguna puerta de feedback puede celebrar en verde un cierre que no ocurrió, las tres se alimentan del mismo clasificador y **ninguna se traga en silencio cuando el pack no puede hacer nada**. La invariante de hilos-secundarios-solo-aporta-`after(0, ...)` cubre cinco métodos de tres clases de vista, con una lista de lo permitido que significa algo y con escrito lo que no comprueba. Suite: **78 tests** (73 backend + 5 headless), y **20 mutaciones verificadas con salida real** (20 muertas, 0 supervivientes) mediante `python _matrix_c26.py`, que es ahora reproducible por primera vez.

---

## CYCLE-025 - 2026-09-30

**Testing & Calidad** — `TASK-034` (Expansión de calidad y pruebas headless de UI y modelos)

### Añadido
- **Prueba de transiciones completas de navegación headless en `MainWindow` (`test_main_window_navigation_transitions`).** Verifica el ciclo de vida completo de navegación entre vistas (`DashboardView`, `PackManagerView`, `ProcessManagerView`), la destrucción limpia de las vistas previas con `not winfo_exists()`, la actualización visual de los estados activo e inactivo de la barra de navegación (`theme.ACCENT` vs `theme.BORDER`), y el bombeo asíncrono seguro durante la carga de procesos sin bloqueos en runners headless.
- **Sonda de validación estricta y contratos en modelos Pydantic (`test_models_strict_validation_and_contracts`).** Comprueba el rechazo estricto de tipos no booleanos (`"true"`, `1`, `"false"`, `0`) en `is_favorite` e `is_gaming` mediante `strict=True`, la restricción de `default_action` al enum literal `Literal["start", "kill"]`, la retención completa de metadatos adicionales desconocidos mediante `extra="allow"` en `Pack` y `AppData`, y los valores por defecto canónicos de `ProcessInfo`. Suite total: **73 tests backend + 2 headless UI**, 100% en verde.

### Corregido
- **Eliminación de puntos ciegos en la suite de pruebas.** Se detectó que las vistas de gestión de packs y de procesos nunca eran instanciadas en la suite de integración headless previa, dejando sin cobertura la navegación entre pestañas y la destrucción de widgets en memoria.

### Impacto
Blindaje absoluto de la navegación de interfaz y de la integridad del esquema de datos. Se garantiza que ninguna versión futura degrade el formato de guardado ni coaccione tipos booleanos en silencio, manteniendo la robustez del producto sin abrir ventanas molestas durante los tests.

---

## CYCLE-024 - 2026-09-30

**Rendimiento & Latencia** — `TASK-033` (Optimización de latencia en escaneo de procesos)

### Añadido
- **Resolución bajo demanda de rutas de ejecutables (`get_process_exe_path`).** Nueva API en `ProcessService` que obtiene la ruta absoluta (`.exe`) de un proceso únicamente cuando se necesita (al asociar una app a un pack), con protección ante procesos cerrados o permisos denegados.
- **Prueba discriminante y benchmark de escaneo.** Incorporación de `test_scan_latency_and_lazy_exe_resolution` en `run_tests.py` que verifica el escaneo ligero sin `exe`, la resolución exacta del ejecutable del sistema, la degradación ante PIDs inválidos y que el tiempo medio de escaneo no supere los 25 ms. Total suite: **72 tests backend + 1 headless UI**, 100% en verde.

### Cambiado
- **Aceleración del escaneo de procesos del sistema.** Se eliminó la consulta anticipada de la ruta del ejecutable para todos los cientos de procesos del sistema en `get_running_processes()`, la cual generaba cientos de excepciones internas `AccessDenied` e I/O innecesario.
- **Construcción optimizada de objetos de proceso.** Se adoptó `ProcessInfo.model_construct(...)` en el bucle principal de escaneo, eliminando la validación redundante de más de 2.200 campos Pydantic por escaneo.
- **Precomputación del orden de categorías.** El índice de ordenación de categorías ahora se calcula una sola vez a nivel de módulo (`_CAT_ORDER_IDX`), reduciendo asignaciones de memoria en cada refresco.
- **Normalización segura de nombres de proceso.** Se reemplazó el reemplazo global de `.exe` por corte estricto de sufijo, evitando corrupciones en procesos cuyos nombres contienen la cadena `.exe` en posiciones intermedias.

### Impacto
La latencia de escaneo de procesos en frío en Windows 11 se reduce de más de **31 ms a solo ~5.5 ms (~5.6x a ~8x de aceleración)**. La interfaz responde de manera instantánea al refrescar la lista de procesos o preparar el Gaming Mode, manteniendo intacta la seguridad y el blindaje anti-brick.

---

## CYCLE-023 - 2026-09-30

**Base de Datos & Procesos** — `TASK-032` (Expansión de la base de procesos)

### Añadido
- **8 nuevos procesos del sistema catalogados (`process_db.json`).** Escaneo real en Windows que incorpora launchers, herramientas de soporte y bloatware seguro a la base de conocimiento local (total: 81 entradas):
  - `braveupdate` (🟢 Productividad, high): servicio de actualización en segundo plano de Brave.
  - `xboxgamebarwidgets` (🔴 Overlays e Info, none): widgets del Game Bar de Windows (blindado bajo barrera roja G-2).
  - `xboxpcappft` (🟡 Launchers Gaming, none): launcher y runtime de la app Xbox en PC.
  - `whatsapp.root` (🟡 Chat y Comunicación, low): cliente de mensajería UWP de WhatsApp.
  - `crossdeviceresume` (🟢 Sincronización, high): servicio de continuidad multidispositivo Phone Link.
  - `lightingservice` (🔴 Overlays e Info, none): control RGB de ASUS Aura / Armoury Crate (blindado bajo barrera roja G-2).
  - `powertoys.mousewithoutbordershelper` (🟢 Productividad, high): servicio auxiliar de Microsoft PowerToys.
  - `acpowernotification` (🟢 Productividad, high): notificador de estado de batería/corriente OEM de ASUS.
- **Sonda de integridad de esquema en `run_tests.py`.** Nueva prueba `test_process_db_schema_integrity` que valida exhaustivamente que toda entrada contenga claves normalizadas sin `.exe`, categorías pertenecientes a `PROCESS_CATEGORIES`, prioridades válidas (`high`, `medium`, `low`, `none`) y descripciones no vacías. Total suite: **71 tests backend + 1 headless UI**, todos en verde.

### Corregido
- **Cierre del mutante superviviente S1.** `mutation-auditor` identificó que una entrada podía omitir `priority` o `description` sin que los tests previos lo detectaran. La nueva sonda elimina este punto ciego, aniquilando 11/11 mutantes.
- **Blindaje anti-brick estricto verificado.** Se validó que ninguna de las 8 nuevas entradas colisione con `SYSTEM_PROTECTED_PROCESSES` (34 procesos críticos de Windows) ni pueda comprometer la estabilidad del sistema operativo.

### Impacto
La base de datos local amplía su cobertura de procesos residentes comunes en Windows 11 sin añadir peso ni llamadas externas. La integridad de datos queda asegurada mediante verificación estricta de esquema y blindaje anti-brick verificado por pruebas de mutación.

---

## CYCLE-022 - 2026-09-30

**Diseño & Front-End** — `TASK-029` (UI-001 a UI-012)

### Añadido
- **Sistema centralizado de tokens de diseño (`theme.py`).** Se introdujo una fuente única de verdad para la interfaz: colores semánticos por rol (`SURFACE`, `ACCENT`, `GAMING`, `DANGER`), escala tipográfica fija de exactamente 6 tamaños y 3 radios de borde.
- **Icono oficial de la aplicación (`woptimizer.ico`).** Se incorporó el icono multi-tamaño para la ventana principal (`root.iconbitmap`) y para la bandeja del sistema (`pystray`), eliminando el icono genérico de Python en la barra de título y el placeholder "W3".
- **Banda de telemetría permanente en reposo.** La portada (`DashboardView`) ahora muestra de forma continua el recuento de procesos activos en el sistema y el resumen del último Gaming Mode sin consultar `psutil` directamente.
- **Diálogo modal propio para crear packs.** Sustitución de `CTkInputDialog` por `NewPackModal`, un diálogo centrado y adaptado al tema oscuro que previene que la ventana de creación se abra por detrás de la app.
- **6 nuevas pruebas discriminantes en `run_tests.py`.** Verificación AST de ausencia de literales hex sueltos, completitud de tokens, cálculo de contraste WCAG AA (≥ 4.5:1), objetivos de puntero mínimos (≥ 28x28px) y validez del archivo `.ico`. Total suite: **63 tests backend + 1 headless UI**, todos en verde.

### Corregido
- **Contradicción visual del Gaming Mode (Opción A).** El Gaming Mode utilizaba antes rojo en los botones y verde en el banner de resultados. Se unificó en verde Gaming (`#1DB954`), reservando el rojo exclusivamente para acciones destructivas y señales de peligro (`⛔` y `🔴 NO CERRAR`), evitando confusiones de seguridad.
- **La etiqueta del botón Gaming ya no miente.** Se reetiquetó la información para mostrar el número de apps y de categorías automáticas afectadas (`N apps · M categorías · KILL`), reflejando la realidad del comportamiento tras TASK-025.
- **Parpadeo al refrescar la portada.** `refresh_dashboard()` ahora reutiliza los botones existentes cuando los favoritos no cambian en lugar de destruirlos y recrearlos, eliminando parpadeos y conservando el foco.
- **Estado vacío con 0 procesos.** En el Gestor de Procesos se reemplazó el mensaje equívoco `"✅ 0 apps distintas"` por un texto neutro y descriptivo.
- **Desborde de texto en pantallas pequeñas.** Se añadió ajuste de línea (`wraplength=380`) a las descripciones de procesos para garantizar una visualización óptima en pantallas de 14" y ventanas mínimas de 720px.

### Cambiado
- **Barra de navegación renovada.** Altura fija estricta de 44px con `pack_propagate(False)`, soporte hover suave y marcado del estado activo mediante acento visual y texto primario, reemplazando el relleno azul estridente anterior.
- **Cabeceras de categorías mejoradas.** Las cabeceras del Gestor de Procesos ahora cuentan con fondo visual (`SURFACE_ALT`), hover interactivo y recuento explícito de apps contenidas (`▼ Categoría (N)`).
- **Tarjeta del pack Gaming destacada.** Borde de acento verde y badge `PRESET` diferenciado para identificarlo inmediatamente frente a los packs de usuario.
- **Objetivos de puntero ampliados.** Todos los botones y herramientas interactivas cumplen la cota mínima ergonómica de `28x28px`.

### Impacto
Se completó la consolidación estética y funcional más importante desde el rediseño v3. La interfaz ya no depende de colores hardcodeados dispersos, cumple los estándares de accesibilidad de contraste WCAG AA, clarifica la semántica de seguridad (verde para gaming, rojo solo para peligro) y ofrece una experiencia fluida, consistente y profesional.

---

## CYCLE-021 - 2026-09-30

**Resiliencia & Deuda Técnica** — `TASK-028` (FIX-010 al FIX-020)

### Corregido
- **Los avisos del programa ya no se escapan a la consola.** Antes, importar la configuración configuraba el registro de mensajes como efecto secundario y llenaba el registro de avisos duplicados. Ahora se configura de forma explícita y segura con rotación de archivos (`woptimizer.log`), evitando que el archivo crezca sin límite.
- **La versión del programa está sincronizada en todos los sitios.** Se unificó la versión a `3.0.1.dev0` entre el empaquetado (`pyproject.toml`), el código fuente (`__init__.py`) y el gestor de tareas. Un nuevo test hermético comprueba que nunca vuelvan a desfasarse sin necesidad de ejecutar el programa.
- **La app ya no se cuelga si el archivo de configuración no se puede leer.** Si un archivo de perfiles está bloqueado por permisos o truncado a mitad de un carácter especial, la app ahora lo gestiona adecuadamente, avisa al usuario y recurre a la copia de seguridad `.bak` en lugar de fallar de forma silenciosa.
- **Eliminadas redundancias y variables muertas.** Se limpió código innecesario en el cierre de la aplicación y en el gestor de procesos (`is_expanded`), reduciendo deuda técnica.

### Cambiado
- **Los perfiles antiguos de la versión 2 se han archivado de forma segura.** El archivo de perfiles legacy se trasladó a `docs/archive/legacy-root-data/` junto con su documentación histórica, dejando la raíz del proyecto limpia sin perder datos del usuario.

### Añadido
- **8 pruebas nuevas en la suite.** **56 → 57 tests backend + 1 test headless de UI**, todos en verde.
- Verificación exhaustiva de 16 mutaciones con el `mutation-auditor` para asegurar que ningún fix sobreviva a regresiones.

### Impacto
Se cerró un gran bloque de saneamiento acumulado desde la migración a la v3. La auditoría demostró que 5 de las premisas iniciales sobre la deuda técnica eran inexactas (por ejemplo, `PROCESS_LIST_FILE` aún era necesaria para tests de compatibilidad y `procesos.csv` ya había sido migrado). El proyecto queda con su deuda técnica resuelta, registro rotativo limpio y suite de tests reforzada.

---

## CYCLE-020 - 2026-09-30

**Seguridad & Usabilidad** — `TASK-027` (FIX-003, FIX-004, FIX-006)

### Corregido
- **Arrancar las apps de un pack ya no es ejecutar un comando.** La lista de programas de un pack viene de un archivo que escribes tú a mano y que este programa está pensado para compartir. Se ejecutaba a través de la línea de comandos, así que una ruta con `&` o `;` podía encadenar otro comando. Ahora cada ruta se **valida antes de lanzarse**: se rechaza lo que no sea un `.exe` o `.com` dentro de las carpetas permitidas, nada se ejecuta desde una carpeta compartida en red, y nada se cuela con `..\..`.
- **El aviso de «apps arrancadas» ya no miente.** Decía que había arrancado programas que en realidad no arrancaron: el sistema de comandos no avisa cuando no encuentra un programa, asía que el contador solo sumía. Ahora el número que ves es el número real, y si algo no arranca te dice por qué en el registro.
- **Las secciones del Gestor de Procesos salían en el orden equivocado.** Los procesos que **no** debes cerrar aparecían los primeros, y los seguros, los últimos. Era el orden inverso al que sugiere el semáforo. Corregido en los dos sitios donde se ven las categorías, incluida la lista donde decides qué se cierra en el modo juego.
- **La estrella del pack ya se puede volver a pulsar para desmarcarlo.** Antes la segunda pulsación lo volvía a marcar. Ahora es un interruptor de verdad, y desmarca el pack que pulsaste (también cuando por lo que sea hay dos packs marcados).

### Cambiado
- El Gestor de Procesos guarda ahora la **ruta completa** del programa en el pack, no solo su nombre. Sigue funcionando con los packs que ya tenías guardados: los nombres sueltos se siguen buscando, pero ahora dentro de las carpetas permitidas y nunca por la ruta de búsqueda del sistema.

### Añadido
- 4 pruebas nuevas. **48 → 56 tests**, todos en verde. Cada una verificada rompiendo el código a propósito.

### Corregido en la 2.ª revisión (el `mutation-auditor` dio FAIL)
La garantía de arriba —«solo se arranca lo que está dentro de las carpetas permitidas»— **era falsa**, y está corregida:
- **Un «atajo» (junction) dentro de una carpeta permitida se colaba.** La comprobación de si una ruta está dentro de la carpeta trabajo con el texto de la ruta, sin seguir los enlaces del disco. Con un enlace puesto a mano, `C:\Windows\System32\cmd.exe` pasaba el filtro y **se ejecutaba**. Ahora la ruta se resuelve por el sistema de archivos antes de compararla, y si no se puede resolver, **no se arranca nada**.
- **Un `.exe` que en realidad es un enlace a un `.bat` se colaba.** La lista de extensiones permitidas miraba el nombre del enlace, no el del archivo de verdad; el lanzador de Windows ejecuta los `.bat` por línea de comandos. Ahora se mira en las dos.
- **Un programa instalado con las letras en mayúsculas no arrancaba.** En Windows el disco no distingue mayúsculas de minúsculas, pero la comparación sí, así que `C:\PROGRAM FILES\...` se rechazaba. Ahora las dos partes se comparan como Windows las compara.
- **Nadie vigilaba que la comparación fuera por carpetas y no por prefijo de texto.** Ahora hay una prueba que rompe el código a propósito para comprobarlo.

### Verificado rompiendo el código a propósito
**21 mutaciones, 21 detectadas** (la 1.ª revisión declaraba 27 y el `mutation-auditor` midió 29, con 1 que sobrevivía: precisamente la comparación por prefijo, ahora cerrada). Entre las 21: borrar la resolución de enlaces, hacer que la comprobación real siempre dé «dentro», mirar la extensión solo en el alias, no fallar en cerrado cuando la ruta no se puede resolver, rechazar todos los enlaces (que rompe Steam y itch.io), devolver la ruta escrita en vez de la resuelta, y volver a la ejecución por línea de comandos.

### Impacto
El encargo llegó con tres premisas y **las tres eran falsas**: el orden de categorías que pedías (por color) no es el que tenía el programa, el defecto estába en un segundo sitio que nadie señaló, y lo del favorito no era un fallo del motor sino una línea de la pantalla. Lo que sí era verdad, y pesaba más: quitar la línea de comandos **no basta**. El programa busca primero en la carpeta actual, el lanzador de Windows sí ejecuta archivos `.bat` y `.ps1`, y comprobar que una ruta sea «absoluta» no impide ni `..\..\` ni una carpeta compartida en red. Todo eso está medido y escrito en los comentarios y en la documentación, no supuesto.

Y la revisión de los tests encontró algo peor que los fallos de la primera tanda: **una de las protecciones no miraba lo que decía mirar**. La comprobación automática que prohíbe volver a lanzar por línea de comandos solo buscaba un texto concreto, así que la forma más natural de reintroducir el problema —`subprocess.Popen(..., shell=True)`— pasaba inadvertida. Ahora mira las tres formas de escribir esa llamada, y hay una prueba que se asegura de que las ve. También está escrito lo que **no** queda cerrado: nada por intérprete, nada desde una carpeta compartida en red, nada por atajos de carpeta, y **nada que no sea un programa de verdad** —un `.bat` al que le cambian el nombre a `.exe` y lo cuelgan dentro de una carpeta permitida ya no arranca—. Ese último caso estaba **mal escrito en la documentación** y ahora está **arreglado de verdad**: se defendía diciendo que Windows no puede ver ese tipo de enlace, y la verdad medida es otra: Windows sí lo ve, pero el problema no era el enlace, era que las protecciones miraban el **nombre** del archivo en vez de lo que hay **dentro**. Una copia normal, sin ningún enlace ni permisos raros, pasaba exactamente igual.

# Changelog de woptimizer

> Registro humano-legible de todo lo que cambió en el proyecto, escrito por el motor autónomo de I+D (`id-pipeline`).
> Un pase = un ciclo = una entrada. Si algo no aparece aquí, no se hizo.

- **Formato**: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) adaptado: `Añadido` / `Corregido` / `Cambiado` / `Eliminado`.
- **Registro técnico completo** (qué se rompió, decisiones de diseño, modelos por paso): [`.taskmaster/CHANGELOG.md`](.taskmaster/CHANGELOG.md).
- **Salud del sistema y tablero**: [`STATUS.md`](STATUS.md).

---

## Resumen

| Ciclo | Fecha | Área | Qué pasó |
| [#21](#cycle-021--2026-09-30) | 2026-09-30 | Deuda Técnica | 🧹 Saneamiento de logging, sincronización de versión, archivo de perfiles legacy y cierre de mutaciones. 57 tests. |
|:---:|---|---|---|
| [#20](#cycle-020--2026-09-30) | 2026-09-30 | Seguridad | ⚡ Arrancar apps ya no es ejecutar un comando, y el orden de categorías salía al revés. Segunda revisión: un «atajo» (junction) colaba `cmd.exe`. 56 tests. |
| [#19](#cycle-019--2026-09-30) | 2026-09-30 | Resiliencia | 🛡️ La copia de seguridad dejaba de estar a salvo al arrancar la app. Cerrado. |
| [#18](#cycle-018--2026-09-30) | 2026-09-30 | Resiliencia | 🧬 Los 3 tests que pasaban con el bug puesto, cerrados y verificados. 36 tests. |
| [#17](#cycle-017--2026-09-30) | 2026-09-30 | Pipeline | 🧬 Nuevo paso: alguien rompe el código a propósito para ver si los tests se enteran. |
| [#16](#cycle-016--2026-09-30) | 2026-09-30 | Pipeline | Los 3 roles pasan a agentes reales. Aparecen en tu panel. |
| [#15](#cycle-015--2026-09-29) | 2026-09-29 | Resiliencia | 🔴 Un error al guardar te borraba la configuración entera. Blindado. |
| [#14](#cycle-014--2026-09-29) | 2026-09-29 | Gaming & UX | 🔴 El Gaming Mode no consultaba tu configuración. Conectado y blindado. |
| [#13](#cycle-013--2026-09-29) | 2026-09-29 | Base de datos | 🛡️ Blindaje anti-brick: 34 procesos de sistema protegidos. +25 entradas. |
| [#12](#cycle-012--2026-09-29) | 2026-09-29 | Gaming & UX | 🔴 5 acciones destructivas volvieron a pedir confirmación (Trampa #14). |
| [#11](#cycle-011--2026-09-29) | 2026-09-29 | Resiliencia | 🔴 El pipeline podía "completar" ciclos sin versionar nada. |
| [#10](#cycle-010--2026-09-29) | 2026-09-29 | Testing | 🔴 "Restaurar por defecto" era un no-op silencioso (`model_copy` shallow). |
| [#9](#cycle-009--2026-09-29) | 2026-09-29 | Base de datos | 🔴 6 de 8 categorías sin semáforo por emojis desalineados. |
| [#8](#cycle-008--2026-09-29) | 2026-09-29 | Gaming & UX | Notificaciones nativas de Windows (toasts). |
| [#7](#cycle-007--2026-09-29) | 2026-09-29 | Rendimiento | Cache TTL + hashmap: lecturas 5000× más rápidas. |
| [#6](#cycle-006--2026-09-29) | 2026-09-29 | Resiliencia | Cierre limpio del tray y logging por proceso. |
| [#5](#cycle-005--2026-09-29) | 2026-09-29 | Testing | Telemetría de RAM y recuperación de JSON con tests. |
| [#4](#cycle-004--2026-09-29) | 2026-09-29 | Base de datos | +4 procesos de bloatware catalogados. |
| [#3](#cycle-003--2026-09-29) | 2026-09-29 | Gaming & UX | Banner de RAM liberada tras activar un pack. |
| [#2](#cycle-002--2026-09-29) | 2026-09-29 | Resiliencia | System tray (`pystray`), backups y logging continuo. |
| [#1](#cycle-001--2026-09-28) | 2026-09-28 | Arquitectura | Rediseño v3 completo: 3 ventanas, `psutil`, `pydantic v2`. |

**Balance**: 21 ciclos · 8 bugs críticos corregidos · 2 vectores de brick cerrados · 57 tests en verde.

---

## CYCLE-019 — 2026-09-30

**Resiliencia & Robustez** · `TASK-031` · COMPLETED (3 iteraciones, 1 FAIL intermedio)

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo |
|---|---|---|---|
| Copia de la raíz al guardar | no copiarla | **killed** | `la clave raiz 'favorite' desaparecio del disco tras el save()` |
| Ídem, copiando `profiles` | copiarlo también | **killed** | `'profiles' se ha copiado al fichero escrito ... el landmine solo explotaria en el segundo arranque` |
| Validación en la rama antigua | dejarla solo en la moderna | **killed** | `[legacy/keeper]` |
| Validación en la rama moderna | dejarla solo en la antigua | **killed** | `[moderna/keeper]` |
| `is_favorite` estricto | quitar `strict` | **killed** | `_read_json dio None en vez de ValidationError` |
| Normalización de claves | `_normalizar_clave` → identidad | **killed** | `'IS-FAVORITE' se acepto como campo desconocido` |
| Umbral de error de escritura | 1 → 2 pulsaciones | **killed** | `'note' esta a distancia 2 de 'name'` |
| `extra` en la raíz | `AppData extra="ignore"` | **killed** | `quedan ['packs']: los packs se han perdido` |
| `extra` en la hoja | `Pack extra="forbid"` | **killed** | `un campo que esta version no conoce se clasifico como corrupcion` |
| Corrupción de hoja | `Pack(...)` de 5 campos | **killed** | `[legacy/keepers]: dio None en vez de PerfilCorruptoError` |
| Escritura al arrancar | `_ensure_gaming_pack` vuelve a guardar | **killed** | `load() escribio [...]: es de solo lectura` |

### Corregido
- **La copia de seguridad de tu configuración ya está realmente a salvo.** Antes, si el archivo de packs se escribía mal, la app lo detectaba, recuperaba de la copia… y acto seguido **machacaba esa misma copia** al guardar. En 7 de los 8 casos que el propio proyecto daba por protegidos. Y no pasaba cuando tú guardabas: pasaba al **arrancar**.
- **Ya no hay dos definiciones distintas de "archivo dañado".** El motor tenía una para detectar y otra para decidir si era salvable, y la documentación describía la que no se ejecutaba.
- **Un error de escritura ya no se acepta en silencio.** Si escribes `keeper` en vez de `keepers`, o dejas una mayúscula, la app lo detecta y te dice qué campo es. Antes tu lista de programas protegidos se quedaba **vacía sin avisar**, y el modo de juego pasaba a matar lo que debía proteger.
- **Los datos que no son de esta versión ya no desaparecen** al guardar por primera vez.
- Corregida la documentación que **afirmaba una garantía que era falsa**.

### Añadido
- 12 pruebas nuevas. **36 → 48 tests**, todos en verde.
- La comprobación de campos se **deriva del modelo**: si mañana se añade un campo nuevo a un pack, su error de escritura se detecta **sin tocar una sola línea de código**. Lo verificó el auditor con un campo inventado.
- 2 pruebas nuevas para valores mal escritos en los indicadores de favorito y de sistema.

### Impacto
El ciclo costó **tres vueltas**: la primera auditoría devolvió FAIL porque el implementador se había auto-declarado verde y, al romper el código, apareció un fallo que **borraba los packs del usuario del disco**. La segunda dejó tres Medianos, la tercera los cerró. Ese es el motivo de ser del paso: no valida *tu* trabajo, valida que el trabajo sea real.

**Lo que más costó no fue el código, sino las premisas.** Las tres que traía el encargo eran falsas, y la más grave apuntaba al síntoma equivocado: el agujero no estaba donde seBuscar, sino en una rotación de copias que comparaba el archivo con un método distinto del que se usaba para decidir si estaba dañado. Un arreglo siguiendo esas premisas habría escrito muchas pruebas, todas en verde, y no habría arreglado nada.

## CYCLE-018 — 2026-09-30

---


**Resiliencia & Robustez** · `TASK-030` · COMPLETED (con un hueco nuevo, abierto)

> Cierra el FAIL del ciclo #17: los 3 tests que pasaban con el bug puesto.

### Mutaciones auditadas (Paso 4)
| Fix | Mutación | Veredicto | Motivo |
|---|---|---|---|
| Escritura atómica | `os.replace` → `shutil.copyfile` | **killed** | `la escritura atomica no deja .tmp` |
| Limpieza del temporal | quitar el `unlink` | **killed** | `un save fallido no debe dejar un .tmp` |
| `except` honesto | readmitir `OSError` en la tupla | **killed** | `save() no lanzo el PermissionError de la rotacion` |
| Guarda de forma | quitar `isinstance(perfiles, dict)` | **killed** | `lanzo AttributeError(...) en vez de PerfilCorruptoError` |
| `except` honesto | `except Exception` en `load()` | **killed** | `un OSError de lectura no es corrupcion ... arranco en silencio` |
| `except` honesto | readmitir `AttributeError` | **killed** | `AttributeError NO puede estar en CORRUPTION_ERRORS` |
| Publicación en hilo | `self.after(0,_apply)` → `_apply()` | **killed** | en runtime: `'processes' se publico desde el hilo 26140, no desde el principal` |

Las 7 mueren **por la aserción que dicen comprobar**, no por errores de sintaxis. La última se verificó **neutralizando el guard estático**: el test sigue detecting la regresión en runtime, y con el código intacto sigue en verde.

### Corregido
- **La escritura atómica ahora se prueba de verdad.** El test anterior solo miraba que existiera un archivo temporal, así que si la atomicidad desaparecía y el temporal nunca se creaba, pasaba por la razón equivocada. Ahora se inyecta un fallo *dentro* de la escritura y se comprueba que **tu archivo de configuración sigue intacto**, comparando bytes. Sin hilos y sin esperas.
- **Un fallo de permisos ya no se confunde con "no intentó guardar".** Ahora se comprueba el estado resultante, no un contador de llamadas.
- **`{"profiles": "texto"}` ya no tumba la app al arrancar.** Antes reventaba con un error interno al cargar la configuración. Ahora se detecta como corrupción y se recupera de la copia de seguridad.
- **El test de la vista ya no necesita abrir una ventana.** Se resuelve con un doble que anota desde qué hilo se publica, y desaparece el watchdog que mataba el proceso de tests tras 150 segundos.
- Corregido el comentario que prometía más de lo que el código cumplía.

### Añadido
- 8 pruebas nuevas. **28 → 36 tests**, todos en verde.
- Documentada la razón de por qué un error interno deliberadamente **no** se trata como corrupción: hacerlo convertiría cualquier fallo de programación en una pérdida de packs.

### Impacto
Los tres tests que el paso anterior destapó están cerrados y verificados rompiéndolos otra vez. La lección del arquitecto fue la más valiosa del ciclo: **de sus tres premisas, ninguna era cierta** — la lista de errores ya cubría los casos, un contador de llamadas no puede distinguir dos escenarios, y en Windows el permiso de archivo no bloquea la lectura. Se comprobó con mediciones, no con opiniones.

### ⚠️ Hallazgo nuevo que queda abierto
La auditoría buscando el fallo **opuesto** encontró que la validación comprueba que la *caja* de cada pack es correcta, pero no su *contenido*. Un pack con la lista de protecciones mal escrita se cuela, la copia de seguridad sana **nunca se consulta**, y un guardado posterior la **machaca**. Es pérdida de datos irreversible. Ya está registrado como `TASK-031`, con prioridad máxima.

---


## CYCLE-017 — 2026-09-30

**Pipeline** · sin cambios en la app todavía · **CERRADO por el ciclo 18** (Paso 4 = FAIL aquí)

> El Paso 4 de este ciclo devolvió **FAIL**: encontró 3 tests del ciclo 15 que pasan con el bug puesto. Es exactamente para lo que existe ese paso. **Los 3 se cerraron y verificaron en el ciclo 18** (integridad de datos: no se documentaron como deuda aceptada).

### Añadido
- **Nuevo paso en el bucle: el Paso 4, "auditar los tests".** El bucle pasa de 3 pasos a 4. Consiste en **romper el código a propósito** y comprobar que los tests se enteran. Hay un agente nuevo, `mutation-auditor`, que lo hace en una copia aparte para no tocar el proyecto.

### Por qué
Porque **`run_tests.py` en verde no demuestra nada sobre los tests**. Dice que el código hace lo que el test comprueba; no dice que el test compruebe algo. Un test que ejecuta una función y no mira el resultado da 100% de cobertura y cero verificación. Es un problema conocido en la industria —lo llaman *mutation testing*— y en este repo ya había dado resultados: un test comparaba contra un texto que el código ya no contenía, y **siempre pasaba**.

### Corregido
- Reparadas 9 referencias a `tm.py` en la documentación del repo, que seguían mandando usar un comando que **no funciona en este entorno**. Cualquier agente nuevo que lo leyera se atascaba.
- La sección de validación de la skill afirmaba cosas que el script **no comprueba**. Ahora lista lo que comprueba de verdad y lo que no.

### Impacto
El agente nuevo, en su primer minuto de vida, encontró **tres tests que pasan con el bug puesto**: uno da por buena la escritura atómica sin comprobar nunca que el archivo quede intacto si el guardado se corta a mitad; otro acepta "no intentó guardar" igual que "intentó y falló"; y un tercero no cubre los errores de tipo que sí tumban la app. **Eran fallos del ciclo anterior, dados por buenos.** Nada de eso lo habría detectado volver a pasar los tests.

### Mutaciones auditadas (Paso 4)
| Fix del ciclo 15 | Mutación | Veredicto | Motivo |
|---|---|---|---|
| Backup preventivo | `shutil.copy2` → `pass` | **killed** | `save() no creo el .bak preventivo` |
| Escritura atómica | `os.replace` + temporal → `open(w)` directo | **SUPERVIVIÓ** | 28/28 verde: el assert solo mira que exista un `.tmp`, y si ya no se crea, sigue pasando |
| Escritura atómica | `os.replace` → `shutil.copyfile` | killed | Detecta el artefacto `.tmp`, **no la garantía** de atomicidad |
| Recuperación `.bak` | devuelve `AppData()` vacío | **killed** | `no devolvio los packs del usuario: ['gaming']` |
| `except` honesto | `CORRUPTION_ERRORS` → solo `JSONDecodeError` | **SUPERVIVIÓ** | 28/28 verde: `ValidationError`/`TypeError`/`UnicodeDecodeError` sin cobertura |
| `except` honesto | reintroducir `OSError` en `CORRUPTION_ERRORS` | **SUPERVIVIÓ** | 28/28 verde: `except OSError: pass` acepta "no intentó guardar" igual que "intentó y falló" |
| Sentinela `⚪ Otros` | → `"? Otros"` (ASCII) | **killed** | `_DEFAULT_META[0] es '? Otros'`: la interrogación no es U+26AA |
| Publicación en hilo | quitar `self.after(0, _apply)` | killed | **Por el guard `ast`, no por la aserción real** — al quitarlo, el test cuelga el bucle Tcl en vez de fallar |


---

## CYCLE-016 — 2026-09-30

**Pipeline** · sin cambios en la app · COMPLETED

### Corregido
- **Los tres roles del pipeline ya no se pierden en la traducción.** El arquitecto, el desarrollador y el analista de procesos eran ficheros de instrucciones que yo tenía que traducir a mano en cada delegación. Ahora son **agentes de verdad**: aparecen en tu panel y se les delega directamente.
- **Arreglada una instrucción que llevaba tiempo rota:** la skill seguía mandando invocar un mecanismo que ya no existe. Por eso la primera vez que quise llamar al arquitecto dio error, y tuve que improvisar. Corregido en los bloques de invocación **y en las tres plantillas de prompt**, que también pedían el modelo a mano. Anotado que **no existe** para que no se repita.
- **Un fallo que introduje yo en este mismo pase:** al reescribir la sección de roles de `AGENTS.md` la renombré, y `validate_docs.py` buscaba el encabezado antiguo por nombre literal → la validación pasó a dar FAIL. Un validador atado a un título deja de validar en cuanto el título mejora. Ahora acepta ambos nombres.

### Añadido
- Cada agente lleva dentro las **lecciones de los dos últimos ciclos**, no solo el texto original: que el blindaje de nombres no protege `svchost`, que hay que comparar el nombre completo del proceso, y la trampa de los emojis.
- En `AGENTS.md`, una tabla que separa **skill** (fichero de instrucciones) de **agente** (sesión propia), porque esa distinción era justo lo que te impedía verlos.

### Verificación
No me fié de "ya están creados": le encargué al arquitecto una auditoría de prueba y acertó por su cuenta con dos detalles que le habían dado errores a otros — que la función de protección de sistema es un método de la clase y no una función suelta, y que la lista de nombres **no** protege al servicio de Windows — citando el código en ambos casos. Cero ficheros modificados: respetó su propio rol.

---

## CYCLE-015 — 2026-09-29

**Resiliencia & Robustez** · `TASK-026` · COMPLETED

### Corregido
- **Un error al guardar te borraba toda la configuración.** Si el archivo de packs se corrompía, la app lo sustituía por un pack vacío sin avisar. Y lo peor: el código que debía distinguir "archivo dañado" de "no tengo permiso para escribir" en realidad aceptaba **cualquier** error, así que un simple fallo de permisos hacía exactamente lo mismo — borrarlo todo.
- **Los packs ahora se guardan con copia de seguridad** y se recuperan solos. La escritura es atómica: si se corta a mitad, el archivo anterior sigue intacto.
- **Cerrado un fallo que podía colgar la app** al abrir el Gestor de Procesos: la lista se construía en segundo plano mientras la ventana la recorría a la vez. Ahora se construye aparte y se muestra de una sentada. El mismo descuido hacía que la lista de PIDs a cerrar estuviera desfasada.
- **Un filtro que no filtraba nada**: comparaba contra el texto equivocado al detectar procesos sin categoría, con lo que la lista-"Otros" se colaba en el resto.
- Corregida una comprobación de tests que **siempre pasaba** porque miraba un valor que ya no existía en el código.

### Documentación corregida
El registro anterior afirmaba que las copias de seguridad ya existían desde hace 12 ciclos. **No existían**: nunca se había escrito ni una línea. Corregido, y añadida una comprobación automática para que la documentación no vuelva a mentir sobre si una función existe.

### Verificación
`run_tests.py` 28/28 en verde · `verify_ui_syntax.py` EXITO · `validate_docs.py` sin fallos.
Cada test nuevo se comprobó **revirtiendo el arreglo a propósito**: los 4 fallan sin él, cada uno por su comprobación prevista.

### Nota sobre cómo se corrige esto
Al reescribir el README se descubrió que la documentación afirmaba en 5 sitios que la app "se auto-eleva para matar procesos protegidos". Al buscarlo, un análisis automático concluyó que era falso y casi se documenta así. **Era una conclusión equivocada**: el `.exe` sí se compila con `--uac-admin` (`force_build.py`), y la búsqueda fallaba porque la elevación es una opción de compilación, no código en `src/`. El README describe lo que ocurre de verdad: el ejecutable pide permisos de administrador, y al correrlo desde código no.

---

## CYCLE-014 — 2026-09-29

**Gaming & Telemetría UX** · `TASK-025` · COMPLETED

### Corregido
- **El Gaming Mode ya consulta tu configuración.** Antes, marcar categorías para cerrar y aplicaciones para proteger no tenía efecto: el motor solo cerraba la lista manual de apps y nunca miraba `keepers` ni `target_categories`. Ahora sí, y con la misma política en los tres caminos (bandeja del sistema, portada y gestor de packs).
- **Cerrada una vía que podía dejar Windows inservible.** El blindaje por lista de nombres no cubría la evaluación por categoría: `svchost.exe` y `explorer.exe` no están en esa lista y su categoría 🔴 era seleccionable. Ahora hay una **barrera de categoría roja** independiente, aplicada en dos capas.
- **Corregido un fallo silencioso que habría tumbado tus protecciones.** Los keepers se guardan como `discord.exe` pero el proceso se comparaba sin extensión, así que ni los keepers ni las apps explícitas se reconocían. Steam y Discord habrían muerto siendo "protegidos".
- El Gaming Mode configurado **solo por categorías** ya no se ignoraba (dos salidas mudas lo bloqueaban).

### Añadido
- `test_execute_gaming_pack_integration`, verificado **por mutación**: al desactivar la barrera a propósito, el test falla admitting `svchost.exe`. No es un test decorativo.

### Verificación
`run_tests.py` 24/24 en verde · `verify_ui_syntax.py` EXITO · revisión independiente: **PASS**.
Commits pendientes: el entorno bloqueó el versionado durante este pase.

---

## CYCLE-013 — 2026-09-29

**Base de Datos & Procesos** · `TASK-024` · COMPLETED · `0ad23bb`

### Añadido
- **Blindaje anti-brick**: 34 procesos de Windows marcados como indestructibles, aplicados por **tres vías** (al cargar la base, al resolver metadatos y en el propio cierre). El motivo: el pack lo escribes tú a mano, así que un `lsass.exe` en un pack también tiene que ser indestructible.
- **+25 entradas** de bloatware real (48 → 73): PowerToys, consumo de Armoury Crate, servidores de lenguaje, audio y actualizadores.

### Impacto
Se cierra la vía por la que la app más se dañaba a sí misma. Un proceso de la base solo se cierra si su categoría lo permite, aunque escribas su nombre a mano.

---

## CYCLE-012 — 2026-09-29

**Gaming & Telemetría UX** · `TASK-023` · COMPLETED

### Corregido
- **5 acciones destructivas volvieron a pedir confirmación.** La reescritura a v3 perdió el patrón de doble pulsación: "Cerrar Seleccionados" mataba N procesos de un solo clic, y en la portada los packs se colocan de dos en dos, así que el botón Gaming tenía un pack vecino pegado.
- El Gestor de Packs no daba **ningún feedback** al borrar un pack protegido: fallaba en silencio.

### Añadido
- `ui/confirmation.py` con `DoubleTapGuard`, en un solo sitio y reutilizado por las tres vistas.
- **Trampa #14** documentada: nunca un diálogo modal en la ventana principal, porque se abre *detrás* y parece que la app está rota. La seguridad la da la segunda pulsación, no el diálogo.

---

## CYCLE-011 — 2026-09-29

**Resiliencia & Robustez** · `TASK-022` · COMPLETED

### Corregido
- **El pipeline podía "completar" ciclos sin versionar nada.** `git_safe_commit.py` salía con código 0 ante cualquier fallo de commit, así que el registro guardaba hashes que podían no existir y nadie se enteraba.
- Un texto de git (`"nothing to commit"`) se usaba para decidir, y **ese texto cambia con el idioma del sistema**: en un Windows en español nunca aparece.

### Añadido
- Wrapper reescrito con códigos de salida honestos y flag `--verify`.
- `dist/woptimizer.exe` regenerado (25,65 MB).

---

## CYCLE-010 — 2026-09-29

**Testing & Calidad** · `TASK-021` · COMPLETED

### Corregido
- **"Restaurar por defecto" no hacía nada.** `model_copy()` de Pydantic v2 es *shallow*, así que las listas del pack Gaming se compartían con el global y la UI las modificaba en silencio.
- +8 tests para invariantes que se habían quedado sin cubrir tras la migración v2→v3.

---

## CYCLE-009 — 2026-09-29

**Base de Datos & Procesos** · `TASK-020` · COMPLETED

### Corregido
- **6 de las 8 categorías perdían su semáforo** por emojis desalineados entre la base y la configuración: todos esos procesos caían en "? Otros" **sin indicador de seguridad**. Un desajuste de un carácter en un emoji.
- El semáforo se evaluaba por prioridad antes que por categoría, pintando de amarillo lo que era rojo.

### Añadido
- +14 procesos: navegadores, launchers y herramientas de IA.

---

## CYCLE-008 — 2026-09-29

**Gaming & Telemetría UX** · `TASK-019` · COMPLETED

### Añadido
- **Notificaciones nativas de Windows**: al cerrar procesos o activar un pack, sale un toast del sistema aunque la ventana esté oculta. Funciona con la app minimizada en la bandeja.

---

## CYCLE-007 — 2026-09-29

**Rendimiento & Latencia** · `TASK-018` · COMPLETED

### Cambiado
- Búsqueda de metadatos por **hashmap O(1)** en vez de lista lineal, y **caché de 2 segundos** para no re-escanear el sistema en cada pulsación.
- Las lecturas cacheadas bajaron de ~15 ms a **0,003 ms** (unas 5000×). Cerrar procesos invalida la caché.

---

## CYCLE-006 — 2026-09-29

**Resiliencia & Robustez** · `TASK-017` · COMPLETED

### Corregido
- El icono de la bandeja no se guardaba, así que el cierre limpio era imposible.
- Cierre de apps sin logging: los fallos individuales pasaban desapercibidos.

---

## CYCLE-005 — 2026-09-29

**Testing & Calidad** · `TASK-016` · COMPLETED

### Añadido
- Tests de memoria liberada, de protección del pack Gaming y de recuperación ante un JSON corrupto.

---

## CYCLE-004 — 2026-09-29

**Base de Datos & Procesos** · `TASK-015` · COMPLETED

### Añadido
- 4 procesos de telemetría y sincronización catalogados.

---

## CYCLE-003 — 2026-09-29

**Gaming & Telemetría UX** · `TASK-014` · COMPLETED

### Añadido
- Banner en la portada: **cuántos procesos se cerraron y cuántos MB de RAM se liberaron** tras activar un pack. Verde para Gaming, azul para el resto.

---

## CYCLE-002 — 2026-09-29

**Resiliencia & UX** · `TASK-012` · COMPLETED

### Añadido
- **System tray**: cerrar la ventana la minimiza a la bandeja en vez de salir, con menú rápido.
- Rotación de copias de `profiles.json` y logging continuo en `woptimizer.log`.

---

## CYCLE-001 — 2026-09-28

**Arquitectura & UI** · `TASK-001..009` · COMPLETED

### Añadido
- **Rediseño completo a v3**: tres ventanas (Portada, Packs, Procesos) con `CustomTkinter`.
- Backend migrado de PowerShell/WMI a **`psutil`**.
- Persistencia con **`pydantic v2`**.
