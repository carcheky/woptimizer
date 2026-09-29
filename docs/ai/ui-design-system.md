# Sistema de Diseño y Flujo UI CustomTkinter (v3)

## Arquitectura de Vistas (3 Ventanas/Paneles)

### 1. Ventana Principal (Portada / Dashboard)
- **Propósito:** Ejecución ultra rápida de un solo clic al sentarse a jugar o volver a trabajar.
- **Contenido Central:**
  - Botones gigantes para los packs marcados como `is_favorite = True`.
  - El botón del pack Gaming tiene estilo prioritario (color acentuado rojo `#c22d2d`).
  - Al hacer clic en un favorito, ejecuta su acción principal (apagar para gaming, arrancar para packs de trabajo).
- **Barra de Navegación Inferior:**
  - Botón `📁 Gestor de Packs`: Abre la vista de gestión completa.
  - Botón `⚡ Gestor de Procesos`: Abre la vista de procesos activos.

### 2. Gestor de Packs (`views/pack_manager_view.py`)
- **Propósito:** Crear, editar y ejecutar packs de aplicaciones.
- **Contenido:**
  - Botón superior `➕ Nuevo Pack`.
  - Lista scrollable con tarjetas para cada pack.
  - Cada tarjeta de pack incluye:
    - Nombre del pack y cantidad de apps configuradas.
    - Botón `⭐` para alternar si es favorito (aparece en portada).
    - Botón `⛔ Apagar Apps`: Cierra todos los ejecutables del pack vía `process_service`.
    - Botón `🚀 Arrancar Apps`: Lanza todos los ejecutables configurados vía `subprocess.Popen`.
    - Botón `✏️ Editar`: Abre modal para añadir/quitar apps o keepers.
    - Botón `🗑️ Borrar`: Elimina el pack (deshabilitado si `is_gaming = True`).

### 3. Gestor de Procesos en Vivo (`views/process_manager_view.py`)
- **Propósito:** Explorar qué está consumiendo recursos y agregarlo a packs fácilmente.
- **Contenido:**
  - Botón superior `🔄 Actualizar Lista`.
  - Buscador de texto en tiempo real.
  - Lista agrupada por categorías (`🔴 Navegadores`, `🟡 Chat`, etc.) con checkboxes.
  - Barra de acción inferior fijada:
    - Desplegable `Añadir seleccionados a: [Seleccionar Pack ▼]`.
    - Botón `➕ Añadir al Pack`.
    - Botón `⛔ Cerrar Seleccionados Ahora`.

## Reglas de CustomTkinter
- **Tema:** Modo oscuro forzado (`ctk.set_appearance_mode("Dark")`).
- **Fuentes:** Utilizar familias de sistema estándar (`"Segoe UI"` en Windows).
- **Hilos de Fondo:** Toda operación de listado o kill pesado debe correr en un `threading.Thread(daemon=True)` para que la interfaz nunca se congele, actualizando la UI mediante `master.after(0, callback)`.

## Especificaciones de Pantalla y Responsive (14 Pulgadas)
- **Dimensiones:** Ventana inicial de `860x560` (mínimo `720x460`) optimizada para portátiles de 14" con escalado de Windows de 125% a 150%.
- **Semáforo Visual de Seguridad (`get_safety_badge`):**
  - `🟢 SEGURO`: Verde brillante (`#40c057`) sobre fondo verde oscuro (`#163820`). Cierre recomendado (Browsers, Sync, Productividad).
  - `🟡 PRECAUCIÓN`: Amarillo ámbar (`#fcc419`) sobre fondo amarillo oscuro (`#3d3711`). Apps de juegos/media (Launchers, Discord, Spotify).
  - `🔴 NO CERRAR`: Rojo vibrante (`#ff6b6b`) sobre fondo rojo oscuro (`#401616`). Vitales para el SO o hardware (Windows, drivers, antivirus).
- **Gestor de Packs Compacto:**
  - Toolbar de acciones en tarjetas de pack limitada a ~270px para evitar colisiones con el título.
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
    killed, failed, skipped, freed_mb = process_service.kill_pack_apps(p.apps)
    self.after(0, self._show_banner, killed, freed_mb, p.is_gaming)

threading.Thread(target=_run_kill, args=(pack,), daemon=True).start()

# En el hilo principal (after callback):
def _show_banner(self, killed: int, freed_mb: float, is_gaming: bool):
    # … actualizar status_label y hacer pack() del frame …
    self.after(5000, self._hide_banner)
```

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
DashboardView(self.content_frame, self.process_service, self.pack_service, self.notification_service)
PackManagerView(self.content_frame, self.process_service, self.pack_service, self.notification_service)
ProcessManagerView(self.content_frame, self.process_service, self.pack_service, self.notification_service)
```

Todas las vistas aceptan `notification_service=None` y crean un local si no se les pasa, de modo que los constructores antiguos y los tests headless siguen funcionando.

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

### Invariantes a Respetar
- **Se congela la INTENCIÓN, se recalculan los DATOS.** El token de `on_kill_selected` es el conjunto de claves marcadas; los `ProcessInfo` se recalculan en la segunda pulsación. Entre pulsaciones el PID se recicla: matar un `ProcessInfo` congelado es matar a un inocente.
- **Cambiar la selección invalida y re-arma** (mensaje "⚠️ Selección cambiada. Vuelve a pulsar para confirmar."), no ejecuta con la intención vieja. Se usa `changed_text=` para ese mensaje.
- **El token es el `id` del pack, nunca el objeto `Pack`**: `reset_gaming_pack()` re-empaqueta con `model_copy(deep=True)` y una referencia capturada puede quedar obsoleta. Re-fetch por `id` al confirmar.
- **`self.after(...)`, nunca `self.master.after(...)`.** Toda navegación destruye la vista y crea otra; `master` es `content_frame`, que sobrevive, y el callback huérfano reconfigura widgets destruidos.
- **Se cancela en `destroy()`, en `refresh_packs()`/`refresh_dashboard()` y ANTES de ejecutar la acción confirmada** (la propia acción puede destruir el botón, caso `remove_app_from_pack`).
- Solo hay una pendiente viva por vista: pulsar otra acción distinta la descarta.
- `ui/confirmation.py` solo importa `typing`; prohibido `psutil`, `json`, `services` y `models` (§7.4 de la OpenSpec). El guard de imports vive en `run_tests.py::test_double_tap_guard`.
- **Nada se traga en silencio:** los fallos de `delete_pack` (pack de sistema / inexistente) se muestran en el `status_label`, nunca `except: pass`.
