# Modelos de Datos y Persistencia (v3)

## Esquema Pydantic (`src/woptimizer/models.py`)

### 1. `ProcessInfo`
Representa un proceso en memoria listado mediante `psutil`:
- `name`: Nombre limpio sin extensión (ej: `chrome`).
- `full_name`: Nombre con extensión (ej: `chrome.exe`).
- `pid`: ID numérico del proceso en Windows.
- `exe_path`: Ruta completa al ejecutable en disco (si es accesible).
- `category`: Categoría asignada (ej: `🔴 Navegadores`).
- `priority`: Nivel de prioridad (`high`, `medium`, `low`, `none`).

### 2. `Pack` (Concepto Unificado)
Reemplaza a los perfiles legacy. Un pack puede ser lanzado (abrir) o cerrado (apagar):
```python
class Pack(BaseModel):
    id: str                                  # Clave única
    name: str                                # Nombre visible
    apps: List[str] = Field(default_factory=list) # Lista de ejecutables (ej: ['chrome.exe'])
    is_favorite: bool = False                # Si se muestra en la portada
    is_gaming: bool = False                  # Si es el preset protegido del sistema
    default_action: str = "kill"             # Acción rápida por defecto ('kill' o 'start')
    keepers: List[str] = Field(default_factory=list) # Apps protegidas en gaming (ej: ['discord.exe'])
    target_categories: List[str] = Field(default_factory=list) # Categorías a cerrar dinámicamente en Gaming
```

### 3. `AppData` (Estructura de `profiles.json`)
```python
class AppData(BaseModel):
    packs: Dict[str, Pack] = Field(default_factory=dict)
```

## Reglas de Persistencia
- Archivo en disco: `profiles.json` ubicado en el directorio de la aplicación (`_app_dir()`).
- Si el archivo no existe o se corrompe, el servicio debe regenerar de inmediato el pack protegido `gaming` por defecto:
  - `id`: `"gaming"`
  - `name`: `"🚀 Preparar para Gaming"`
  - `is_favorite`: `True`
  - `is_gaming`: `True`
  - `keepers`: `["discord"]`
  - `apps`: `[]`
- El pack con `is_gaming = True` **NUNCA** puede ser eliminado por el usuario.

### 4. Respaldo Preventivo (Backups)
- En cada guardado exitoso de `profiles.json`, se crea de forma atómica una copia de seguridad `profiles.json.bak` mediante `shutil.copy` para prevenir corrupciones.

## Base de Datos de Procesos (`assets/process_db.json`)

### Esquema
`dict[str, dict]`. La clave es el **nombre del proceso en minúsculas y sin extensión**
(`chrome`, no `chrome.exe`) y el valor es un `dict` con exactamente tres campos:

```json
"powertoys": {
    "category": "🟢 Productividad",
    "priority": "high",
    "description": "PowerToys de Microsoft. Reconstruye unos 20 procesos al iniciar sesion..."
}
```

- `category`: tiene que existir **literalmente** (emoji incluido) como clave de
  `PROCESS_CATEGORIES` en `config.py`. Si no coincide, el lookup falla y el proceso cae en
  `? Otros` perdiendo su semáforo. Lo cubre `test_category_emoji_alignment` con un diff de
  conjuntos entre ambos ficheros.
- `priority`: `high` | `medium` | `low` | `none`. El semáforo visible lo manda la categoría
  (emoji 🔴/🟡/🟢); la prioridad solo desempata categorías desconocidas.

### Blindaje anti-brick (TASK-024)

Los procesos de nivel sistema cuyo cierre deja Windows inservible (`csrss`, `lsass`,
`winlogon`, `wininit`, `services`, `smss`, `dwm`, `System`, `Registry`, `fontdrvhost`,
`audiodg`, `RuntimeBroker`…) **no pueden ofrecerse nunca como cerrables**, ni siquiera si
alguien los registra por error en el JSON.

- Lista canónica: `SYSTEM_PROTECTED_PROCESSES` (un `frozenset`) en
  `src/woptimizer/services/process_service.py`. Coincidencia **exacta** sobre el nombre
  normalizado (`_normalizar_nombre`: minúsculas, sin `.exe`), nunca por subcadena: el
  matching del servicio acepta subcadenas y un nombre genérico bloquearía procesos
  legítimos. No confundir con los `patterns` legacy de `PROCESS_CATEGORIES['🔴 Sistema de
  Windows']`, que incluyen procesos del usuario (`taskmgr`, `cmd`, `powershell`, `wsl`).
- Se comprueba en **tres puntos**, todos antes de tocar el sistema operativo:
  1. `_load_local_db()` sanea el hashmap al cargar: una entrada de la Familia A se fuerza a
     `("🔴 Sistema de Windows", "none", ...)` aunque el JSON diga `🟢/high`.
  2. `_get_process_meta()` la consulta **antes** que la DB y que el fuzzy match, así que un
     proceso de sistema no puede heredar la categoría de otro patrón.
  3. `kill_processes()` y `kill_pack_apps()` la comprueban sobre el PID/nombre recibido: un
     pack escrito a mano con `lsass.exe` se cuenta como `skipped` y no mata nada.
- Cobertura: `test_no_system_process_is_killable` en `run_tests.py` falla si (a) alguien
  degrada una entrada de la Familia A a cerrable en el JSON, (b) la lista de protección deja
  de cubrir el núcleo duro, o (c) el blindaje deja de forzar 🔴/`none` con un JSON
  envenenado a propósito.

### Qué entra y qué no
- **Sí**: bloatware y telemetría de terceros (PowerToys, procesos de consumo de Armoury Crate,
  mejoras de audio, language servers, actualizadores de drivers). Van a `🟢 Productividad`
  (`high`) o `🟡 Media y Streaming` (`medium`) cuando tocan la ruta de audio.
- **No**: el entorno de trabajo del usuario (`pwsh`, `python`, `wsl`, terminales) — cerrarlos
  rompería su propia sesión; y las pilas de control de hardware (`armsvc`, `asus_framework`,
  `rogliveservice`) van a `🔴 Overlays e Info` / `none`, igual que `icue`, `razer` o `lghub`,
  porque cerrarlas deja el equipo sin perfil de ventilación o RGB.

