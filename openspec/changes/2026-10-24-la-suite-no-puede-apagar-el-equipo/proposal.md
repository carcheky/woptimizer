# La suite no puede apagar el equipo del dueño (TASK-093)

## Qué pasó

El 2026-10-24 el dueñoAvisó de que el equipo **se le había apagado más de una vez**
mientras el motor de I+D corría. No era una impresión: el **registro de eventos de
Windows** del host lo dice, evento a evento.

| momento | evento | lo que dice |
|---|---|---|
| 23/10 07:32:08 | `1074` (User32) | "El proceso `MoUsoCoreWorker.exe` (PCCK) inició el **Reinicio** del equipo ... motivo: *Sistema operativo: service pack (planeado)*" |
| 23/10 07:33:36 | `1074` (User32) | "El proceso `winlogon.exe` (PCCK) inició el **Apagar** del equipo" |
| 24/10 02:52:52 | `1074` (User32) | "El proceso `StartMenuExperienceHost.exe` (PCCK) inició el **Apagar** del equipo" |
| las 4 noches anteriores | `42` (Kernel-Power) | "El sistema está entrando en suspensión. Motivo de la suspensión: **System Idle**" |

Y el dato que cierra la cadena:

```
powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE
  -> índice de configuración de corriente alterna actual: 0x00000384   (900 s)
```

## La causa raíz (y lo que NO la causó)

El equipo **se dormía por inactividad** y **Windows Update reiniciaba lo que dormía**:

- El temporizador de suspensión estaba en **900 s con el equipo enchufado**.
- Ese temporizador **no lo reinicia la carga de CPU**: cuenta inactividad **de
  usuario**, no trabajo del proceso. Por mucha CPU que queme el motor de I+D de
  noche, el temporizador sigue corriendo.
- `MoUsoCoreWorker.exe` es el orquestador de **Windows Update**, y su motivo
  declarado fue *"Sistema operativo: service pack (planeado)"*.

**Ninguna prueba apagó el equipo.** Eso se comprobó, no se supuso:

- `grep` sobre los 55 `.py` del repo: **cero** coincidencias de las 17 palabras
  de la API de energía de Windows y de la simulación de entrada.
- `grep` sobre el repo: **cero** llamadas a `shutdown`, `powercfg`,
  `SetSuspendState`, `pyautogui`, `SendInput`, `mouse_event`, `SetCursorPos`…

Lo que sí era nuestro, y lo que queda cerrado aquí, es otra cosa: **que nada en el
repo pueda abrir esa vía el día de mañana**. Un comando de apagado "para cuando
termine la descarga" o un ratón sintético que caiga en "Apagar" del menú Inicio
(que es literalmente el proceso que registró el apagón del 24/10) serían la misma
pérdida de tiempo.

## Lo que se hizo

### 1. La mitigación del host (fuera del repo, reversible)

```powershell
powercfg /change standby-timeout-ac 0
```

- **Valor original**: `0x384` = 900 s (AC). **Batería**: `0x258` = 600 s (DC),
  **sin tocar** (en batería el equipo sí puede dormirse).
- **Cómo revertirlo**: `powercfg /change standby-timeout-ac 900`.

El reinicio de Windows Update solo ocurre contra una máquina dormida; con el
equipo despierto, la política por defecto de WU no reinicia con un usuario con
sesión iniciada. Por eso no se toca la política de WU ni el resto del plan de
energía: **la mitigación mínima es la que corta la cadena**.

### 2. El blindaje en el repo (`run_tests.py`)

`_la_suite_no_puede_apagar_el_equipo()` vigila los **`.py` del repo DERIVADOS del
disco** (`os.walk`, no una lista escrita a mano: una lista es *vaciable*) con un
vocabulario **cerrado**:

| regla | qué caza |
|---|---|
| (a) lanzador con argumento prohibido | `subprocess.run`/`Popen`/`call`/`check_call`/`check_output`, `os.system`/`os.popen` cuyo **argumento** nombra el apagado o la suspensión |
| (b) llamada directa a la API | `SetSuspendState`, `ExitWindowsEx`, `InitiateSystemShutdown`, `NtShutdownSystem`… (vía `ctypes.windll.user32`) |
| (c) importación de simulación de entrada | `pyautogui`, `pynput` |
| (d) `taskkill` por NOMBRE (`/IM`) | matar al `lsass.exe` o al `winlogon.exe` **apaga el Windows** |

**Por qué (a) mira el argumento y no la palabra suelta:** porque así el guard
puede vigilarse a sí mismo (su propio vocabulario vive en una tupla, no en el
argumento de un lanzador) y no necesita una lista de exentos. El guard se excluye
a sí mismo **solo** de su propio bloque, delimitado por dos centinelas, y ese
bloque se delimita con `rfind` (la primera aparición del centinela de fin está
en la constante que lo define: con `find` el rango se quedaba corto y el guard
se acusaba a sí mismo con su propia contraprueba — así se encontró).

**Por qué no es un `test_*`:** el recuento de tests es un contrato escrito a mano
en cinco sitios (`235 = 159 + 76`) y `validate_docs.py:2967` lo dice
explícitamente. El guard se invoca desde `__main__` como comprobación
transversal. **El recuento no se mueve.**

## Criterios de aceptación (MEDIDOS)

1. `powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE` → el índice AC es
   `0x00000000` y el DC sigue en `0x258`. ✅
2. El guard pasa sobre el repo real: **55 ficheros `.py` vigilados, 0 vías**. ✅
3. **Contrapruebas en cámara desechable** (repo copiado a `%TEMP%`, sin `.git`):
   - se inyecta `subprocess.run(['shutdown', '/s', '/t', '0'])` → **ROJO** ✅
   - se inyecta `import pyautogui` → **ROJO** ✅
   - se inyecta `ctypes.windll.user32.SetSuspendState(0)` → **ROJO** ✅
   - se inyecta `subprocess.run(['taskkill', '/F', '/IM', 'lsass.exe'])` → **ROJO** ✅
   - **control positivo**: `subprocess.run(['taskkill', '/F', '/T', '/PID', pid])`
     → **VERDE** (es legítimo: las utilidades matan su propio hijo) ✅
4. Las **tres citas por número de línea** que apuntan a `run_tests.py` (`1600`,
   `24785`, `30731`) siguen **intactas**: el guard se insertó **por debajo de
   las tres**, con desplazamiento **cero**. ✅

## Lo que este cambio NO cierra

- **No arregla un apagón del sistema por otra causa** (sobrecalentamiento, corte
  de corriente, un corte de luz). Solo corta la cadena medida: *inactividad →
  suspensión → Windows Update reinicia*.
- **No vigila el código que no está en el repo**: un script suelto en `%TEMP%`
  que llame a `shutdown` no lo ve nadie. El guard vigila el repo.
- **El guard es de FORMA sobre un vocabulario cerrado**: es perfectible en la
  práctica (la API de energía de Windows tiene un número finito de nombres),
  pero una llamada hecha con `ctypes` construida a mano y sin ninguna de esas
  palabras **no la ve**. Es un límite consciente, no un descuido.
- **La mitigación del host no está en el repo**: si otro host usa este motor,
  hay que aplicarla allí. Está escrita en `docs/ai/sandbox-rules.md`.
