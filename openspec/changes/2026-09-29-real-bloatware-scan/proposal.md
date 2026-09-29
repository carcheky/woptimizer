# Propuesta: Bloatware real del sistema (PowerToys, Armoury Crate, audio, language servers) con blindaje anti-brick

- **Change ID**: `2026-09-29-real-bloatware-scan`
- **Ciclo**: #13
- **Área de rotación**: 3 — Base de Datos y Procesos
- **Taskmaster**: `TASK-024`
- **Subagente de ejecución**: `process-db-updater`
- **Estado**: Pendiente de ejecución

## 1. Qué se ha medido

Escaneo real del sistema con `psutil.process_iter`:

| Métrica | Valor |
|---------|-------|
| Entradas en `assets/process_db.json` | 48 |
| Nombres de proceso únicos en el sistema | 131 |
| Procesos no registrados | **122** |

Los 122 no son todos candidatos. La lista se divide en tres familias con consecuencias
**opuestas**, y confundirlas es literalmente el riesgo de vida o muerte de la app.

### Familia A — Sistema operativo: PROHIBIDO registrarlos como cerrables

`csrss`, `lsass`, `winlogon`, `smss`, `services`, `wininit`, `dwm`, `sihost`, `fontdrvhost`,
`ctfmon`, `spoolsv`, `lsaiso`, `ngciso`, `memcompression`, `Registry`, `System`, `System Idle
Process`, `smss`, `wininit`, `conhost`, `openconsole`, `dllhost`, `shellexperiencehost`,
`searchhost`, `searchindexer`, `startmenuexperiencehost`, `RuntimeBroker`, `taskhostw`,
`audiodg`, `wudf*`, `SecurityHealth*`, `TextInputHost`, `SystemSettings`…

Matar cualquiera de estos **deja Windows inservible** (pantalla negra, BSOD, pérdida de sesión).
Que la app de "optimización" ofrezca matarlos es el peor defecto posible en este producto.

**Regla dura: ninguno de estos entra en la base de datos, y un test de regresión lo bloquea.**

### Familia B — Bloatware y telemetría legítimos (el objetivo real del ciclo)

| Grupo | Procesos detectados | Por qué |
|-------|--------------------|---------|
| **PowerToys** (Microsoft) | `powertoys`, `powertoys.mousewithoutborders`, `powertoys.mousewithoutbordershelper`, `herculesdjcontrolmp3` (Audio Switch), `cowork-svc`, `lightingservice`, `dsatray` | Utilidades reconstruidas varias veces al inicio, residuo permanente de RAM |
| **Armoury Crate** (ASUS) | `armourycrate`, `armsvc`, `armouryhtmldebugserver`, `armourysocketserver`, `armouryswagent`, `armourycrate.service`, `armourycrate.usersessionhelper`, `asus_framework`, `asuscertservice`, `aurawallpaperservice` | **El bloatware gaming por excelencia**: ~10 procesos residentess que no hacen falta para jugar |
| **Audio enhance** | `atkexcomsvc` (Realtek ATK), `dtsapo4service` (DTS) | Mejoras de audio que se ejecutan en segundo plano |
| **Dev / editores** | `antigravity`, `antigravity ide`, `language_server`, `language_server_windows_x64` | Los language servers son de los mayores-devoradores de RAM del equipo |
| **Varios** | `keepassxc`, `keepassxc-proxy`, `crashhelper`, `calendarapp.gui.win10`, `unigetui`, `dsaupdateservice`, `crossdeviceresume`, `gigabyteupdateservice`, `rogliveservice`, `mpdefendercoreservice`, `acpowernotification`, `telemetry_agent`, `nodoze-1.1`, `unigetui` | Utilidades de terceros de arranque |

### Familia C — Fuera de alcance

`vmmemwsl`, `wsl`, `wslhost`, `wslservice`, `vmcompute`, `vmwp`, `windowsterminal`, `pwsh`,
`powershell`, `python`, `minimax code`, `sihost` — son **del usuario o del propio entorno de
trabajo**. Registrarlos como cerrables sería molestarle o romperle la sesión. No entran.

## 2. Objetivo

1. Añadir las entradas reales de la **Familia B** con su categoría y semáforo correctos.
2. Blindar el motor contra la **Familia A** de forma permanente y testeada.

## 3. Semáforo (reglas del proyecto)

- 🟢 `high` — bloatware/telemetría seguro de cerrar durante gaming (PowerToys, Armoury Crate,
  language servers, servicios de audio).
- 🟡 `low` — cerrable con cuidado.
- 🔴 `none` — nunca cerrar.

La categoría debe existir **exactamente** en `PROCESS_CATEGORIES` de `config.py`. Ya se corrigió
un bug en el ciclo #9 por emojis desalineados entre ambos ficheros: **no reintroducirlo**.

## 4. Blindaje anti-brick (lo más importante de este ciclo)

Añadir un conjunto de **nombres prohibidos** de nivel sistema, en el servicio, que:

1. Se compruebe **antes** de construir la lista de matables.
2. Devuelva esas entradas con semáforo 🔴 y `priority: none`, aunque se registren por error.
3. Esté cubierto por un **test de regresión** que falle si alguien añade `csrss`, `lsass`,
   `winlogon`, `wininit`, `services`, `smss`, `dwm`, `System` o similar a la base de datos como
   cerrables.

## 5. Fuera de alcance

- **NO** registrar nada de la Familia A ni de la Familia C.
- **NO** tocar la lógica de kill, la UI ni los servicios más allá del blindaje.
- **NO** cambiar categorías ni emojis existentes.
- **NO** añadir dependencias.

## 6. Criterios de aceptación

- [ ] Entre 15 y 25 entradas nuevas de la Familia B, todas con `category`, `priority` y
      `description` en español.
- [ ] Todas las categorías usadas existen **exactamente** en `PROCESS_CATEGORIES` (sin emojis
      desalineados).
- [ ] El blindaje anti-sistema está implementado en el servicio y cubierto por test.
- [ ] Test de regresión: ningún nombre de la Familia A aparece como cerrable.
- [ ] `assets/process_db.json` sigue siendo JSON válido con el esquema `dict[str, dict]`.
- [ ] `python run_tests.py` y `python verify_ui_syntax.py` en verde.
- [ ] `docs/ai/data-models.md` documenta el blindaje.
- [ ] Cierre limpio: 0 cambios pendientes.

## 7. Riesgo

**Alto, y hay que decirlo**: un error de una letra en el nombre de un proceso de la Familia A
—o un emoji de categoría desalineado— puede dejar la app matando procesos del sistema. Por eso
el blindaje y su test son criterios de aceptación, no improvements: son la Mitad del trabajo.
