# Propuesta: cerrar los 3 supervivientes de mutación del ciclo #17 (TASK-030)

- **Change ID**: `2026-09-30-close-mutation-survivors`
- **Ciclo**: #18
- **Área de rotación**: 1 — Resiliencia & Robusteza (integridad de datos)
- **Taskmaster**: `TASK-030`
- **Subagente de ejecución**: `openspec-dev`
- **Estado**: AUDITADA por architect-review — **aprobada con correcciones obligatorias** (§6)
- **Alcance**: `src/woptimizer/services/pack_service.py`, `run_tests.py`,
  `docs/ai/data-models.md`, `docs/ai/testing-guide.md`
- **Prohibido**: tocar `SYSTEM_PROTECTED_PROCESSES`, keepers, barrera roja G-2, la doble pulsación,
  `run.py`, y **cualquier otro `except` de `pack_service.py`** fuera de lo descrito aquí.

## 0. Qué es realmente este trabajo

El Paso 4 del bucle rompió el código a propósito y encontró **3 tests que pasan con el bug puesto**
(`CHANGELOG.md:57-67`, sección CYCLE-017). Cerrarlos **no** significa "añadir más asserts": significa
que cada criterio de aceptación tiene que **nombrar la mutación exacta que lo mata**. Un criterio sin
mutación asociada es una opinión, y un test sin mutación asociada es el problema que estamos
resolviendo.

**Método de verificación de esta propuesta (no es una promesa, es una medición).** Se construyó una
matriz de mutación real: se carga una **copia del texto** de `pack_service.py` con `importlib`
(`spec_from_file_location`, nunca se toca `src/`), se le aplica cada mutación y se ejecutan las cinco
sondas de prueba contra el código mutado. Resultado bruto:

| Escenario | Sondas que lo matan |
|---|---|
| **BASE (código actual)** | solo **P4** → el bug `AttributeError` es REAL, no una premisa |
| M1 `os.replace`+temporal → `open(w)` directo | **P1** (×4) + **P3** |
| M2 `os.replace` → `shutil.copyfile` | **P1b** |
| M3 no borra el `.tmp` al fallar | **P1** |
| M4 `except Exception: pass` (traga el error) | **P1** |
| M5 `CORRUPTION_ERRORS` → solo `JSONDecodeError` | **P5** |
| M6 reintroduce `OSError` en `CORRUPTION_ERRORS` | **P2** + **P6** |
| M7 `load()` → `except Exception` (el bug del ciclo 15) | **P7** |
| M9 `AttributeError` en `CORRUPTION_ERRORS` (arreglo ingenuo) | **P7** |
| M10 el `.tmp` en otro directorio/volumen | **P1** |
| **ARREGLO PROPUESTO** (§4.3) | **TODO VERDE** |
| ARREGLO + reintroducir `OSError` | **P2** + **P6** (el arreglo no tapa la regresión) |

Las sondas no son nuevos ficheros de producción: son el contenido de los tests nuevos de `run_tests.py`.
El script de la matriz lived en `%TEMP%\wopt_probe.py` (y el de FIX-007 en `%TEMP%\wopt_probe_fix007.py`).
**No forman parte del entregable**, pero son reejecutables tal cual: reconstruyen la matriz desde el
texto de `src/` y no escriben nunca dentro del repo. El mutation-auditor debe reejecutarlos con los
tests finales (§8).

## 1. Punto 1 — Cómo se prueba la atomicidad de verdad

### 1.1 Lo que hay hoy no prueba nada

`run_tests.py:1903` y `:1916` afirman `not os.path.exists(…".tmp")`. Eso no es la atomicidad: es un
**artefacto**. Si `save()` deja de crear el `.tmp` (mutación M1), el assert sigue verde por la razón
equivocada — exactamente lo que reporta el auditor.

### 1.2 Decisión: inyección de fallo **dentro** del `json.dump`, en el mismo hilo

Se sustituye `json.dump` por un doble que, **antes de escribir nada**:

1. anota `fp.name` (la ruta que el servicio le ha dado), si es el principal, si está en el mismo
   directorio, si el `.tmp` existe **en ese instante**, y si el principal conserva sus bytes;
2. escribe un prefijo JSON verosímil (`'{\n    "packs": {\n        "trabajo": {\n            "id": "tra'`)
   a través del **handle real**, `flush()`, y
3. lanza `OSError("apagón simulado")`.

El `handle real` es la clave: si el servicio escribió sobre el principal, el prefijo truncado queda
**de verdad** en el archivo del usuario. Después: `save()` debe haber lanzado, los bytes del principal
deben ser **idénticos** a los previos, y no debe quedar `.tmp`.

**Orden obligatorio de captura (un error que costó una iteración de la matriz):** el instante de
referencia `antes = read_bytes(principal)` se toma **después** de construir el `PackService`, porque
`__init__` → `load()` → `_ensure_gaming_pack()` → `save()` **ya reescribe el archivo una vez**. Si se
captura antes, el test falla también con el código correcto (falso positivo).

### 1.3 Alternativas rechazadas

| Alternativa | Por qué se rechaza |
|---|---|
| Leer el fichero desde otro hilo mientras se escribe | Depende de `sleep` o de una carrera de timing. El proyecto tiene Trampa #8 (threading en Tk) y la Trampa #12 (no molestar al usuario con tests), y una carrera de timing es un generador de flakes: verde hoy, rojo el 5 % de las ejecuciones. **Rechazada.** |
| Afirmar solo "existe un `.tmp`" | Es el test actual. Verde por la razón equivocada. **Rechazada.** |
| Afirmar solo "el principal no quedó truncado" | Correcto pero ciego a M2: con `shutil.copyfile` el volcado **sí** va al temporal, así que la aserción pasa (medido: M2 no dispara P1). Hace falta además P1b. |
| **`shutil.copyfile` hostil que trunca el destino y revienta** | **ELEGIDA** como sonda P1b. Emula fielmente "la publicación no es atómica y se apagó a mitad": `copyfile` real abre el destino en `wb` y **trunca** antes de copiar. Con el código correcto `shutil.copyfile` no se llama nunca; con M2 se llama y el principal queda inservible. Determinista, sin hilos. |
| Guard `ast` sobre `os.replace` | Necessary pero insuficiente: la auditoría de FIX-007 ya demostró que un guard estático puede ser lo **único** que detecte la mutación, y entonces el test runtime es decorativo. Se usa **además**, nunca en lugar de. |

### 1.4 La sonda P1b y su honestidad

La atomicidad de la publicación **no es observable desde un solo hilo**: entre el `truncate` y el
último byte de una copia hay una ventana que ningún test de un solo hilo puede ver. Eso no es una
carencia del test, es una propiedad de la materia. La respuesta correcta es **inyección de fallo**
(una copia interrumpida sí es observable) más un guard estático como red de seguridad declarada
como tal, no como prueba.

## 2. Punto 2 — Cómo se distingue "no intentó guardar" de "intentó y falló"

### 2.1 La premisa de `TASK-030` es FALSA en su forma literal

La descripción de la tarea dice: *"Falta un espía que afirme que `save()` NO se llamó"*. Medido:

```
BASE, camino D2 (principal corrupto + solo lectura, sin .bak):  save()=1  volcados=1
M6 (OSError_readmitido en CORRUPTION_ERRORS):                    save()=1  volcados=1
M7 (load() -> except Exception):                                 save()=1  volcados=1
```

**El código correcto llama a `save()` y el mutante también, y amboscalled `json.dump` una vez, y
ambos terminan lanzando el mismo `PermissionError` desde el mismo sitio.** El caso D2 es
**indiscriminable por construcción**: no existe ninguna aserción sobre el resultado observable que
distinga una ruta de la otra. Un espía sobre `save()` no solo no mata al mutante — **no puede**:
los dos caminos hacen lo mismo.

### 2.2 Decisión: no contar llamadas, observar la **clasificación** y la **escritura**

Dos sondas, y ninguna cuenta llamadas:

- **P3 (espía del volcado, no de `save()`).** Cuenta invocaciones de `json.dump` en el camino D2 y
  exige `>= 1`. Mata M1 y M10 (`volcados=0`: no llegó a volcar nada). No mata M6/M7 — y **no se
  presenta como si lo hiciera**. Complementary, útil, limitado.
- **P2 (la que sí mata a M6).** El invariante que M6 rompe es: *"un error que no es corrupción no
  puede convertirse en 'sigo y sobrescribo'"*. Se arma con un `json.load` que lanza `PermissionError`
  (simula el principal bloqueado por el antivirus) durante `_rotate_backup`, se vacía `svc._data` y
  se llama `save()`. Correcto: `save()` **lanza** y el principal conserva sus bytes. M6/M7: `save()`
  **no lanza y sobrescribe el archivo del usuario con el estado vacío**. Medido: M6 →
  `save() no lanzó` + `SOBRESCRIBIÓ el principal`. Dos fallos, inequívocos.
- **P6 (el mismo invariante por el lado de `load()`).** Principal ilegible + `.bak` sano:
  `PackService()` debe propagar el `PermissionError` y no tocar el `.bak`. M6 → arranca en silencio
  con el contenido viejo del backup.

### 2.3 Por qué el filesystem solo no alcanza (y es una limitación del SO, no del test)

`os.chmod(0o400)` en Windows activa el atributo **solo escritura**; el archivo sigue siendo legible
(medido: `open(w)` → `PermissionError`, `os.access(W_OK)` → `False`, pero lectura permitida). Para
producir un `OSError` **de lectura** sobre un fichero real harían falta ACL (`icacls` = `subprocess`,
prohibido por la Trampa #9) o un handle con `FILE_SHARE_NONE` (no expuesto por la API estándar de
Python). Se probaron tres escenarios solo-filesystem (`data_path` como directorio, `.bak` como
directorio, principal bloqueado) y **ninguno distingue M6**: en todos, la ruta correcta y la mutada
terminan lanzando el mismo `OSError`. **La inyección en la costura de parseo no es un atajo: es la
única forma honesta de probar este invariante en Windows.**

## 3. Punto 3 — `CORRUPTION_ERRORS`: ni ampliarla a ciegas ni abrir el `except`

### 3.1 La premisa es FALSA: las tres clases YA están en la tupla

`pack_service.py:16`:

```python
CORRUPTION_ERRORS = (json.JSONDecodeError, ValidationError, TypeError, UnicodeDecodeError)
```

Verificado en caliente: `CORRUPTION_ERRORS = ['JSONDecodeError', 'ValidationError', 'TypeError',
'UnicodeDecodeError']`. El mutante M5 sobrevivió porque **ningún test mira esas tres clases**, no
porque falten. Esto invierte el encargo: el arreglo del punto 3 es **de test**, no de código.

### 3.2 El agujero real es `AttributeError`, y tumba la app

`_read_json` (`pack_service.py:77-98`) accede a `raw_data['profiles'].items()` y a `v.get(...)` sin
comprobar la forma. Medido con el código actual:

| Contenido | Resultado |
|---|---|
| `{"profiles": "texto"}` | **`AttributeError: 'str' object has no attribute 'items'`** |
| `{"profiles": {"x": 123}}` | **`AttributeError: 'int' object has no attribute 'get'`** |
| `{"profiles": {"x": []}}` | **`AttributeError`** |

`AttributeError` no está en `CORRUPTION_ERRORS` → sale de `PackService.__init__` → **`PackService()`
reventa al arrancar la app**. Esto es peor que el bug que FIX-009 cerró: no pierde packs, mata el
lanzamiento. La premisa del briefing ("no cubre ValidationError, TypeError ni UnicodeDecodeError")
apunta al síntoma equivocado; el agujero que queda abierto es otro.

### 3.3 Las tres salidas posibles, argumentadas

| Salida | A favor | En contra — **motivo del rechazo/elección** |
|---|---|---|
| **(A) Ampliar la tupla con `AttributeError`** | 6 caracteres | **Elegida: RECHAZADA.** `AttributeError` es un **síntoma**, no una clase de fallo. Con M6-style thinking, cualquier `None` mal desreferenciado dentro de `_read_json` (o un `.get` sobre algo que cambió) se convertiría en "el archivo está roto" → recuperación desde el `.bak` → y en el siguiente `save()`, **los packs que el usuario acaba de crear desaparecen**. Ampliar la lista de excepciones para tapar un `AttributeError` de forma no validada convierte un bug de una línea en pérdida de datos. Medido: la sonda P7 (§4.2) mata exactamente a este mutante, o sea que es detectable, y por tanto no es inocuo. |
| **(B) `except Exception` (o `except (ValueError, AttributeError)`) en `load()`** | Robustísimo ante cualquier forma futura | **RECHAZADA.** Es literalmente el bug del ciclo 15: `except (json.JSONDecodeError, Exception)` traga `PermissionError` y entra en la ruta que regenera y sobrescribe los packs del usuario. Medido como M7: `TODO VERDE` salvo P7 — o sea, reintroduce la pérdida de configuración y los tests lo detectan. El riesgo de "listo" que menciona el briefing se cumple literalmente aquí. |
| **(C) Validar la FORMA en la costura y lanzar un error propio** | El `AttributeError` que llegue a `load()` es **deliberado**; el resto sigue propagándose | **ELEGIDA.** Ver §4.3. |

## 4. Los arreglos de código (los mínimos; el resto es test)

### 4.1 `save()` — no cambia

`pack_service.py:143-162` ya es correcto (temporal en el mismo directorio + `os.replace` + limpieza
en `contextlib.suppress` + `raise`). **No tocar.** Lo que le falta es que alguien lo compruebe (§1).

### 4.2 `load()` / `_rotate_backup()` — no cambian

La clasificación por tupla ya es correcta. Lo que falta es el test que la fija (§2.2 y §5).

### 4.3 `_read_json()` — guarda de forma (el ÚNICO cambio de producción de esta tarea)

```python
class PerfilCorruptoError(ValueError):
    """El profiles.json tiene una FORMA que el servicio no sabe leer (p.ej.
    'profiles' no es un mapa). No es un bug del codigo: es dato roto."""
```

Definida **antes** de `CORRUPTION_ERRORS` (si se define después, la tupla la referencia antes de que
exista → `NameError` al importar; comprobado, es el fallo que dio el primer intento del arreglo) y
añadida a la tupla. En la rama legacy: `isinstance(raw_data['profiles'], dict)` y
`isinstance(v, dict)` antes de `.items()` / `.get()`, lanzando `PerfilCorruptoError` con el tipo
real en el mensaje. Medido: con este arreglo **BASE pasa a TODO VERDE** y M11 (arreglo + reintroducir
`OSError`) sigue muriendo en P2/P6 — el arreglo no tapa la regresión.

### 4.4 BUG COLATERAL REAL: `load()` escribe dos veces

`pack_service.py:59-61`:

```python
self._data = AppData()
self._ensure_gaming_pack()   # ya llama a save() en :172-173 si falta 'gaming'
self.save()                  # segundo volcado redundante
```

Medido en M4: `save()=2, volcados=2`. No es un bug de datos (el segundo volcado es idéntico), pero
es la **razón mecánica por la que un espía sobre `save()` no puede funcionar**: la ruta de
regeneración siempre fue doble, así que cualquier umbral de llamadas es arbitrario. **No se arregla
en esta tarea** (toca código que funciona); se documenta en `data-models.md` como deuda menor y se
registra como candidato a tarea. Sí se elimina el `self.save()` **si** el mutation-auditor lo exige
como parte del mismo commit; no es bloqueante.

## 5. Sondas de prueba → mutación que debe morir

Cada criterio de `tasks.md` referencia esta tabla. Todas sin `sleep`, sin hilos para P1–P7, headless.

| Sonda | Invariante | Muerte |
|---|---|---|
| **P1** `test_save_atomic_nunca_toca_el_principal` | el volcado va a otro fichero del mismo directorio; el principal conserva sus bytes cuando el volcado se corta | M1, M3, M4, M10 |
| **P1b** `test_publicar_no_trunca_el_principal` | publicar no usa un primitivo de copia; el principal queda íntegro o completo, nunca a medias | M2 |
| **P2** `test_save_no_escribe_si_la_rotacion_no_puede_leer` | un error que no es corrupción no se convierte en "sigo y sobrescribo" | M6, M7 |
| **P3** `test_corrupcion_sin_backup_intenta_volar` | se distingue "no intentó escribir" de "intentó y falló" (espiando el volcado) | M1, M10 |
| **P4** `test_forma_legacy_no_tumba_la_app` | `profiles` / valores no-mapa no revientan `PackService()` y sí se recuperan del `.bak` | — (**falla hoy: es el bug**) |
| **P5** `test_todas_las_clases_de_corrupcion_se_recuperan` | tabla de 4 clases (`JSONDecodeError`, `TypeError`, `UnicodeDecodeError`, `ValidationError`) | M5 |
| **P6** `test_oserror_de_lectura_no_es_corrupcion` | un `OSError` al leer el principal se propaga y no toca el `.bak` | M6, M7 |
| **P7** `test_attribute_error_ajeno_no_es_corrupcion` | un `AttributeError` que no sea el deliberado **se propaga** | M7, **M9** |
| **P8** `test_do_load_publica_sin_tk` (FIX-007) | el arnés sin ventana detecta la publicación desde el secundario | mutación de FIX-007 |

### 5.1 P8 — el cuelgue de Tcl del test de FIX-007, sin abrir ventana

Diagnóstico: el test actual (`run_tests.py:1576-1868`) **monta un `ctk.CTk()` real, un
`threading.Event` por llamada y un `faulthandler.dump_traceback_later(150, exit=True)`** porque el
bloqueo ocurre *dentro* de Tcl, donde ningún timeout de Python sirve. Consecuencias: 150 s de suite
colgada en cada regresión, un `exit=True` que mata el runner entero (y por tanto **todos** los tests
posteriores), y el guard `ast` de la fase D como única red.

**Decisión: arnés sin Tk.** Se construye la vista con `PMV.__new__(PMV)` sobre una **subclase** que
convierte `processes` y `grouped_processes` en **propiedades** que anotan `threading.get_ident()`, con
un `after` falso que **encola** el callback y un doble de `ProcessService`. El test **hace de bucle de
eventos**: junta el hilo con `join(10)` y ejecuta en el principal lo que el secundario entregó. Sin
`CTk`, sin `root`, sin `mainloop`, sin `sleep`: **no existe ruta por la que Tcl pueda colgarse.**

Verificado con la misma técnica de mutación (§0):

```
BASE (FIX-007 puesto)                        -> ARNÉS VERDE
mutación: el secundario vuelve a publicar   -> ARNES MATORRADO
      'processes' se publico desde el hilo 24336, no desde el principal (17776)
      'grouped_processes' se publico desde el hilo 24336, no desde el principal (17776)
      el estado nunca se publico desde el principal
```

El test **conserva** su valor adicional: las dos cargas solapadas (fase B) y la puerta sin `sleep`
siguen siendo válidas, pero se ejecutan contra el arnés, no contra una ventana. El guard `ast` **se
conserva** (es una comprobación distinta y válida: prohíbe `self.master.after`, tarea TASK-023) y deja
de ser la única red.

## 6. Correcciones obligatorias a la `description` de TASK-030

1. (b) "Falta un espía que afirme que `save()` NO se llamó" → **falso**: el código correcto **sí**
   llama a `save()` en D2 (`save()=1, volcados=1`) y el mutante también. D2 es indiscriminable; el
   arreglo es P2 + P6, no un espía de llamadas.
2. (c) "`CORRUPTION_ERRORS` no cubre `ValidationError`, `TypeError`, `UnicodeDecodeError`" → **falso**:
   ya están en `pack_service.py:16`. El agujero real es `AttributeError` en la rama legacy, que
   **tumba la app** (P4).
3. Añadir el coste no considerado: **Windows no puede negar lectura con `chmod`**, así que toda la
   familia D (permisos) es ciego al mutante M6. La inyección en la costura es obligatoria, no opcional.

## 7. Orden de ejecución

1. **P1 / P1b / P3** (no tocan `src/`) — matan M1, M2, M3, M4, M10. Empiezan por aquí porque no
   dependen del arreglo de código y ya cierran el punto 1 entero.
2. **P5 / P2 / P6 / P7** (no tocan `src/`) — matan M5, M6, M7, M9.
3. **§4.3 guarda de forma** (toca `pack_service.py`) + **P4**.
4. **P8 + arnés sin Tk** — mata la mutación de FIX-007 y elimina el `faulthandler ... exit=True`.
5. Documentación viva: `data-models.md` (§4.4 + contrato de clasificación) y `testing-guide.md`
   (las sondas y **por qué** cada una existe).

## 8. Verificación de cierre

- `python run_tests.py` en verde, con las sondas P1–P8 registradas en el `__main__`.
- `python verify_ui_syntax.py` y `python validate_docs.py` en verde.
- **Reejecutar la matriz de mutación de §0** con los tests finales: las 8 sondas deben matar su
  mutación y el escenario ARREGLO debe salir TODO VERDE. Sin ese reejecutado, el ciclo no se cierra.
- Cero ediciones fuera de: `pack_service.py`, `run_tests.py`, los dos `docs/ai/` y este change.
