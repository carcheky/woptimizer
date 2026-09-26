# Capability: woptimizer

Capacidad raíz del producto. Cualquier submódulo (kill, profiles, gaming, executable) refina estos requisitos.

## Purpose

woptimizer es un Process Manager con foco gamer para Windows: lista procesos, los cierra por categoría o app, persiste listas, relanza perfiles, y prepara la máquina para gaming matando distracciones. Distribución principal: `dist\woptimizer.exe` standalone (auto-eleva como admin).

## Requirements

### Requirement: Process listing
The system SHALL listar todos los procesos en ejecución del host usando PowerShell 5.1+ vía subprocess con `CREATE_NO_WINDOW = 0x08000000`. Cada proceso SHALL incluir al menos: `pid`, `name`, `cmdline` (truncado a `MAX_CMDLINE_LEN`).

#### Scenario: Lista exitosa
- WHEN el usuario pulsa "Actualizar" en la GUI
- THEN la lista muestra todos los procesos en <2s sin abrir ventanas de consola

#### Scenario: PowerShell no disponible
- WHEN PowerShell 5.1+ no está en PATH
- THEN el sistema SHALL mostrar un error claro en el `status_label` con instrucciones

### Requirement: Process killing
The system SHALL matar procesos por PID usando `taskkill /F /T /PID <pid>` (no `proc.kill()` solo). Tras el kill, SHALL verificar post-estado en <500ms.

#### Scenario: Kill de proceso simple
- WHEN el usuario confirma el kill (doble tap) de un proceso con PID 1234
- THEN `taskkill /F /T /PID 1234` se ejecuta y el proceso desaparece de la lista en el siguiente refresh

#### Scenario: Kill con hijos
- WHEN el proceso tiene procesos hijos (ej. navegador con renderers)
- THEN `/T` mata el árbol completo

### Requirement: Profiles persistence
The system SHALL persistir perfiles de relanzado en `profiles.json` ubicado junto al ejecutable (no en cwd). SHALL soportar crear, editar, borrar, marcar favorito, lanzar.

#### Scenario: Primer arranque
- WHEN el archivo `profiles.json` no existe
- THEN `load_profiles()` lo crea con un perfil de sistema `__system_gaming__` (factory defaults)

#### Scenario: Frozen mode
- WHEN la app corre como `.exe` PyInstaller
- THEN `profiles.json` se crea junto al `.exe` (vía helper `_app_dir()`), NO en `sys._MEIPASS`

### Requirement: Gaming system profile
The system SHALL mantener un perfil de sistema `__system_gaming__` no borrable, con `keepers` (lista de strings a mantener) y un toggle `kill_low_chat` (matar chat de baja prioridad). SHALL ser reseteable a factory defaults.

#### Scenario: Reset a fábrica
- WHEN el usuario pulsa "Reset a valores de fábrica"
- THEN keepers vuelven a `["discord"]` y `kill_low_chat` a `True`

#### Scenario: Borrado intentado
- WHEN el usuario intenta borrar el perfil gaming
- THEN el botón "🗑️ Borrar" está deshabilitado y la operación se rechaza silenciosamente

### Requirement: GUI confirmation (doble tap)
The system SHALL usar doble tap en el mismo botón para acciones destructivas (no `messagebox.askyesno`). Tras el primer tap SHALL cambiar el texto del botón a "⚠️ PULSA OTRA VEZ" durante 3s, y restaurar si no hay segundo tap.

#### Scenario: Primer tap solo
- WHEN el usuario pulsa "⛔ Matar" una vez
- THEN el botón cambia a "⚠️ PULSA OTRA VEZ" durante 3s y vuelve a su estado normal

#### Scenario: Doble tap antes de timeout
- WHEN el usuario pulsa "⛔ Matar" dos veces en menos de 3s
- THEN se ejecuta el kill con la selección actual

### Requirement: Standalone executable
The system SHALL distribuirse como `dist\woptimizer.exe` (single-file, 9-12 MB) construido con PyInstaller `--onefile --noconsole --uac-admin`. El ejecutable SHALL funcionar en Windows 10/11 sin Python instalado.

#### Scenario: Doble clic limpio
- WHEN el usuario hace doble clic en `woptimizer.exe`
- THEN aparece UAC prompt (auto-eleva), tras aceptar se abre la GUI sin consola visible

#### Scenario: Primera ejecución
- WHEN el .exe arranca por primera vez en una carpeta
- THEN `profiles.json` se crea junto al .exe con gaming profile por defecto

### Requirement: Documentation discoverability (SDD)
The project SHALL publicar `llms.txt` y `llms-full.txt` en la raíz del repo para carga selectiva por agentes IA. SHALL seguir la propuesta OpenSpec para que cualquier cambio futuro empiece con un proposal en `openspec/changes/`.

#### Scenario: Agente externo lee llms.txt
- WHEN un agente IA abre `llms.txt`
- THEN encuentra en <1KB la descripción del proyecto + links a docs relevantes

#### Scenario: Cambio futuro
- WHEN se propone cualquier cambio no trivial
- THEN existe un `openspec/changes/<id>/proposal.md` antes de tocar código

## Anti-patterns prohibidos

### Anti-pattern: PowerShell `$pid` (Trampa #1)
El script PowerShell embebido SHALL usar otra variable, nunca `$pid` (reservada).

### Anti-pattern: `proc.kill()` sin `/T` (Trampas #10, #11)
Cleanup de procesos con hijos SHALL usar `taskkill /F /T /PID`, no `proc.kill()`.

### Anti-pattern: `messagebox` en main UI (Trampa #14)
La UI principal SHALL usar `status_label` inline + doble tap, NUNCA `messagebox.askyesno/showinfo/showwarning`.

### Anti-pattern: `__file__` en frozen mode (Trampa #17)
Data files SHALL usar helper `_app_dir()` (que devuelve `sys.executable` dir en frozen mode), NUNCA `os.path.dirname(__file__)`.