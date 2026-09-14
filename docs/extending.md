# Extending — Cómo añadir features sin romper nada

> ⚠️ **REGLA:** Una feature a la vez. Test después de cada cambio.

## Workflow seguro para añadir features

```
1. Pensar la feature
2. Implementar cambio mínimo
3. Ejecutar verify_app.py → debe seguir abriendo
4. Si es feature de kill → ejecutar test_kill_real.py → debe matar
5. Si algo falla → revertir y pensar
6. Solo cuando todo pasa → commit
```

## Cómo añadir una nueva categoría gaming

Editar `PROCESS_CATEGORIES` en `process_manager.py`:

```python
PROCESS_CATEGORIES = {
    '🔴 Navegadores': { ... },  # existente
    # AÑADIR:
    '🟠 Mi nueva categoría': {
        'priority': 'high',     # high/medium/low/none
        'patterns': ['miproceso', 'miproceso2'],
        'description': 'Qué hace esta categoría',
    },
}
```

Y añadir la clave al final de `CATEGORY_ORDER`:

```python
CATEGORY_ORDER = [
    '🔴 Navegadores',
    # ...
    '🟠 Mi nueva categoría',  # ← aquí
]
```

Si quieres que aparezca en modo Simple:

```python
SIMPLE_CATEGORIES = [
    '🔴 Navegadores',
    # ...
    '🟠 Mi nueva categoría',  # ← aquí
]
```

**Test:** `python verify_app.py` y verificar visualmente.

## Cómo añadir un nuevo botón de acción

1. Crear el botón en `create_widgets()`:
```python
btn_mi_accion = tk.Button(actions_frame, text="Mi acción",
                          command=self.mi_accion, ...)
btn_mi_accion.pack(side=tk.LEFT, padx=5)
```

2. Añadir el método en la clase:
```python
def mi_accion(self):
    # tu lógica
    pass
```

3. Test: `python verify_app.py`

## Cómo modificar el script PowerShell

⚠️ **ZONA PELIGROSA.** Lee [`known-issues.md`](known-issues.md) antes de tocar.

Reglas:
- NUNCA uses `$pid` (variable reservada)
- NUNCA uses `-replace "patron", "[PIPE]"` (regex char class)
- SIEMPRE usa TAB como delimitador
- SIEMPRE excluye `powershell.exe` y `pwsh.exe` (su CommandLine contiene el script completo)
- SIEMPRE fuerza UTF-8: `$OutputEncoding = [System.Text.Encoding]::UTF8`

Test de regresión tras cualquier cambio PowerShell:
```bash
python test_kill_real.py
```

## Cómo añadir un atajo de teclado

En `create_widgets()`:

```python
self.root.bind('<F6>', lambda e: self.mi_accion_con_teclado())
```

Lista de teclas: `<F1>` a `<F12>`, `<Control-x>`, `<Alt-x>`, `<Shift-x>`, `<Escape>`, `<Delete>`, etc.

Test: `python verify_app.py` + abrir la GUI y pulsar la tecla.

## Cómo añadir persistencia (más campos en saved_processes.json)

1. Modificar `kill_processes()` para incluir el nuevo campo en el dict
2. Modificar `save_processes_to_relaunch()` si cambia la estructura
3. La lectura (`load_saved_processes()`) usa `JSON.parse` que ignora campos extra → no breaking

**Compatibilidad hacia atrás:** añadir campos es seguro. Eliminar campos requiere migración.

## Cómo añadir un endpoint API (si vuelves a Mini App)

Cuando MiniMax Code solvente el EACCES, en `server.mjs`:

```javascript
if (method === 'GET' && path === `${apiBase}/mi-endpoint`) {
    // tu lógica
    sendJson(res, 200, { data: ... });
    return;
}
```

Patrón ya establecido en `handleRequest()`.

## Anti-patrones

❌ **Añadir 5 features a la vez** → imposible validar cuál rompe
❌ **Cambiar formato de saved_processes.json sin migrar** → pierdes datos del usuario
❌ **Auto-elevation sin fallback visible** → app muere silenciosa
❌ **Usar variables reservadas en PowerShell** → `$pid`, `$Host`, `$PSVersionTable`, etc.

## Cómo revertir si algo se rompe

```bash
# Ver el último cambio (si usas git)
git diff process_manager.py

# Revertir cambios
git checkout process_manager.py

# O restaurar desde .pyw (que es copia)
Copy-Item process_manager.pyw process_manager.py -Force
```

Si no usas git, restaura desde backup o reescribe la sección problemática.

## Cómo pedir feedback al usuario tras cambios

```
"He aplicado [cambio]. Validado:
- verify_app.py: PASS
- test_kill_real.py: PASS
- Sincronizado .pyw

¿Quieres probarlo manualmente con doble clic?"
```

No asumas. Espera confirmación.
