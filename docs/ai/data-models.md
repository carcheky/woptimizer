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
