# Decisión de producto: qué dice la Portada cuando un pack no puede hacer nada

**Ciclo #26 / TASK-035 · decisión de `architect-review` · sin cambios en `src/`**

> ⚠️ **Tabla histórica, medidas ANTES de la decisión.** Los números de línea caducaron
> al ejecutarse (CYCLE-026 cambió el código), y la última fila ya **no es cierta**: la
> duplicación byte a byte del literal la eliminó TASK-036, hoy hay una sola llamada.
> Se conserva como el estado que motivó la decisión. **Ancla por símbolo, no por línea**:
> `DashboardView.execute_pack`, `PackManagerView._aviso_pack_inerte` y
> `PackManagerView.start_pack`.

Medido antes de decidir (no deducido del enunciado):

| puerta | pack no-gaming sin apps | símbolo (anclaje vigente) |
|---|---|---|
| Portada, ambas ramas | `return` mudo, ni aviso ni confirmación | `DashboardView.execute_pack` |
| Gestor, `kill_pack` | avisa en ÁMBAR, dos veces en el mismo método | `PackManagerView._aviso_pack_inerte` |
| Gestor, `start_pack` | avisa en ÁMBAR | `PackManagerView.start_pack` |

Eran **cuatro** comportamientos, no tres: el literal `"⚠️ '{pack.name}' no tiene apps que
apagar."` estaba **duplicado byte a byte dentro del mismo método** (los dos puntos de la
doble guarda de `_aviso_pack_inerte`). Un cuarto texto más en la Portada habrían sido cinco.
**Cerrado:** ambas ramas de la Portada avisan, y la duplicación ya no existe.

---

## 1. VEREDICTO: AVISO, en las DOS ramas, por un formateador compartido

El silencio no es la opción neutra: `dashboard_view.py:296` corta **antes** de
`_require_double_tap` (`:304`), así que con un pack vacío la pulsación no arma ni
descarta nada y no queda rastro de que la app haya recibido el clic. El caso peor que
describe el briefing es real: `default_action="start"` con `apps == []` deja al usuario
creyendo que se abren programas que nunca se abren.

Existe además un precedente normativo en el propio repo: el design system ya llama
"guarda preventiva" a los dos avisos del Gestor (`docs/ai/ui-design-system.md:325`) y
regla dura del §Acciones Destructivas es **"Nada se traga en silencio"**
(`docs/ai/ui-design-system.md:301`). La Portada es hoy la excepción que rompe la regla.

### Texto exacto y color

Una sola frase para los cuatro sitios, con el verbo derivado de `default_action`
dentro del formateador (**nunca un literal en la vista**):

```
⚠️ '{nombre}' no tiene apps que {verbo}. Añádelas desde el Gestor de Procesos.
```

- `verbo`: `default_action == "kill"` → `"apagar"`; `"start"` → `"iniciar"`.
  `Pack.default_action` es `Literal["start", "kill"]` (`src/woptimizer/models.py:54`),
  así que el mapa es total por construcción y no hay tercer verbo posible.
- El destino ("Gestor de Procesos") es el mismo que ya nombra la tarjeta del Gestor
  (`pack_manager_view.py:298`): una sola voz, no dos.
- **Color:** `AMBAR` (`ui.confirmation`) en la familia inline, `theme.WARNING` en la
  familia banner. Es el mismo reparto que ya respetan `mensaje_cierre_pack`
  (feedback.py:96-103) y `mensaje_banner_cierre` (feedback.py:121-130), y coincide con
  el desenlace `NADA` de ambas. Nunca verde (no hubo éxito) ni rojo (no hubo error).

### NO es un quinto desenlace de `clasificar_cierre`

`clasificar_cierre(killed, failed)` clasifica **un resultado real** y su docstring
(feedback.py:66-70) dice que no mira el pack ni la ruta. Un pack vacío no produce
resultado: no se llama a ningún servicio. Meterlo ahí sería mentir sobre el contrato
del clasificador y abriría la puerta a un quinto color que ninguna puerta de cierre
puede alcanzar.

Lo que sí hace falta son **funciones puras nuevas en `ui/feedback.py`** (que es
exactamente el módulo que existe para que no haya un `if` suelto en la vista):

```python
def es_pack_inerte(is_gaming: bool, n_apps: int, n_categorias: int) -> bool
def mensaje_sin_apps(nombre, default_action)        -> (texto, AMBAR)
def mensaje_banner_sin_apps(nombre, default_action)  -> (texto, theme.WARNING)
def mensaje_gaming_inerte(nombre)                   -> (texto, ROJO)
def mensaje_banner_gaming_inerte(nombre)             -> (texto, theme.WARNING)
```

Los pares comparten la frase con un constructor privado, de modo que las dos familias
**no pueden divergir** y hay un test que lo mata (§3).

## 2. QUÉ RAMAS Y EL CASO LÍMITE DEL GAMING

- **Rama `kill` y rama `start`: las dos.** La guarda actual es una sola y va **antes**
  del `if pack.default_action`, así que el aviso sale de un único punto y el verbo lo
  decide `default_action` solo. Un solo call-site en la Portada, no dos.
- **La guarda va antes de `_require_double_tap`**, igual que en `kill_pack`
  (`pack_manager_view.py:462` está antes del `:470`). Prohibido armar la doble
  pulsación sobre un pack que no puede hacer nada: el texto que produciría es
  `"Segunda pulsación para apagar 0 apps de 'X'."`, que es la fealdad que la guarda
  actual ya evita y que nadie debe volver a ver.
- **Sin hilo, sin `after`, sin worker, sin toast.** El aviso se publica de forma
  síncrona: ya estamos en el hilo principal dentro de un callback de Tk.

### El gaming inerte es un caso de diagnóstico, no de ejecución

`es_pack_inerte` marca **solo** `is_gaming and n_apps == 0 and n_categorias == 0`.
Con ambas listas vacías, `execute_gaming_pack` no puede producir un candidato ni
siquiera: `should_kill_for_gaming` (`gaming_service.py:36-39`) cae a `False` para todo
lo que no esté protegido. Es **inerte por construcción**, no "probablemente inerte".

Texto, distinto del anterior porque el diagnóstico no es el mismo hecho:

```
⛔ El Gaming Mode de '{nombre}' no tiene nada que cerrar: 0 apps y 0 categorías configuradas. Revísalo en el Gestor de Packs.
```

- **Color:** `ROJO` en inline / `theme.WARNING` en banner. Es un bloqueo, no un aviso,
  y por eso lleva `⛔` como las cuatro ramas de fallo. En la Portada **no** puede ser
  `ROJO`: `theme.DANGER` sobre `SURFACE_ALT` da 3.07:1 y el design system exige 4.5:1
  (`feedback.py:117-119`, `test_contrast_wcag_aa`).
- **Dónde:** el mismo punto en las dos puertas (`dashboard_view.execute_pack` y
  `pack_manager_view.kill_pack`), también antes de `_require_double_tap`.
- **Por qué no reutiliza el desenlace `NADA`:** hoy un gaming inerte cae en la puerta
  real y produce `"⚠️ Nada que cerrar: 0 ya cerrados o protegidos."` (feedback.py:130),
  donde el `0` es el contador de blindaje, no de apps. El usuario lee "ya estaban
  cerrados" y culpa al sistema operativo. Es una mentira de otra clase: no de
  ejecución, de configuración.
- **Un gaming con apps **o** con categorías NO es inerte** y no debe avisar: cierra de
  verdad por la vía G-2/G-3. Es la mutación que el auditor tiene que probar (§4, M-F).

### La Portada necesita un canal nuevo, no `_inline_status`

`DashboardView._inline_status` (`dashboard_view.py:128-132`) **no** sirve aquí, y por
dos razones medidas:

1. Pinta el fondo con `CANCEL` (`confirmation.py:37`, `#5a4a1e`), que es la familia del
   aviso de "confirmación pendiente" (`PENDIENTE_FG`, `confirmation.py:35`). Un aviso
   permanente con ese fondo se lee como "espera la segunda pulsación".
2. **Nunca se auto-oculta**: llama a `pack()` y no a `_reprogramar_autoocultado()`
   (`dashboard_view.py:159`). Dejaría el aviso pegado, contra la regla de
   `_on_expirado` ("el banner de la portada es de usar y tirar", `dashboard_view.py:136`).

Nuevo `_show_aviso_banner(texto, color)`: `fg_color=theme.SURFACE_ALT` (el de
`_show_banner`/`_show_start_banner`), `pack(...)`, `configure(...)` y
`self._reprogramar_autoocultado()`. Un solo sitio, con el temporizador único ya
garantizado por el ciclo 26 iteración 3.

## 3. EL TEST: sí, código y test en el MISMO commit

El bloque actual (`run_tests.py:8578-8596`) **afirma el silencio**:
`assert dash.status_label.cget("text") == antes_texto` con el mensaje *"se corta en
silencio: ni aviso ni confirmación armada"*. Falso por diseño: una aserción que
prohíbe la verdad nueva se convierte en la especificación de la mentira. Se invierte.

**Lo que se mantiene** (sigue siendo cierto y sigue siendo valioso):
`len(hilos) == antes_hilos` y `len(cola) == antes_cola` — el aviso no lanza worker ni
publica por `after`.

**Lo que se invierte** (esto es lo que discrimina):

```python
assert dash.status_label.cget("text") == (
    "⚠️ 'Vacio' no tiene apps que apagar. "
    "Añádelas desde el Gestor de Procesos."
)
assert dash.status_label.cget("text_color") == theme.WARNING
assert _sin_confirmacion_pendiente(dash), "el aviso no puede ir montado sobre una doble pulsación"
```

Por qué **`cget("text")` con el texto exacto** es la aserción que discrimina y no un
`assert "no tiene apps" in texto`: sin el fix el `status_label` conserva el valor
anterior, así que **cualquier** comparación contra el texto exigido muere. Un `!=` o un
`in` parcial también moriría, pero el texto exacto ata además la frase a la decisión y
detecta la deriva entre las dos familias. La de color muere sola ante un `VERDE`
equivocado. La de confirmación pendiente es la única que muere si alguien mueve la
guarda **después** de `_require_double_tap`; sin ella, M-D sobrevive.

Casos nuevos obligatorios en el mismo test:

| caso | qué mata |
|---|---|
| `default_action="start"` → el texto dice **"iniciar"** | verbo cableado (M-B) |
| gaming con `apps=[]` y `target_categories=["🟡 Media y Streaming"]` → **no** avisa | `or` en vez de `and` (M-F) |
| gaming inerte → texto de diagnóstico y **sin** `_require_double_tap` | ausencia del diagnóstico (M-E) |
| `mensaje_sin_apps(...)[0] == mensaje_banner_sin_apps(...)[0]` (y el par del gaming) | duplicación de la frase en dos sitios |
| `format_kill_result` sigue omitiendo MB con `0.0` (`run_tests.py:303`) | no se toca |

Los literales de categoría del test nuevo: `🟡 Media y Streaming` con `\U0001F7E1` y
espacio normal (U+0020). Nada de `?` ASCII. Ver `docs/known-issues.md`.

**También en el mismo commit:** `docs/ai/ui-design-system.md` (§"Guarda preventiva",
nuevas filas de la tabla de desenlaces y el caso inerte) y el criterio de aceptación de
`proposal.md`. Un commit que cambia el texto y otro que cambian el test dejan el
histórico con un estado en el que la suite afirma algo que el código ya no hace.

## 4. MUTACIONES QUE EL `mutation-auditor` DEBE PASAR (sin esto, el arreglo es código muerto)

| id | mutación | aserción que tiene que morir |
|---|---|---|
| **M-A** | `execute_pack`: sustituir el aviso por el `return` mudo de `:296-297` (el estado actual) | `cget("text") == <texto exacto>` |
| **M-B** | `mensaje_sin_apps(pack.name, "start")` hardcodeado, o el mapa invertido | caso `default_action="start"` esperando **"iniciar"** |
| **M-C** | color `VERDE` o `ROJO` en vez de ÁMBAR | `cget("text_color") == theme.WARNING` |
| **M-D** | mover la guarda **después** de `_require_double_tap` | `_sin_confirmacion_pendiente(dash)` |
| **M-E** | borrar el diagnóstico del gaming inerte (o su `and` → `or`) | caso gaming inerte / caso gaming sano |
| **M-F** | `es_pack_inerte` con `or`: `n_apps == 0 or n_categorias == 0` | gaming con apps pero sin categorías **no** avisa |
| **M-G** | reusar `_inline_status` en la Portada en vez de `_show_aviso_banner` (fondo `CANCEL` + sin auto-ocultado) | aserción de **fondo** `fg_color == theme.SURFACE_ALT` **y** de auto-ocultado a 5500 ms |
| **M-H** | borrar la cláusula `if freed_mb > 0` del helper de MB (§5) | texto con `killed=1, freed_mb=0.0` |

M-G necesita reloj: el bloque ya tiene un reloj falso (t=5500 en
`run_tests.py:8299-8305`), reúsalo en vez de escribir un test nuevo.

## 5. INCIDENCIA #4 — la cláusula `(0.0 MB liberados)`: **OMITIRLA**

**No Approved.** El argumento del dev ("no promete más de lo que pasó") no se sostiene,
porque el repo **ya decidió** esta regla y la aplicó a la otra puerta:

- `format_kill_result` omite la cláusula cuando `freed_mb <= 0`
  (`src/woptimizer/services/notification_service.py:133`), y está **fijada por un test**:
  `run_tests.py:303` — `assert "MB liberados" not in format_kill_result(3, 0, 0.0)`.
- Los dos formateadores de banner/guide **ya no lo hacen** (`feedback.py:96`, `:99`,
  `:124`, `:126`) y `_last_gaming_summary` tampoco (`dashboard_view.py:196`).

Es decir: la misma verdad se dice de dos maneras según por dónde se ejecute, que es la
razón por la que existe `ui/feedback.py`. Y `✅ 2 procesos cerrados (0.0 MB liberados)`
no es una promesa imposible: es un número que el usuario no puede cuadrar con lo que ve
en el Administrador de tareas y que le hace sospechar de la telemetría entera.

**Helper único en `feedback.py`:**

```python
def clausula_mb(freed_mb: float) -> str:   # "" si freed_mb <= 0
```

**Textos resultantes con `freed_mb <= 0` (especificación exacta):**

| desenlace | inline | banner |
|---|---|---|
| éxito | `✅ {N} {sus} cerrados · '{nombre}'.` | `⚡ {N} procesos cerrados` |
| parcial | `⚠️ '{nombre}': {N} cerrados, {M} con error.` | `⚠️ {N} procesos cerrados · {M} con error.` |

`nada` y `fallo` no cambian: nunca llevaban MB. En `dashboard_view._show_banner`,
`self._last_gaming_summary` pasa a `f"{killed} cerrados"` + la cláusula si la hay.

Ningún test actual fija por texto exacto un caso `killed > 0, freed_mb == 0`
(las 10 aserciones exactas de `MB liberados` usan 2.5, 8.0, 12.0, 40.0, 64.0, 128.5,
256.0), así que el cambio no rompe verde: **añade** el caso
`killed=1, freed_mb=0.0 → "✅ 1 procesos cerrados · 'Trabajo'."`.

**Es independiente de §1 y §2:** si el padre tiene que cerrar el ciclo, el mínimo
bloqueante es §1 + §2 y la cláusula MB se puede separar a otro commit. Lo que **no** es
aceptable es aprobarla como deuda sin escribirla en un fichero (ver §6).

## 6. LAS 5 INCIDENCIAS QUE SOLO VIVEN EN UN MENSAJE: **persistir con severidad**

**No son basura y no puedo descartarlas** porque no están en ningún fichero: eso es
justo el motivo por el que hay que escribirlas. Una incidencia que solo existe en un
mensaje de agente se pierde en cuanto el mensaje se pierde, y este repo ya pagó ese
coste (ciclo 12, un patrón de seguridad entero; y el validador que deriva los ciclos
obligatorios de `rd_journal.json`, STATUS.md:78).

Procedimiento obligatorio, en este orden:

1. **`openspec/changes/2026-09-30-pack-telemetry-feedback/deuda-ciclo-26.md`** (ya creado,
   con la tabla y las 2 incidencias que sí constaban en un fichero de repo): el dev
   transcribe ahí las 5 restantes **con su redacción literal**, sin resumir.
2. **`STATUS.md`, sección `## ⚠️ Deuda Técnica Conocida`** (línea 70), una línea por
   incidencia con la severidad de esta escala:
   - 🔴 **miente al usuario o pierde datos** (rompe un invariante de `AGENTS.md`),
   - 🟡 **inconsistencia o UX** sin pérdida,
   - ⚪ **limpieza**.
3. Las 2 que ya estaban escritas se numeran con la misma escala. **No se cambia su
   redacción**, solo se les añade la severidad.
4. **Regla de cierre:** una línea de deuda solo desaparece cuando la línea dice qué
   ciclo la cerró y con qué test. Si al verificarla el dev descubre que ya estaba
   arreglada, se marca `✅ cerrado en CYCLE-0xx` con el nombre del test que lo
   demuestra; **no se borra en silencio**, porque borrar sin evidencia es el mismo
   fallo que no escribirla.

`validate_docs.py` no vigila esto hoy, así que la disciplina es del orquestador, no del
validador: leer un `0 FAIL` no prueba que la trazabilidad esté al día (STATUS.md:78).
