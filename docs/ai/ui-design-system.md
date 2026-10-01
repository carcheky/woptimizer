# Sistema de Diseño y Flujo UI CustomTkinter (v3)

## Sistema de Diseño y Tokens (`ui/theme.py`)

A partir de la versión 3.0.1 (TASK-029), la interfaz implementa un sistema de diseño centralizado en `src/woptimizer/ui/theme.py`.
Este módulo define **únicamente tokens visuales** y funciones matemáticas de luminancia y contraste WCAG 2.1; está libre de widgets y lógica de negocio.

### 1. Colores Semánticos y Roles
- **Superficies:**
  - `SURFACE = "#121212"`: Fondo base de la aplicación y frames principales.
  - `SURFACE_ALT = "#1a1a1a"`: Fondo de barras de navegación, tarjetas de packs y cabeceras de categorías.
  - `SURFACE_SUNKEN = "#151515"`: Fondo de subcontenedores (listas de apps, cajas de texto de entrada).
  - `SURFACE_HOVER = "#262626"`: Estado hover en superficies y botones de navegación/herramientas.
  - `BORDER = "#2e2e2e"`: Bordes delimitadores y divisores de contenedor.
- **Tipografía y Textos:**
  - `TEXT_PRIMARY = "#ffffff"`: Texto de alto contraste para títulos, ejecutables y botones activos.
  - `TEXT_MUTED = "#888888"`: Texto secundario, descripciones y pistas.
- **Identidad de Marca y Estados (Opción A):**
  - `GAMING = "#1DB954"` / `GAMING_HOVER = "#1aa34a"`: **Verde Gaming**. Utilizado exclusivamente para el botón principal del Gaming Mode en portada, badges de preset y bordes activos de packs gaming. Resuelve la contradicción histórica (la documentación previa mencionaba rojo en §1 y verde en §5).
  - `ACCENT = "#3B8ED0"` / `ACCENT_HOVER = "#1f6aa5"`: Azul de acento para acciones primarias constructivas (arranque de packs, altas, selecciones).
  - `DANGER = "#c22d2d"` / `DANGER_HOVER = "#a82424"`: **Rojo exclusivo para peligro y acciones destructivas**. Reservado para botones de kill manual, apagado forzado y avisos de bloqueo irrecuperable.
  - `WARNING = "#f59e0b"`: Ámbar para confirmaciones pendientes y estados de atención.
  - `SUCCESS = "#22c55e"`: Verde confirmatorio para feedback completado.

### 2. Escala Tipográfica (Exactamente 6 Tamaños)
La jerarquía tipográfica está estrictamente acotada a una tupla de 6 valores numéricos (`FONT_SIZES = (9, 11, 13, 14, 18, 24)`):
- `FONT_SIZE_TINY = 9`: Badges compactos (PRESET en tarjetas).
- `FONT_SIZE_SMALL = 11`: Descripciones de procesos, tooltips y opciones secundarias.
- `FONT_SIZE_BODY = 13`: Cuerpo de texto estándar, filas de apps y elementos de navegación.
- `FONT_SIZE_SUBHEADER = 14`: Títulos de tarjetas y cabeceras colapsables.
- `FONT_SIZE_HEADER = 18`: Títulos de sección y botones de favoritos en portada.
- `FONT_SIZE_HERO = 24`: Título principal del Dashboard.

### 3. Radios de Borde (Exactamente 3 Tamaños)
- `RADIUS_SMALL = 4`: Badges y checkboxes.
- `RADIUS_MEDIUM = 6`: Tarjetas internas, filas de procesos y botones de herramientas.
- `RADIUS_LARGE = 8`: Marcos principales, barra de navegación y tarjetas de nivel superior.

### 4. Accesibilidad y Micro-UX
- **Contraste WCAG 2.1 AA:** Todo par de colores de texto y fondo en uso supera la ratio de contraste de `4.5:1` (`theme.is_wcag_aa(fg, bg)`).
- **Objetivos de Puntero (Hit Targets):** Todos los botones y controles interactivos tienen una dimensión mínima de `28x28px`.
- **Diálogos Modales Propios:** Sustitución de `CTkInputDialog` huérfano por `NewPackModal` acoplado al toplevel con `grab_set()` y centrado relativo, sin `messagebox`.
- **Responsive y Ancho Mínimo (720px):** Las etiquetas de descripción incorporan `wraplength=380` para prevenir desbordes laterales en pantallas de 14" con escalado de DPI de 125%-150%.

---

## Arquitectura de Vistas (3 Ventanas/Paneles)

### 1. Ventana Principal (Portada / Dashboard)
- **Propósito:** Ejecución ultra rápida de un solo clic al sentarse a jugar o volver a trabajar.
- **Barra de Telemetría en Reposo:** Muestra permanentemente el estado del sistema (`N procesos activos`) y el resultado de la última activación del Gaming Mode sin importar `psutil`.
- **Contenido Central:**
  - Botones de favoritos para los packs marcados como `is_favorite = True`.
  - El botón del pack Gaming tiene estilo prioritario en verde Gaming (`#1DB954`).
  - Al hacer clic en un favorito, ejecuta su acción principal (apagar para gaming, arrancar para packs de trabajo).
  - **Rejilla Dinámica Adaptativa (TASK-049):** Rejilla responsiva con columnas calculadas dinámicamente según el ancho real de `buttons_frame` y el token `theme.ANCHO_MIN_CARD` (280 px). La fórmula es `cols = max(1, min(len(favorites), ancho // ANCHO_MIN_CARD))`. En pantallas anchas distribuye uniformemente en 3 o 4 columnas; en ventanas estrechas colapsa a 2 o 1 columna. Los eventos `<Configure>` del frame re-maillan los botones en vivo sin destruirlos ni alterar el estado de confirmación. Columnas no utilizadas sueltan su peso (`weight=0, uniform=""`) para evitar columnas fantasma. El estado vacío `_empty_label` abarca la totalidad de las columnas calculadas (`columnspan=cols`).
- **Barra de Navegación Inferior:**
  - Altura fija unificada (`height=44`, `pack_propagate(False)`).
  - Indicador de vista activa mediante acento visual y texto primario, sin fondos azules estridentes.
  - Botón `📁 Gestor de Packs`: Abre la vista de gestión completa.
  - Botón `⚡ Gestor de Procesos`: Abre la vista de procesos activos.

### 2. Gestor de Packs (`views/pack_manager_view.py`)
- **Propósito:** Crear, editar y ejecutar packs de aplicaciones.
- **Contenido:**
  - Botón superior `➕ Nuevo Pack` que abre un diálogo modal acoplado (`NewPackModal`).
  - Lista scrollable con tarjetas para cada pack.
  - El pack Gaming de fábrica cuenta con borde y badge `PRESET` resaltados en verde Gaming (`#1DB954`).
  - Cada tarjeta de pack incluye:
    - Nombre del pack y cantidad de apps configuradas.
    - Botón `⭐` para alternar si es favorito (aparece en portada). Es un **toggle real**: la segunda pulsación de la estrella de un pack que ya es favorito lo **desmarca** (`pack_service.set_favorite(None)`). El estado se lee **en vivo** de `get_all_packs()`, nunca del `pack` capturado en el render (queda obsoleto en cuanto el estado cambia) ni del glifo ⭐/☆, y **nunca** con `get_favorite_pack()` (devuelve el PRIMER favorito: con dos favoritos pulsaría el segundo en vez de desmarcarlo). Consecuencia aceptada: al desmarcar el único pack la portada queda en su **estado vacío** (`dashboard_view._show_empty_state`), un callejón sin salida *desde la portada* pero recuperable desde el Gestor de Packs, que es donde vive la estrella (TASK-027 / FIX-006).
    - Botón `⛔ Apagar Apps`: Cierra los ejecutables del pack. Si `is_gaming = True` va por `gaming_service.execute_gaming_pack()` (respeta `keepers` y `target_categories`); si no, por `process_service.kill_pack_apps()`.
    - Botón `🚀 Arrancar Apps`: Lanza todos los ejecutables configurados vía `ProcessService.start_pack_apps()`, que **valida cada ruta antes de lanzarla** (sin intérprete, sin UNC, contenida en las raíces permitidas y con extensión `.exe`/`.com`). La UI nunca llama a `subprocess` ni a `os.startfile`: ver `architecture.md` § 14 (TASK-027 / FIX-003).
    - Botón `🔄 Restaurar`: Restablece la configuración predeterminada del pack Gaming (`reset_gaming_pack`).
    - Botón `🗑️ Borrar`: Elimina el pack (deshabilitado si `is_gaming = True`).

### 3. Gestor de Procesos en Vivo (`views/process_manager_view.py`)
- **Propósito:** Explorar qué está consumiendo recursos y agregarlo a packs fácilmente.
- **Contenido:**
  - Botón superior `🔄 Actualizar Lista`.
  - Buscador de texto en tiempo real.
  - Cabeceras de categorías con fondo (`SURFACE_ALT`), hover (`SURFACE_HOVER`) y contador `(N)`.
  - Lista agrupada por categorías (`🔴 Navegadores`, `🟡 Chat`, etc.) con checkboxes y descripciones con `wraplength=380`.
  - **El orden de las secciones es `CATEGORY_ORDER`**, no el color del semáforo y **nunca `sorted()`** sobre los nombres: se llama a `config.ordenar_categorias()` en los **dos** sitios que dibujan categorías (`_render_list` y el acordeón de `pack_manager_view`). `CATEGORY_ORDER` entrelaza verde y amarillo a propósito (`🟢 Productividad` va detrás de `🟡 Chat`), así que «orden semántico 🟢 → 🟡 → 🔴 → ⚪» es un criterio imposible. Lo que `sorted()` rompía: ordena por **punto de código**, y el centinela `⚪ Otros` (U+26AA, BMP) salía PRIMERO mientras que 🟢🟡🔴 viven en el plano suplementario (U+1F7E2, U+1F7E1, U+1F534): el bloque rojo «NO CERRAR» subía al primer golpe de vista. Las categorías desconocidas van al final conservando su orden de entrada. Trampa en [`../known-issues.md`](../known-issues.md) (TASK-027 / FIX-004).
  - Estado vacío neutro y descriptivo sin checks fuera de lugar (UI-011).
  - Barra de acción inferior fijada:
    - Desplegable `Añadir seleccionados a: [Seleccionar Pack ▼]`.
    - Botón `➕ Añadir al Pack`.
    - Botón `⛔ Cerrar Seleccionados Ahora`.

## Reglas de CustomTkinter
- **Tema:** Modo oscuro forzado (`ctk.set_appearance_mode("Dark")`).
- **Fuentes:** Utilizar familias de sistema estándar (`"Segoe UI"` en Windows) con la escala tipográfica de `theme.py`.
- **Hilos de Fondo:** Toda operación de listado o kill pesado debe correr en un `threading.Thread(daemon=True)` para que la interfaz nunca se congele, actualizando la UI mediante `self.after(0, callback)`.

## Especificaciones de Pantalla y Responsive (14 Pulgadas)
- **Dimensiones:** Ventana inicial de `860x560` (mínimo `720x460`) optimizada para portátiles de 14" con escalado de Windows de 125% a 150%.
- **Semáforo Visual de Seguridad (`get_safety_badge`):**
  - `🟢 SEGURO`: Verde brillante (`#40c057`) sobre fondo verde oscuro (`#163820`). Cierre recomendado (Browsers, Sync, Productividad).
  - `🟡 PRECAUCIÓN`: Amarillo ámbar (`#fcc419`) sobre fondo amarillo oscuro (`#3d3711`). Apps de juegos/media (Launchers, Discord, Spotify).
  - `🔴 NO CERRAR`: Rojo vibrante (`#ff6b6b`) sobre fondo rojo oscuro (`#401616`). Vitales para el SO o hardware (Windows, drivers, antivirus).
- **Gestor de Packs Compacto:**
  - Toolbar de acciones en tarjetas de pack con hit targets mínimos de 28x28px.
  - Acordeón plegable para configurar categorías automáticas en el Pack Gaming.

## Banner de Telemetría de RAM (`status_banner`) — TASK-014

### Ubicación en `DashboardView._build_ui()`
Insertado como tercer bloque, **después** del `header` y **antes** del `buttons_frame` (actualmente líneas 22-23 de `dashboard_view.py`):

```
header (fill=x, pady=(0,20))
status_banner  ← NUEVO  (fill=x, pady=(0,8))
buttons_frame  (fill=both, expand=True)
```

### Estructura de Widgets
```
status_banner_frame  CTkFrame  fg_color=transparent  (oculto por defecto: pack_forget)
  └─ status_label    CTkLabel  wraplength=600, font=("Segoe UI", 13, "bold")
```

### Colores de Acento por Tipo de Pack
| Condición | Color de fondo | Color de texto |
|-----------|---------------|----------------|
| `pack.is_gaming == True` | `#1B4332` (verde oscuro) | `#1DB954` (verde gaming) |
| Otros packs (kill) | `#1a2a3a` (azul oscuro) | `#4a9fd4` (azul) |

### Wiring Thread-Safe del Callback
```python
# En execute_pack, hilo secundario:
def _run_kill(p):
    if p.is_gaming:
        # Gaming Mode: consulta keepers y categorias en la capa de servicios
        killed, failed, skipped, freed_mb = self.gaming_service.execute_gaming_pack(p)
    else:
        killed, failed, skipped, freed_mb = self.process_service.kill_pack_apps(p.apps)
    self.after(0, self._show_banner, killed, freed_mb, p.is_gaming)

threading.Thread(target=_run_kill, args=(pack,), daemon=True).start()

# En el hilo principal (after callback):
def _show_banner(self, killed: int, freed_mb: float, is_gaming: bool):
    # … actualizar status_label y hacer pack() del frame …
    self.after(5000, self._hide_banner)
```

Este es **el** patrón del proyecto y no es solo un ejemplo: el hilo secundario no lee ni
escribe estado de la vista, y `self.after` (nunca `self.master.after`, que sobrevive a la
destrucción de la vista en cada navegación) es el único publicador.

**Gestor de Procesos, TASK-026 (FIX-007).** `ProcessManagerView._do_load` lo cumple con un
`_apply` explícito porque publica **dos** atributos a la vez:

```python
def _load():
    procs = self.process_service.get_running_processes()
    grouped = self._group(procs)          # función pura, dict NUEVO

    def _apply():
        self.processes = procs
        self.grouped_processes = grouped   # REBIND, nunca .clear() in situ
        self._render_list()
        self._update_pack_dropdown()

    self.after(0, _apply)
```

El REBIND es lo que hace seguro el resto: el hilo principal itera `grouped_processes` en cada
`_render_list` (y en cada pulsación del buscador), así que mutarlo desde el hilo secundario
provocaba `RuntimeError: dictionary changed size during iteration` y, con dos refrescos
solapados, dejaba el set de PIDs de `on_kill_selected` desalineado respecto de la lista que el
usuario ve. Cuando dos cargas se solapan, el que llegue último al mainloop gana **entero**;
`processes` y `grouped_processes` nunca describen snapshots distintos.

> `tkinter` exige que el hilo principal esté **dentro** del bucle de eventos cuando otro hilo
> llama a `after` (`RuntimeError: main thread is not in main loop`). En la app es el caso
> normal; en los tests hay que entrar en el mainloop real, no en un bucle con `update()`.

### Invariantes a Respetar
- La UI **nunca** llama a `psutil` directamente; `freed_mb` llega exclusivamente como argumento del callback.
- Toda manipulación de widgets ocurre en el hilo principal vía `self.after(0, ...)`.
- El pack gaming (`is_gaming=True`) puede activarse (acción kill/start) pero **no** puede borrarse.

## Notificaciones Nativas (Toast) — TASK-019

### Inyección del Servicio
`WOptimizerApp` crea un `NotificationService` y lo inyecta por parámetro de constructor. `MainWindow` lo recibe y lo reenvía a las tres vistas:

```python
# app.py -> MainWindow
MainWindow(master, process_service, pack_service, gaming_service, notification_service)

# MainWindow -> cada vista
DashboardView(self.content_frame, self.process_service, self.pack_service, self.notification_service, self.gaming_service)
PackManagerView(self.content_frame, self.process_service, self.pack_service, self.notification_service, self.gaming_service)
ProcessManagerView(self.content_frame, self.process_service, self.pack_service, self.notification_service)
```

Todas las vistas aceptan `notification_service=None` y crean un local si no se les pasa, de modo que los constructores antiguos y los tests headless siguen funcionando. Desde TASK-025, `DashboardView` y `PackManagerView` aceptan además `gaming_service=None` con el **mismo fallback defensivo** (`GamingService(process_service, pack_service)` local). `ProcessManagerView` no lo necesita: no ejecuta packs.

### API que Consume la UI (no llamar a `pystray` nunca)
| Helper | Cuándo usarlo |
|--------|---------------|
| `notify_pack_activated(pack.name, killed, freed_mb)` | Tras ejecutar un pack con `default_action="kill"` |
| `notify_apps_launched(pack.name, started, failed)` | Tras ejecutar un pack con `default_action="start"` |
| `notify_kill_result(killed, failed, freed_mb)` | Tras un cierre manual en el Gestor de Procesos |

### Puntos de Emisión
- `DashboardView.execute_pack()` → ambos helpers según `default_action`.
- `PackManagerView.kill_pack()` / `.start_pack()` → ambos helpers.
- `ProcessManagerView.on_kill_selected()` → `notify_kill_result`.
- `WOptimizerApp` menú del tray (`gaming_action`) → `notify_pack_activated`.

### Invariantes a Respetar
- La UI **nunca** importa `pystray`; solo conoce los tres helpers.
- Las notificaciones se emiten **desde el hilo secundario** ya que no tocan widgets: son llamadas al sistema operativo, no manipulación de la UI.
- `notify()` nunca lanza excepciones: si no hay bandeja o el backend falla, degrada al log (`woptimizer.log`).
- Los mensajes se formatean en español con plurales correctos (`1 cerrada` / `5 cerradas`) vía la función pura `format_kill_result()`, testeable sin sistema operativo.
- `auto-hide` a los 5 s con `self.after(5000, self._hide_banner)` para no saturar la UI.

## Acciones Destructivas: Doble Pulsación — TASK-023

### Por qué (y por qué no un `messagebox`)
En la v2 las acciones destructivas exigían una segunda pulsación. Se perdió en la reescritura v3 y volvió como regresión silenciosa. El patrón nació de un incidente real: un `messagebox.askyesno` se abría **por detrás** de la ventana principal, el usuario pulsaba "Cerrar", no veía nada y reportó "la app está rota, no mata procesos". **Regla dura: nunca `messagebox` en la ventana principal**; la seguridad se consigue con la segunda pulsación y el feedback va al `status_label` inline.

### Las dos capas de `ui/confirmation.py` (helper único)
| Capa | Qué es | Regla |
|------|--------|-------|
| `DoubleTapGuard` | Máquina de estados ** pura: `arm` / `consume` / `reset` / `is_pending` / `cancel_on_destroy`, con `scheduler` inyectable | No importa `customtkinter` ni `tkinter`; se testea headless con un doble |
| `Confirmable` | Mixin fino de las vistas: `_require_double_tap(...)` arma o devuelve `True`, `_cancel_confirm()`, `cancel_on_destroy()`, `_inline_status()` | Solo configura widgets; no decide nada de negocio |

El mixin **no** es clase base de las vistas: instanciar un `CTkFrame` exigiría un root Tk y la máquina de estado tiene que poder probarse sin ventana.

### Uso en una vista
```python
class MiVista(Confirmable, ctk.CTkFrame):
    def __init__(self, master, ...):
        super().__init__(master, fg_color="transparent")
        self._build_ui()          # crea self.status_label y los botones
        self._init_confirmable(self.status_label)   # DESPUÉS de crear el label

    def destroy(self):
        self.cancel_on_destroy()  # mata el `after` vivo ANTES de destruir
        super().destroy()

    def accion_destructiva(self, pack_id, button=None):
        if not self._require_double_tap(f"mi_accion:{pack_id}", button, "⚠️ Segunda pulsación para ..."):
            return                   # 1ª pulsación: solo queda armada
        ...                          # 2ª pulsación: se ejecuta
```

### Los 3 estados del botón
| Estado | `text` | `fg_color` | `hover_color` |
|--------|--------|-----------|---------------|
| Reposo | el literal propio del botón (se recuerda solo, no se hardcodea) | el propio | el propio |
| Pendiente | `"⚠️ ¿SEGURO? PULSA OTRA VEZ"` | `#b8860b` | `#8a6508` |
| Tras confirmar | reposo, `state="disabled"` 300 ms y se rehabilita solo | — | — |

Mensajes al `status_label`: rojo `#c22d2d` para los `⛔` de bloqueo, ámbar `#b8860b` para los `⚠️`, verde `#1DB954` para los `✅`.

### Las 5 acciones cubiertas
| Vista | Handler | Token | Ventana |
|-------|---------|-------|---------|
| `ProcessManagerView` | `on_kill_selected()` | tupla de claves marcadas | 3000 ms |
| `PackManagerView` | `kill_pack(pack_id, button)` | `pack_kill:{id}` | 3000 ms |
| `PackManagerView` | `delete_pack(pack_id, button)` | `pack_del:{id}` | 3000 ms |
| `PackManagerView` | `remove_app_from_pack(pack_id, app, button)` | `pack_app:{id}:{app}` | 3000 ms |
| `DashboardView` | `execute_pack(pack, button)` | `dashboard:{id}` | **2000 ms** |

`execute_pack` confirma **solo** en la rama `default_action == "kill"`. Arrancar apps no es destructivo y no pide nada.

### Única excepción: el ítem del tray (TASK-025)
El menú de la bandeja (`WOptimizerApp.show_tray → gaming_action`, ítem `🚀 Preparar Gaming Mode`) es la **única ruta de kill del producto que NO pasa por `_require_double_tap`**. No es una vía nueva: ya ejecutaba el Gaming Mode sin confirmar antes de TASK-025.

Por qué es la excepción y no un olvido:
- **No puede recibir doble pulsación.** Un `MenuItem` de `pystray` no es un widget: no tiene `status_label` donde explicar nada, ni ciclo de vida de vista que permita armar/cancelar una pendiente. La única alternativa sería un diálogo, y **`messagebox` está prohibido explícitamente** (Trampa #14, el incidente del diálogo que se abría por detrás).
- **La objeción real a la doble pulsación no aplica.** El riesgo documentado es el clic en el objetivo equivocado por adyacencia: un ítem de menú es una **única entrada, con nombre explícito, sin vecinos ni selección que fallar**.
- **El alcance de la acción sí es mayor**, y por eso la excepción queda escrita aquí y no implícita: con `target_categories` activas, la ruta por categoría cierra procesos que el usuario nunca enumeró. Esa amplitud está acotada por la barrera de categoría roja G-2 de `GamingService.execute_gaming_pack` (una categoría `🔴` marcada como objetivo es inerte) y por el blindaje de nombres de `SYSTEM_PROTECTED_PROCESSES`, ambos en la capa de servicios, no en la UI.
- Desde TASK-025 el tray ejecuta `self.gaming_service.execute_gaming_pack(gaming_pack)` (igual que las dos vistas), de modo que respeta `keepers` y `target_categories` y comparte la única puerta de kill.

**Invariante que deja el cambio:** *ningún camino de kill nuevo puede añadirse sin `_require_double_tap`*. Las tres rutas de la ventana están inventariadas en la tabla de arriba y el guard es la única puerta dentro de ella; el tray es la única excepción documentada. Si algún día se le quiere dar confirmación, hay que añadir antes una superficie de estado al `MenuItem` (o un ítem de "confirmar"), nunca un `messagebox`.

### La rama Gaming Mode dentro de la doble pulsación
En las dos vistas, el texto del aviso se adapta al pack pero **el guard es el mismo** (`_require_double_tap` con su token y su ventana). Nada se reimplementa:

| Vista | Handler | Texto del aviso |
|-------|---------|-----------------|
| `DashboardView` | `execute_pack(pack, button)` | `"⚠️ Segunda pulsación para preparar el Gaming Mode de '{name}'."` |
| `PackManagerView` | `kill_pack(pack_id, button)` | `"⚠️ Segunda pulsación para preparar el Gaming Mode de '{name}'."` |

`PackManagerView` mantiene el **re-fetch del pack por `id`** en la segunda pulsación, porque `reset_gaming_pack()` re-empaqueta con `model_copy(deep=True)`. El resto de la comprobación también es Gaming-aware: un Gaming Mode con `apps` vacía se ejecuta (su configuración está en `keepers` + `target_categories`), así que la guarda es `if not pack.is_gaming and not pack.apps`.

### Invariantes a Respetar
- **Se congela la INTENCIÓN, se recalculan los DATOS.** El token de `on_kill_selected` es el conjunto de claves marcadas; los `ProcessInfo` se recalculan en la segunda pulsación. Entre pulsaciones el PID se recicla: matar un `ProcessInfo` congelado es matar a un inocente.
- **Cambiar la selección invalida y re-arma** (mensaje "⚠️ Selección cambiada. Vuelve a pulsar para confirmar."), no ejecuta con la intención vieja. Se usa `changed_text=` para ese mensaje.
- **El token es el `id` del pack, nunca el objeto `Pack`**: `reset_gaming_pack()` re-empaqueta con `model_copy(deep=True)` y una referencia capturada puede quedar obsoleta. Re-fetch por `id` al confirmar.
- **`self.after(...)`, nunca `self.master.after(...)`.** Toda navegación destruye la vista y crea otra; `master` es `content_frame`, que sobrevive, y el callback huérfano reconfigura widgets destruidos.
- **Se cancela en `destroy()`, en `refresh_packs()`/`refresh_dashboard()` y ANTES de ejecutar la acción confirmada** (la propia acción puede destruir el botón, caso `remove_app_from_pack`).
- Solo hay una pendiente viva por vista: pulsar otra acción distinta la descarta.
- `ui/confirmation.py` solo importa `typing`; prohibido `psutil`, `json`, `services` y `models` (§7.4 de la OpenSpec). El guard de imports vive en `run_tests.py::test_double_tap_guard`.
- **Nada se traga en silencio:** los fallos de `delete_pack` (pack de sistema / inexistente) se muestran en el `status_label`, nunca `except: pass`.
- **El acordeón de categorías compara contra el centinela canónico (TASK-026 / FIX-005).** El filtro `if "⚪ Otros" not in row.category` de `PackManagerView` usa el **círculo U+26AA**, el mismo literal que `config.CATEGORY_ORDER[-1]` y que `process_service._DEFAULT_META[0]`. Escribirlo como `"? Otros"` deja el filtro comparando contra un texto que ya no existe en el código (no-op) y, en cuanto la DB traiga la categoría canónica, ofrece "Otros" como casilla activable de `target_categories`: basura seleccionable que el usuario nunca pidió. Cuando se toque uno de los tres sitios, se tocan los tres.

## Feedback y Telemetría en Ejecución de Packs (TASK-035)

### Motivación y Unificación
Previamente existía asimetría entre vistas y acciones:
- En la Portada (`DashboardView`), la acción `kill` mostraba un banner enriquecido con procesos cerrados y MB de RAM liberados (`_show_banner`), mientras que `start` lanzaba un worker en segundo plano y toast del tray, pero la interfaz permanecía muda sin banner en pantalla ni refresco de telemetría.
- En el Gestor de Packs (`PackManagerView`), tanto `kill_pack` como `start_pack` corrían en hilos secundarios pero dejaban `status_label` completamente vacío.
- Además, `start_pack` con un pack sin apps retornaba de forma silenciosa sin indicar al usuario por qué no ocurría nada.

### Contrato de Feedback Visual Unificado
1. **Portada (`DashboardView`):**
   - **Arranque (`start`):** El worker secundario despacha al hilo principal vía `self.after(0, self._show_start_banner, launched, failed, p.name)`.
   - `_show_start_banner(launched, failed, pack_name)`:
     * Invalida la caché del servicio de procesos (`process_service.invalidate_cache()`).
     * Actualiza la barra de reposo en vivo (`_update_resting_bar()`).
     * Configura `status_banner_frame` y `status_label` con fondo `theme.SURFACE_ALT`:
       - `failed == 0`: texto `"🚀 Pack '{pack_name}' iniciado ({launched} apps)."` con color `theme.ACCENT`.
       - `failed > 0`: texto `"⚠️ Pack '{pack_name}': {launched} apps iniciadas, {failed} fallaron."` con color `theme.WARNING`.
     * Cancela cualquier temporizador previo de auto-ocultación y programa el nuevo, **llamando a `self._reprogramar_autoocultado()`** (cancela `self._banner_timer`, saca el handle de `_timers_ui` y programa `AUTOOCULTADO_MS = 5000` ms). Es el **único** sitio donde se programa el auto-ocultado del banner, y lo usan las dos puertas.
   - **Apagado (`kill`):** Se mantiene `_show_banner` (sin alias: `_show_kill_banner` era código muerto y se borró), mostrando procesos cerrados y MB liberados con `theme.GAMING` o `theme.ACCENT`, y refrescando la barra de reposo con `_update_resting_bar()`.

2. **Gestor de Packs (`PackManagerView`):**
   - **Guarda preventiva en `start_pack`:** Si `not pack.apps`, la UI cancela confirmaciones pendientes y emite de inmediato `self._inline_status(*mensaje_sin_apps(pack.name, "start"))` sin crear un hilo innecesario. Aquí la **acción** es arrancar, así que el verbo es "iniciar" aunque el pack sea gaming con `default_action="kill"`: quien decide el verbo es el formateador, y quien dice qué acción se ejecuta es el método.
     - Eso no es una convención sin medir: `test_el_feedback_de_pack_dice_la_verdad` pasa un `Pack(is_gaming=True, default_action="kill", apps=[])` por `start_pack` y exige el texto **"no tiene apps que iniciar"**. El caso anterior (pack normal) no distinguía nada, porque `default_action` vale `"start"` de serie y las dos cableaciones dan el mismo texto; con el gaming de apagar, cablear `pack.default_action` produce **"apagar"** y el test muere por aserción. Si "corregir" esa línea a `pack.default_action` parece más coherente, es la suite la que lo dice que no.
   - **Guarda preventiva en `kill_pack`:** el pack no gaming y sin apps se avisa con `mensaje_sin_apps(pack.name, "kill")`. La comprobación vive **una vez** en `_aviso_pack_inerte(pack)` y se llama en los **dos** puntos donde `kill_pack` lee el pack (antes de `_require_double_tap` y tras el re-fetch por `id`): el literal estaba duplicado byte a byte dentro del mismo método, que es la forma más barata de tener dos verdades. Los dos puntos están medidos; el segundo por su propia vía (ver "El pack que no puede hacer nada", mutante `K-a`).
     - El verbo también lo decide el **método**, por el mismo argumento que en `start_pack` y su espejo: `_aviso_pack_inerte` es la puerta de **apagar** y solo la de apagar, así que cablea `"kill"` y **no** `pack.default_action`. Un pack recién creado nace con `default_action="start"` (`on_new_pack` → `create_user_pack(pack_id, name, [])` → el default del modelo), de modo que cablear el pack hacía que la primera acción de un usuario recién instalado —pulsar **⛔ Apagar**— respondiera *"no tiene apps que **iniciar**"*. Lo mide `test_el_feedback_de_pack_dice_la_verdad` con un pack **no gaming, vacío y `default_action="start"`** en `kill_pack`, que exige el texto **"no tiene apps que apagar"**: mutado a `pack.default_action` **o** a `"start"`, el mutante muere por esa aserción. El pack es **no gaming a propósito**, para que el diagnóstico del gaming inerte no se adelante y el assert muera por el verbo y por nada más.
     - **La cadena causal del "nace con `start`" también está medida, por la vía real.** La afirmación anterior la sostenía el comentario de la sonda y este doc, pero ningún test la miraba: cambiar el default del modelo (`models.py`, `default_action: Literal["start", "kill"] = "start"`) a `"kill"` dejaba la suite entera en verde. Desde la iteración 7 la sonda llama a `create_user_pack` **de verdad** (no un `Pack(...)` con literales), exige `default_action == "start"` en el pack que devuelve y pasa ese mismo pack por la puerta de **apagar** exigiendo el texto "apagar". Así la cadena entera —default del modelo → pack recién creado → verbo de la puerta de apagar— queda atada; mutante `D5-d` de `_matrix_c26.py`, MUERE.
   - **Gaming inerte:** un `is_gaming` con 0 apps **y** 0 categorías se diagnostica con `mensaje_gaming_inerte(nombre)` (ROJO, `⛔`) en `_aviso_pack_inerte`, también antes de `_require_double_tap`. Con ambas listas vacías `should_kill_for_gaming` cae a `False` para todo lo no protegido: es **inerte por construcción**. Un gaming con apps **o** con categorías no es inerte y no avisa.
   - **Arranque (`start_pack._run`):**
     * `failed == 0`: `self.after(0, self._inline_status, f"🚀 {started} apps iniciadas · '{nombre}'.", VERDE)`
     * `failed > 0`: `self.after(0, self._inline_status, f"⚠️ '{nombre}': {started} iniciadas, {failed} con error.", AMBAR)`
   - **Apagado (`kill_pack._run`):** el mensaje **no se escribe en la vista**, se calcula en
     `ui/feedback.py` (`mensaje_cierre_pack`) a partir de la 4-tupla que devuelven las
     puertas de cierre y se publica entero:
     `texto, color = mensaje_cierre_pack(nombre, killed, failed, skipped, freed_mb)` y después
     `self.after(0, self._inline_status, texto, color)`.

3. **Gestor de Procesos (`ProcessManagerView`):**
   - **Guarda preventiva en `on_kill_selected`:** sin selección marcada se avisa con `MSG_SIN_SELECCION`; con selección que ya no está en ejecución, con `MSG_SIN_PROCESOS`. Ninguna de las dos toca el servicio.
   - **Cierre (`_kill` → `_publicar_cierre`):** el worker solo publica —
     `self.after(0, self._publicar_cierre, killed, failed, skipped, freed_mb, len(selected_keys))` —
     y el texto sale del **mismo** `mensaje_cierre_pack` que las otras dos puertas, con el
     nombre `"{N} seleccionadas"` y el sustantivo `"procesos"`. Con `killed == 0` no hay
     tick ni verde. Tras publicar, `self._schedule_ui(1000, self.refresh_processes)` retira
     de la lista lo que ya no está corriendo.
     OJO con el `len(...)`: es `len(selected_keys)`, **no** `len(to_kill)`. El usuario marcó
     N **casillas** y cada una puede traer varios PIDs; el aviso de confirmación cuenta
     casillas, así que el resultado tiene que contar las mismas. Escribir `len(to_kill)`
     aquí no es una diferencia de estilo: reintroduce el descuadre que arregló el ciclo 26.
   - Antes (ciclo 26, iteración 3) esta puerta tenía su **propia** verdad y pintaba
     `"<tick> {killed} cerrados, {failed} fallidos."` con `killed == 0`. Era el bug que
     motivó el ciclo, y el más grave de los tres porque mata uno a uno lo que el usuario
     marcó a mano.

### El cierre dice la verdad: tres puertas, cuatro desenlaces, verde solo con éxito (ciclo 26)

Hay **tres puertas de cierre**, y las tres devuelven la **misma 4-tupla**
`(killed, failed, skipped, freed_mb)`:

| puerta | quién la llama | servicio |
|---|---|---|
| gaming | `PackManagerView.kill_pack` y `DashboardView.execute_pack` con `is_gaming` | `gaming_service.execute_gaming_pack(pack)` |
| pack | `PackManagerView.kill_pack` y `DashboardView.execute_pack` sin `is_gaming` | `process_service.kill_pack_apps(apps)` |
| seleccion | `ProcessManagerView.on_kill_selected` | `process_service.kill_processes(procesos)` |

El texto se formatea **una sola vez**, en `ui/feedback.py`, y las tres lo reciben.
Es deliberado: es la forma de no repetir el fallo del ciclo 14, donde un camino
evaluaba `p.name` y el otro `p.full_name` y uno de los dos dejaba de proteger en
silencio.

> **Alcance real de esa garantía — léase antes de citarla.** El **formateador** es
> común; la **llamada** no lo es por sí sola. Que las tres alimenten
> `mensaje_cierre_pack` no basta: hace falta que (a) ninguna construya su propio
> texto, y (b) toda rama se ejecute alguna vez en la suite. El ciclo 26 felló dos
> veces por esto: la iteración 2 arregló la puerta del Gestor de Packs y dejó
> intacta `on_kill_selected`, que pintaba `"<tick> 0 cerrados, 0 fallidos."` con
> `killed == 0`; y la rama no-gaming de la portada no se ejecutaba nunca, de modo
> que `if p.is_gaming:` y `kill_pack_apps(p.apps)` podían romperse sin que nada
> se notase. Hoy lo que lo sostiene es `test_el_feedback_de_pack_dice_la_verdad`
> (que entra por `execute_pack` con pack gaming **y** con pack normal), la sonda
> nueva `test_el_gestor_de_procesos_tampoco_miente` y la guarda AST.

`ui/feedback.py` es **puro**: solo importa `typing`, `ui.confirmation` y `ui.theme`. Ni `tkinter`,
ni `psutil`, ni `json`, ni `services`. `clasificar_cierre(killed, failed)` es el clasificador
ÚNICO de las tres puertas, con cuatro desenlaces:

| Desenlace | Cuándo | Gestor de Packs (`_inline_status`) | Portada (`_show_banner`) | Gestor de Procesos (`_publicar_cierre`) |
|---|---|---|---|---|
| **éxito** | `killed > 0`, `failed == 0` | `"✅ N procesos cerrados (X MB liberados) · 'pack'."` en **VERDE** | `"⚡ N procesos cerrados · X MB liberados"` en `GAMING`/`ACCENT` | `"✅ N procesos cerrados (X MB liberados) · 'N seleccionadas'."` en **VERDE** |
| **parcial** | `killed > 0`, `failed > 0` | `"⚠️ 'pack': N cerrados, M con error (X MB liberados)."` en ÁMBAR | `"⚠️ N procesos cerrados · X MB liberados · M con error."` en `WARNING` | idéntico al del Gestor de Packs, con `'N seleccionadas'` |
| **nada** | `killed == 0`, `failed == 0` | `"⚠️ 'pack': 0 procesos cerrados, K protegidos o ya cerrados."` en ÁMBAR | `"⚠️ Nada que cerrar: K ya cerrados o protegidos."` en `WARNING` | idéntico al del Gestor de Packs, con `'N seleccionadas'` |
| **fallo** | `killed == 0`, `failed > 0` | `"⛔ No se cerró nada de 'pack': M con error."` en ROJO | `"⛔ No se cerró nada: M procesos con error."` en `WARNING` | idéntico al del Gestor de Packs, con `'N seleccionadas'` |

`X MB liberados` es `clausula_mb(freed_mb)`, y **desaparece con `freed_mb <= 0`**: los
cuatro textos de éxito y parcial quedan entonces sin MB, y `_last_gaming_summary` en la
Portada pasa a `"N cerrados"` a secas. La regla ya estaba decidida y fijada por un test
en la otra puerta (`format_kill_result`, `notification_service.py:133`,
`run_tests.py::test_notification_message_formatting`); decir la misma verdad de dos
maneras según por dónde se ejecute es exactamente lo que `ui/feedback.py` vino a cerrar.
Y no es una LOSS de información: `"0.0 MB liberados"` es un número que el usuario no puede
cuadrar con el Administrador de tareas y que le hace sospechar de la telemetría entera.

`mensaje_cierre_pack` admite un **sustantivo parametrizable** (`"procesos"` por
defecto) para que quien hable de apps lo diga por parámetro. Duplicar el texto
por vista sería volver a tener dos verdades, que es justo lo que el módulo existe
para evitar. El parámetro se usa en **las dos ramas que lo nombran** (éxito y nada):
probándolo solo en el éxito, cablearlo a mano pasaba la suite, porque los dos
llamantes de producción pasan `"procesos"`.

### El pack que no puede hacer nada (TASK-036)

Un pack **no gaming sin apps** y un **Gaming Mode con 0 apps y 0 categorías** no producen
un resultado que clasificar: no hay 4-tupla, no se llama a ningún servicio y no hay worker.
Por eso **no son un quinto desenlace de `clasificar_cierre`** (que clasifica un resultado
real y cuyo docstring dice que no mira el pack ni la ruta) y tienen sus propios formateadores
puros, los mismos que el resto del módulo:

| caso | texto (idéntico en las dos familias) | inline | banner |
|---|---|---|---|
| pack normal sin apps | `"⚠️ '{nombre}' no tiene apps que {apagar\|iniciar}. Añádelas desde el Gestor de Procesos."` | `AMBAR` | `theme.WARNING` |
| Gaming Mode inerte | `"⛔ El Gaming Mode de '{nombre}' no tiene nada que cerrar: 0 apps y 0 categorías configuradas. Revísalo en el Gestor de Packs."` | `ROJO` | `theme.WARNING` |

- El **verbo se mapea dentro del formateador** a partir de la acción que se está
  ejecutando (`VERBOS` en `feedback.py`). Hay **tres** fuentes de la acción, no dos:
  en la Portada, `DashboardView.execute_pack` pasa `pack.default_action`, que es lo que
  decide la rama; en `PackManagerView.start_pack`, `"start"`, porque arrancar es lo que
  ese método hace aunque el pack sea gaming; y en `PackManagerView._aviso_pack_inerte`,
  `"kill"`, porque ese helper es la puerta de apagar y solo la de apagar. Quien llama
  pasa la **acción**, nunca el verbo, y nunca un literal de frase. Una acción que no
  esté en el mapa es un `KeyError` con el nombre de la puerta y la acción recibida, no un
  verbo por defecto (ver más abajo).
- **Una sola frase para las dos familias**, construida por `_frase_sin_apps` y
  `_frase_gaming_inerte`. El inventario, contado por `grep` y no de memoria: la familia
  tiene **cuatro** formateadores que devuelven `(texto, color)` —`mensaje_sin_apps`,
  `mensaje_banner_sin_apps`, `mensaje_gaming_inerte` y `mensaje_banner_gaming_inerte`—
  sobre **dos** frases privadas, y **una** guarda, `es_pack_inerte`, evaluada en **dos**
  call-site (`DashboardView.execute_pack` y `PackManagerView._aviso_pack_inerte`).
  Quien **pide** el par son **tres** call-site —`execute_pack`, `_aviso_pack_inerte`
  (invocado **dos** veces desde `kill_pack`) y `start_pack`—, es decir **cuatro
  invocaciones**. La versión anterior de esta línea decía "los cuatro call-sites":
  son cuatro *invocaciones* de tres *call-sites*, y `_aviso_pack_inerte` es un método,
  no un sitio de llamada.
  El literal del Gestor estaba **duplicado byte a byte dentro del mismo método** (las dos
  ramas de `PackManagerView._aviso_pack_inerte`, se ancla por símbolo y no por número de
  línea: la línea cambia con cada edición y el número ya caducó una vez), y esa
  duplicación es la que hizo que "un cuarto texto en la Portada" fueran cinco.
- **Los dos puntos de guarda de `_aviso_pack_inerte` están los dos medidos.** El
  auditor de cierre mutó el **segundo** (el del re-fetch por `id`, posterior a la doble
  pulsación) y el mutante **vivió**: un pack que pierde sus apps entre las dos
  pulsaciones llegaba a `kill_pack_apps([])` *después* de haber consumido la doble
  pulsación, y el usuario veía el desenlace de un cierre vacío en vez del aviso. Hoy
  `test_el_feedback_de_pack_dice_la_verdad` lo mide por la vía real —entra por `kill_pack`
  con doble pulsación y un doble de servicio que entrega el pack **con** apps en las dos
  primeras lecturas y **sin** apps en el re-fetch, y exige el aviso, cero llamadas a
  `kill_pack_apps` y cero workers—, y la matriz de la iteración 7 lo reproduce
  (`_matrix_c26.py`, mutante `K-a`, MUERE). Un doc que afirma una defensa de dos puntos
  sin medir el segundo es exactamente la clase de fallo que este ciclo vino a cerrar.
- **La tarjeta de la Portada no puede mentir con el verbo.** `_get_pack_button_text`
  toma el verbo de `pack.default_action` en las **dos** ramas, incluida la gaming: antes
  era un `"KILL"` literal congelado en la vista, cierto hoy y falso en cuanto el dato se
  mueve. Con `DEFAULT_GAMING_PACK` (que nace con `default_action="kill"`) el texto es
  idéntico al de antes; lo que cambia es que ya no es una afirmación que la vista
  mantiene sola. Lo afirma `test_el_feedback_de_pack_dice_la_verdad` por la vía real
  (`refresh_dashboard` → botón real → `cget("text")`), en las dos ramas y en las dos
  direcciones, con un Gaming Mode de `default_action="start"` como control: mutantes
  `P-d-a` y `P-d-b` de `_matrix_c26.py`, ambos MUEREN.
- **El gaming inerte es un diagnóstico, no un desenlace**: sin él, caía en la puerta real
  y pintaba `"⚠️ Nada que cerrar: 0 ya cerrados o protegidos."`, donde el `0` es el
  contador de blindaje, no de apps. El usuario leía "ya estaban cerrados" y culpaba al
  sistema operativo.
- **Nunca verde** el aviso de apps vacías (no hubo éxito) ni **nunca `DANGER`** en
  banner (`#c22d2d` sobre `SURFACE_ALT` = 3.07:1 < 4.5:1).
- **Una acción desconocida en `VERBOS` es un `KeyError`, no un verbo por defecto.** La
  versión anterior usaba `VERBOS.get(accion, VERBOS["kill"])`, y eso hacía invisible el
  bug que motivó el ciclo: como la respuesta correcta de la puerta de apagar **es**
  "apagar", un cableado erróneo (cablear un verbo donde va una acción) producía la
  respuesta correcta y nadie se enteraba. Medido: meter `"apagar"`, `"stop"` o `"Kill"`
  en la puerta de apagar **no mataba** la suite. Ahora `_verbo` lanza `KeyError` con el
  nombre de la puerta y la acción recibida.
  **Por qué fallo duro y no un tercer desenlace "verbo desconocido" que la vista
  muestre:** (1) el dominio es **total** y lo garantiza el modelo, no este módulo
  —`default_action: Literal["start", "kill"]`, todo pack entra por `Pack(**validado)` y
  un `ValidationError` ahí ya se clasifica como corrupción—, así que una acción
  desconocida no puede llegar por datos sino por un error de cableado, que es un fallo
  de programación y no una situación del usuario; (2) un tercer desenlace mete un error
  de programación **dentro de una frase dirigida al usuario** ("no tiene apps que
  &lt;verbo desconocido&gt;"), con su color y su política: es una mentira nueva en lugar
  de la que se quita, y `feedback.py` es puro y no tiene logger; (3) una `KeyError` no
  se puede silenciar con un `.get`, que es justo lo que la hacía invisible.
  El contrato del docstring ("quien llama pasa la acción, nunca el verbo") está atado en
  **dos** sitios: una guarda `ast`, al principio de `test_el_feedback_de_pack_dice_la_verdad`
  y antes de cualquier llamada, que exige que el segundo argumento de
  `mensaje_sin_apps`/`mensaje_banner_sin_apps` sea una ACCION literal o
  `pack.default_action` (mutantes `D5-e` y `D5-f` de `_matrix_c26.py`, MUEREN), y la
  frontera, que exige el `KeyError` (mutante `D5-c`, MUERE). La guarda va primero a
  propósito: si un llamante cablea un verbo, el fallo tiene que nombrar fichero y línea,
  no reventar más abajo con un traceback sin contexto.
- **Guarda antes de `_require_double_tap`, en las dos puertas.** Armar la confirmación
  sobre un pack imposible no deja nada que confirmar, y el texto que produciría
  ("Segunda pulsación para apagar 0 apps de 'X'") es la fealdad que la guarda evita.
  Sin hilo, sin `after`, sin worker: ya estamos en el hilo principal dentro de un callback.

**El canal de la Portada es `_show_aviso_banner`, no `_inline_status`.** Hay **dos**
`_inline_status` y confundirlos es como nació la incidencia de contraste que quedó
transcrita en `deuda-ciclo-26.md` (fila 8): el de la **base** (`ui/confirmation.py`) solo
configura `text` y `text_color` del label — **no pinta ningún fondo**; el **override** de la
Portada (`ui/views/dashboard_view.py`) sí configura `fg_color=CANCEL` (`#5a4a1e`), la familia
del aviso de "confirmación pendiente". Todo lo que sigue habla del override. Un aviso
permanente con ese fondo se lee como "espera la segunda pulsación"; y **nunca se
auto-oculta** (llama a `pack()` y no a `_reprogramar_autoocultado()`), con lo que dejaría
el aviso pegado contra la regla de `_on_expirado`. `_show_aviso_banner` publica sobre
`theme.SURFACE_ALT` y programa el auto-ocultado, como las otras dos puertas. Las tres
comparten ahora la única línea de publicación, `_publicar_en_banner` (fondo, texto, color,
`pack(...)` y `_reprogramar_autoocultado()`): el bloque era de cuatro líneas y estaba
copiado en dos sitios, y la tercera puerta iba a ser la tercera copia.

Por dónde sale, entonces, cada diagnóstico, y por qué ninguno cae sobre `CANCEL`:

| diagnóstico | canal | fondo real | color |
|---|---|---|---|
| Gaming inerte en la **Portada** | `_show_aviso_banner` → `_publicar_en_banner` | `theme.SURFACE_ALT` | `theme.WARNING` |
| Gaming inerte en el **Gestor** | `_inline_status` **de la base** (`confirmation.py`) | ninguno: el de reposo (`transparent`) | `ROJO` |
| Aviso de pack sin apps | igual, el de la vista que lo publica | el de reposo de su label | `AMBAR` / `theme.WARNING` |

Lo mide `test_el_feedback_de_pack_dice_la_verdad`: el bloque (f) para la mitad banner
(`status_banner_frame.cget("fg_color") == theme.SURFACE_ALT`) y el bloque de contrato de
canal de la guarda de `start_pack` para la mitad inline (el `fg_color` del label del Gestor
sigue siendo el de reposo tras publicar el diagnóstico ROJO). Si alguien pintara el canal
inline con `CANCEL`, el test muere con `Reposo: 'transparent', despues: '#5a4a1e'`.

Dos reglas que no se pueden relajar:

- **El verde es una promesa, no un adorno.** Con cero cerrados no hay tick ni verde. Antes
  (ciclo 26, `mutation-auditor` con sonda en runtime) `kill_pack` pintaba
  `"✅ 0 procesos cerrados (0.0 MB liberados)"` en VERDE Gaming con un pack sin apps vivas: todo en
  `keepers`, pack ya vacío, rutas muertas. Es la misma clase que el contador `started` del ciclo 20.
  En la iteración 3 el mismo defecto seguía vivo, literal, en `on_kill_selected`.
- **`skipped` no es "fallaron".** `kill_processes` lo suma por blindaje `is_system_protected`
  (TASK-024) o por `NoSuchProcess` (ya no estaba), y `execute_gaming_pack` le suma además los
  descartes del filtro de `keepers` (G9). Por eso el mensaje dice "protegidos o ya cerrados".
  El mensaje viejo de `on_kill_selected` fundía los dos en "fallidos".

`_show_banner` mantiene la firma anterior y **añade** `failed` y `skipped` con valor por defecto
`0`, de modo que una llamada antigua no rompe; el worker `_run_kill` sí los pasa.

La portada **no** usa `theme.DANGER` en el desenlace "fallo" a propósito: `#c22d2d` sobre
`SURFACE_ALT` da **3.07:1** y el design system exige 4.5:1 (§4 Accesibilidad). El fallo se
distingue por el texto (`⛔`), no inventándose un par de color que no cumple.

### Invariantes de Hilos y Red de Seguridad
- **Cero mutaciones directas de widgets desde hilos secundarios:** Todo worker de fondo (`_run`, `_run_kill`, `_run_start`, `_load`, `_kill`) delega las mutaciones exclusivamente a través de `self.after(0, callback, *args)`. El worker **no arma callbacks anidados**: publica siempre en un método de la vista, que es lo que permite que la guarda AST lo verifique por nombre.
- **Análisis AST, con la lista de lo permitido como PARES `(raiz, metodo)`, no de raíces:** la sonda `test_los_workers_de_pack_solo_publican_por_after` analiza el **objetivo real de cada `threading.Thread(target=...)`** de cinco métodos de tres clases de vista: `DashboardView.execute_pack`, `PackManagerView.kill_pack`, `PackManagerView.start_pack`, `ProcessManagerView._do_load` y `ProcessManagerView.on_kill_selected`. Esa lista es **explícita y está en el bucle de aplicación del test**, a la vista: añadir un worker nuevo sin añadirlo ahí es un hueco, y el docstring de la sonda lo dice. Lo que la guarda marca como infracción, dicho con sus límites, es **toda llamada o escritura que se resuelva sobre `self` por `Attribute`, por `Subscript`, por `getattr`/`setattr`/`delattr`, por `del`, o pasada como argumento de una llamada permitida**. Se exige que **cada** `self.after` del worker lleve `0` ms y un callback de la lista blanca, no solo el primero que aparece. `self.master.after` cae solo por la regla (par `("master", "after")`, no permitido).
  - **Comparar solo la raíz NO alcanza** (medido en la iteración 3 del ciclo 26): con una lista de raíces, `self.pack_service.get_all_packs()` y `self.process_service.get_process_exe_path(1)` pasaban. El par es la unidad de comparación.
  - **Comparar solo `call.func` tampoco** (medido en la iteración 4): `getattr(self, 'status_label').configure(...)` —la misma llamada de widget de siempre, con el `Attribute` partido en dos—, `setattr(self, '_last_gaming_summary', 'x')`, `del self._last_gaming_summary` y `self.process_service.kill_pack_apps(self.status_label)` pasaban las cuatro. La guarda bajaba por `Attribute` y por `Subscript`, y eso son dos de las cinco formas de llegar a `self`.
  - La guarda se prueba **contra sí misma** con código sintáctico en las dos direcciones: ocho infracciones que tiene que ver (método de widget, `self.master.after`, escritura en `self`, `del self.<attr>`, `getattr`/`setattr` sobre la vista, `self.<attr>` como argumento de una llamada permitida, tres métodos prohibidos de raíces permitidas y dos de la puerta de atrás por `__dict__`), un worker conforme que no puede marcar, y un worker de dos ramas en el que tiene que ver *las dos*.
  - **Lo que la guarda NO comprueba**, sin adornos: los `threading.Thread` de `ui/app.py` (el toast de arranque y el hilo del icono de la bandeja), que no son vistas; cualquier worker añadido después de esa lista sin añadirlo ahí; **un alias local** (`lbl = self.status_label` y luego `lbl.configure(...)` no se resuelve hasta `self`, y ese agujero no lo cierra un análisis estático de este tipo); y tampoco que el `after` se ejecute de verdad en el hilo principal ni el resultado de la operación: eso lo cubren las sondas dinámicas con hilo secundario real. Una promesa de "todo lo que cuelgue de `self` es infracción" es más fuerte que lo que el detector cumple, y por eso este párrafo enumera las cinco formas en vez de decir "todo".
- **Gestión de temporizadores:** el bloque de "cancelar el anterior y programar el nuevo" está **extraído a un único método**, `DashboardView._reprogramar_autoocultado()`, al que llaman las **tres** puertas del banner (`_show_start_banner`, `_show_banner` y `_show_aviso_banner`). Estaba duplicado byte a byte y, con la sonda instrumentando solo la primera, tres mutaciones vivían en `_show_banner` (la que el gamer ve tras pulsar "Apagar"): borrar la cancelación, mover los 5000 ms a 60 000 y quitar el `_timers_ui.discard` (que dejaba el handle vivo y lo volvía a cancelar al destruir). El auto-ocultado son **5000 ms** (`dashboard_view.AUTOOCULTADO_MS`), y la sonda los mide con un **reloj simulado de plazo absoluto** en **las dos** puertas de cierre: t0 primer banner, t=1000 segundo banner, lectura a t=5500 y auto-ocultado a t=6500, sin esperar 5,5 s reales; y en la tercera puerta (el aviso de pack inerte) con el mismo reloj, para que un aviso pegado en la portada muera igual que un temporizador que no vence. Además afirma que tras reprogramar queda **exactamente un** handle en `_timers_ui` y que sale al dispararse. `_hide_banner` lo limpia a `None` y `destroy()` cancela el timer pendiente antes de `cancel_on_destroy()`.
- **Alias muertos: no.** `_show_kill_banner = _show_banner` estaba en `DashboardView` sin que nadie lo llamara; lo único que lo sostenía era su propio nombre en la lista blanca de la guarda. Es el mismo patrón que perdió el ciclo 22, así que se borró de los dos sitios.

