# Testing

> ⚠️ **REGLA DE ORO:** Nunca digas "listo" sin haber validado con un test real.

## Scripts de validación incluidos

### `verify_app.py`

Lanza `python process_manager.py`, espera 4 segundos, verifica que el proceso sigue vivo (señal de que la GUI está abierta y funcionando).

```bash
python verify_app.py
```

**PASS esperado:**
```
[verify] Lanzando: python ...\process_manager.py
[verify] Esperando 4s para que la GUI se abra...
[verify] PASS - PROCESO VIVO tras 4s (PID=...). GUI abierta.
[verify] PASS - la app arranca correctamente
```

**FAIL diagnóstico:**
- Proceso muere en <4s → hay un `sys.exit()` o crash en imports
- Proceso vivo pero con stderr → revisar el stderr

### `verify_pyw.py`

Igual pero con `pythonw.exe` (sin consola) — simula el flujo real del `.vbs`.

```bash
python verify_pyw.py
```

### `test_kill_real.py`

**El más importante.** Lanza `notepad.exe`, lo lista con `get_running_processes()`, lo mata con `kill_processes()`, verifica que murió.

```bash
python test_kill_real.py
```

**PASS esperado:**
```
[test] notepad.exe lanzado con PID=...
[test] notepad ENCONTRADO: name=Notepad, pid=...
[test] killed=1, failed=0
[test] notepad murio con codigo: 1
[test] PASS - kill_processes funciona correctamente
```

**FAIL diagnóstico:**
- notepad NO encontrado → bug en `get_running_processes` (probablemente `$pid` reservado)
- killed=0, failed>0 → `taskkill` falla por permisos o PID incorrecto
- notepad sigue vivo tras kill → matar no funcionó

### `test_harness.py`

Test E2E original: arranca PowerShell con sleep → kill → save → relaunch → verify alive → cleanup.

```bash
python test_harness.py
```

Más lento pero valida el ciclo completo.

### `smoke_check.py`

Valida sintaxis AST rápida, presencia del helper `_app_dir()` (Trampa #17 para frozen mode) y versión esperada en `process_manager.py`.

```bash
python smoke_check.py
```

### `validate_docs.py`

Verifica cumplimiento del formato `llms.txt` (Answer.AI v2), completitud de `llms-full.txt`, estructura canónica de `openspec/` y reglas SDD en `AGENTS.md`.

```bash
python validate_docs.py
```

### `test_gaming_profile.py`

Suite de tests para el perfil de sistema Gaming (`__system_gaming__`): creación en primer arranque, persistencia de keepers, toggle de `kill_low_chat`, reset a fábrica, protección contra borrado y auto-recuperación de `profiles.json` corrupto.

```bash
python test_gaming_profile.py
```

### `verify_exe.py`

Verifica la integridad del ejecutable `dist\woptimizer.exe`: tamaño mínimo, cabecera PE válida, PyInstaller >=5.13, manifest `requireAdministrator` embebido y auto-elevación vía UAC en Windows.

```bash
python verify_exe.py
```

---

## Patrón de validación para cambios

Antes de decir "listo" tras modificar el código, ejecuta en este orden:

```bash
# 1. Sintaxis OK
python -c "import py_compile; py_compile.compile('process_manager.py', doraise=True)"

# 2. App arranca con python
python verify_app.py

# 3. App arranca con pythonw
python verify_pyw.py

# 4. Kill funciona con proceso real
python test_kill_real.py

# 5. Sincronizar .pyw
Copy-Item process_manager.py process_manager.pyw -Force
```

Si los 4 pasan → cambio OK.

Si alguno falla → **NO** marques como completo. Investiga, arregla, reintenta.

---

## Tests manuales del usuario

El usuario debe verificar manualmente:

| Test | Cómo |
|------|------|
| GUI abre sin consola | Doble clic en `ProcessManager.vbs` |
| Lista carga | Esperar 2-3s, ver categorías con iconos |
| Búsqueda funciona | Escribir "chrome" en buscador |
| Kill funciona | Seleccionar chrome, click Matar → confirma |
| Relanzar funciona | Click Relanzar → procesos vuelven |
| Atajos | F5, Ctrl+A, Delete, Escape |

---

## Anti-patrones que NO debes usar

❌ **"Debería funcionar, lo probé mentalmente"** → NO. Ejecuta.
❌ **"Lo dejo como está, parece OK"** → NO. Verifica con test real.
❌ **"Cambio múltiples cosas a la vez"** → NO. Un cambio → test → siguiente.
❌ **"El usuario ya lo validará"** → NO. Valida tú primero con tests automatizados.

---

## Debug rápido cuando algo no funciona

```bash
# 1. Sintaxis
python -c "import py_compile; py_compile.compile('process_manager.py', doraise=True)"

# 2. Imports funcionan (sin GUI)
python -c "import process_manager; print('imports OK')"

# 3. Get_running_processes funciona solo
python -c "import process_manager as pm; procs = pm.get_running_processes(); print(f'{len(procs)} procesos')"

# 4. Kill funciona solo
python test_kill_real.py

# 5. Test completo
python verify_app.py
```

Si todos pasan pero la GUI no → problema de tkinter (raro).
Si get_running_processes falla → problema PowerShell (probablemente `$pid`).
Si kill falla → problema de taskkill (permisos o PID incorrecto).
