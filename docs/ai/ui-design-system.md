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
- `auto-hide` a los 5 s con `self.after(5000, self._hide_banner)` para no saturar la UI.
