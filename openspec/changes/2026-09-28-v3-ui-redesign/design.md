# Technical Design: v3-ui-redesign

## Diagrama de Navegación y Vistas

```
              ┌────────────────────────┐
              │   VENTANA PRINCIPAL    │
              │       (Portada)        │
              │                        │
              │  [🚀 GAMING (Fav)]     │
              │  [📦 Mi Setup (Fav)]   │
              │                        │
              │ [Packs]    [Procesos]  │
              └────┬───────────┬───────┘
                   │           │
       ┌───────────┘           └───────────┐
       ▼                                   ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│     GESTOR DE PACKS     │     │   GESTOR DE PROCESOS    │
│                         │     │                         │
│ - [Gaming] (Fijo)       │     │ [x] chrome.exe          │
│   [Apagar] [Arrancar]   │     │ [ ] spotify.exe         │
│ - [Dev Pack]            │     │ [x] discord.exe         │
│   [Apagar] [Arrancar]   │     │                         │
│                         │     │ [Añadir a: Pack v] [➕] │
│ [+ Nuevo Pack]          │     │                         │
└─────────────────────────┘     └─────────────────────────┘
```

## Estructuras de Datos (`models.py`)

```python
class Pack(BaseModel):
    id: str
    name: str
    apps: List[str] = Field(default_factory=list)
    is_favorite: bool = False
    is_gaming: bool = False
    extra_kill_patterns: List[str] = Field(default_factory=list)
    keepers: List[str] = Field(default_factory=list)

class AppData(BaseModel):
    packs: Dict[str, Pack] = Field(default_factory=dict)
```

## Componentes UI (`src/woptimizer/ui/`)
1. `app.py`: Coordinador de navegación entre vistas (usando contenedores/frames intercambiables o ventanas modales de CustomTkinter `CTkToplevel`).
2. `views/dashboard_view.py`: Portada con widgets de favoritos y botones a los otros 2 paneles.
3. `views/pack_manager_view.py`: Gestión CRUD de packs, lista expandible y botones de acción (apagar/encender).
4. `views/process_manager_view.py`: Lista con scroll de procesos activos (agrupados por nombre y PID), buscador en tiempo real, categorías plegables para UX mejorada, y agregador directo a packs.
