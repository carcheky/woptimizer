# Cerrar F1: hacer alcanzable la rama de la ruta viva ilegible

- **Change ID:** `2026-09-30-close-f1-unreadable-profile`
- **Ciclo:** 21, iteración 5 (final)
- **Tarea:** TASK-028
- **Alcance:** `run_tests.py` y documentación. **`src/` NO se toca** (verificado: intacto desde `3cc33dc`).

## 1. El hallazgo

La iteración 4 dejó la sonda N1（「el v2 retirado no vuelve a la ruta que la app lee」）prometiendo
que un `profiles.json` **ilegible da aviso y no tumba la suite**. La promesa era literal en el
`proposal.md` §3.1 —*«si el documento no se puede leer (inválido, vacío, **ilegible**, que no es un
mapa), no se afirma nada»*— y **era falsa**:

```python
if os.path.exists(viva):
    with open(viva, encoding="utf-8") as fh:   # FUERA del try
        crudo_vivo = fh.read()                  # FUERA del try
    doc_vivo = None
    motivo = ""
    try:
        doc_vivo = json.loads(crudo_vivo)
    except ValueError as e: ...
    except (OSError, UnicodeDecodeError) as e:   # CÓDIGO MUERTO: inalcanzable
```

El `open()` y el `read()` estaban **fuera** del `try`, así que el `except (OSError, UnicodeDecodeError)`
**no podía ejecutarse nunca**. No era un mensaje feo: era una guarda que no guardaba.

## 2. Medición del estado de partida (3 de 3 muertes, sin aserción)

Las tres se midieron contra el bloque **sin tocar** de `HEAD`, con la ruta viva sembrada:

| Estado sembrado | Antes | Síntoma |
|---|---|---|
| bytes que no son UTF-8 | **ROJO** | `UnicodeDecodeError` en `run_tests.py:6079` (`fh.read()`) |
| truncado a mitad de un emoji | **ROJO** | `UnicodeDecodeError` en `:6079` («bytes in position 34-35») |
| sin permiso de lectura | **ROJO** | `PermissionError` en `:6078` (`open`) |
| `null` (el literal JSON) | VERDE | …pero con el motivo **vacío** (D1) |

Las muertes eran **tracebacks**, no aserciones: probaban que el código se rompía, no que afirmara
lo correcto. Es la diferencia entre una guarda rota y una guarda que se prueba.

**El escenario no es hipotético.** El `profiles.json` vivo del usuario tiene un `U+1F680` (cuatro
bytes UTF-8: `F0 9F 9A 80`). Un corte de luz o un antivirus que trunca ahí produce exactamente ese
fichero, y el propio docstring de S1 nombra ese escenario.

### 2.1 La asimetría con la app, medida con el mismo fichero

`pack_service.py:40-41` — `CORRUPTION_ERRORS = (json.JSONDecodeError, ValidationError, TypeError,
UnicodeDecodeError, PerfilCorruptoError)`. La app **detecta, avisa y recupera los packs del `.bak`**:

```
LA APP, con un .bak valido:
  basura no-UTF8  -> ARRANCA, packs: ['gaming']
  truncado a mitad-> ARRANCA, packs: ['gaming']
  literal null    -> ARRANCA, packs: ['gaming']
```

La app sobrevive a los tres; la sonda moría a los dos primeros. Un estado soportado no puede ser un
fallo de test.

## 3. El arreglo

Tres cosas, y **las tres hacen falta** (medido: con dos de ellas el mutante escapa):

1. **`open()`/`read()` dentro del `try`.** Sin esto, la excepción se propaga y la sonda muere.
2. **El ORDEN de las ramas invertido.** `UnicodeDecodeError` es **subclase de `ValueError`**
   (`issubclass(UnicodeDecodeError, ValueError) is True`, medido), así que con `except ValueError`
   primero la rama de lectura **vuelve a ser inalcanzable para la decodificación**: el `read()` ya no
   revienta, pero el aviso culparía al JSON de un fallo de bytes. El arreglo «de movidas» que
   proponía la auditoría (mover el `open()` y nada más) **no basta**; está medido como mutante
   `M-F1c`.
3. **Rama explícita para el literal `null` (D1).** `json.loads("null")` devuelve `None` **sin
   lanzar**, así que el `motivo` se quedaba vacío y el aviso se leía: *«Hay un profiles.json local
   en X **y .** La app lo tolera»*. No es una aserción, pero es un texto que se lee, y un hueco así
   es el mismo patrón que hizo que la doc afirmara cosas que el código no hacía.

## 4. El control: la rama ahora se **afirma**, no solo se sobrevive

El arreglo por sí solo es insuficiente: alguien puede volver a mover el `open()` fuera y la suite
seguiría en verde, porque «no reventar» y «afirmar lo correcto» no son lo mismo. Por eso la lectura
se movió a `_leer_documento_de_packs()` y se añadió un control que **escribe de verdad** los tres
ficheros ilegibles y exige que el helper responda con un motivo, distinguiéndolos por su **texto**:

| Caso | Motivo exigido | Por qué ese texto discrimina |
|---|---|---|
| no-UTF8 | empieza por `no se puede leer (` | Con `except ValueError` primero el motivo sería `…como JSON (…)`, que culpa al JSON de un fallo de bytes. |
| truncado a mitad de emoji | empieza por `no se puede leer (` | Ídem, y además prueba que el `read()` (no el `json`) es el que falla. |
| `PermissionError` real | empieza por `no se puede leer (` | Se usa un **directorio** con el nombre del fichero, no `os.chmod`: en Windows `chmod` no impide la lectura y el control no controlaría nada. |
| literal `null` | contiene `` `null` `` | Es el caso que no lanza: sin la rama, el motivo queda vacío. |
| **documento válido** (control positivo) | documento `dict`, motivo `""` | Sin él, un helper que dijera «todo está roto» pasaría los tres controles anteriores. |

El `PermissionError` se captura y se convierte en `AssertionError` a propósito: si el mutante
propaga, la muerte **dice qué pasó y por qué importa**, en vez de dejar un traceback anónimo.

## 5. Deudas menores, en la misma pasada

### D3 — el `def` se saltaba su propia firma

`visit_FunctionDef = pass` se saltaba los **argumentos por defecto** y los **decoradores**, que
**sí se evalúan al definir la función**. Medido en este intérprete (`root.handlers` tras importar,
sin ningún `setup_logging`):

| Forma | ¿configura al importar? |
|---|---|
| `def f(h=logging.basicConfig(force=True)): ...` | **sí** (`handlers == 1`) |
| `class C: def m(self, h=logging.basicConfig(...)): ...` | **sí** |
| `f = lambda h=logging.basicConfig(force=True): h` | **sí** |
| `def f(*, h=logging.basicConfig(force=True)): ...` | **sí** |
| `def f(): logging.basicConfig(force=True)` | no (`handlers == 0`) |
| `def f(h: logging.basicConfig(force=True))` (anotación) | **sí** |
| lo mismo **con** `from __future__ import annotations` | **no** (`handlers == 0`) |

O sea que M16 hacía sitio en un `def` con `basicConfig` en el defecto, y el auditor se equivocó al
estimar el disparo en ≈0: es bajo, pero es **real y medido**.

El arreglo recoge la **firma** (decoradores, `defaults`, `kw_defaults`, anotaciones) y deja el
**cuerpo** intacto, que es la frontera que S4 y la iteración 3 ya tenían medida. Las anotaciones se
saltan cuando el módulo trae `from __future__ import annotations`, porque entonces se guardan como
texto: marcarlas sería un falso positivo sobre documentos legítimos (`NamedTuple`, `TypedDict`).

### D4 — un generador perezoso no es una comprehension

`visit_GeneratorExp` no existía, así que el generador se recorría como cualquier otra cosa y su
**elemento** se marcaba como ilegal. Falso positivo medido: el elemento de un generador **no** se
ejecuta al importar.

| Forma | `root.handlers` |
|---|---|
| `g = (logging.basicConfig(force=True) for _ in (1,))` | **0** (perezoso) |
| `[logging.basicConfig(force=True) for _ in (1,)]` | 1 (sí se ejecuta) |
| `g = (x for x in [logging.basicConfig(force=True)])` | **1** (la lista se construye entera) |
| `class C: g = (logging.basicConfig(force=True) for _ in (1,))` | 0 |

El arreglo recorre **solo el iterable de entrada** del generador, que es lo único que se evalúa al
crearlo. La fila de la comprehension se queda en `ILEGALES`: la distinción es real, no de estilo.

### D2 — la doc dice una cosa y el detector hace otra

`testing-guide.md` no decía que el detector **solo** mira la raíz `profiles`. Se añadió la línea, con
el porqué: la rama legacy de `pack_service.py:403/420` **solo** se engancha ahí
(`raw_data['profiles']`), así que un `profiles` con `factory` y `kill_low_chat` en la raíz **viva** no
lo resucita. El riesgo residual existe pero es más estrecho de lo que parecía, y el auditor lo
validó contra la rama legacy real. **No se cambia el detector.**

## 6. Lo que NO se toca

Las cuatro correcciones centrales de la iteración 4 siguen **cerradas por medición** (S1 mata 7/7
estados ilegibles, el mensaje no ordena borrar nada, S2 mata 5/5, S3 y S4 matan con mutantes reales
en `config.py`, y el detector no es demasiado amplio: los 6 legales siguen limpios). El riesgo
residual de `factory` + `kill_low_chat` en la raíz `profiles` está **confirmado pero no dispara** con
la raíz viva `packs`, porque el detector solo inspecciona `doc["profiles"]`.

## 7. Fuera de alcance (medido, reportado, NO arreglado)

Un **directorio** en la ruta viva `profiles.json` (el `PermissionError` del §4) **también tumba
`test_headless_ui`**, y no por la sonda: por `PackService.__init__` → `load()` → `_read_json()`, que
abre el fichero en `pack_service.py:379` **sin ninguna protección** frente a `OSError`
(`PermissionError` no está en `CORRUPTION_ERRORS`, que solo cubre `UnicodeDecodeError` y los de
JSON). Es decir: **la app no tolera un `PermissionError`**, a diferencia de la corrupción de bytes.

Eso **no** lo arregla esta iteración porque está en `src/` y el encargo prohíbe tocarlo. Queda
declarado en `docs/ai/testing-guide.md` como hallazgo abierto, con la medición. La sonda sí queda
correcta: avisa y no muere, que es lo que era su trabajo.
