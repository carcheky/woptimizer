# Cerrar los falsos positivos de N1 y N7 sobre datos del usuario

- **Change ID:** `2026-09-30-close-user-data-false-positives`
- **Ciclo:** 21, iteración 4
- **Tarea:** TASK-028 (cierre de supervisores y huecos de alcance)
- **Alcance:** `run_tests.py` y documentación. **`src/` NO se toca.**

## 1. Por qué esta iteración y no otra

La iteración 1 cerró 16 supervisores del `mutation-auditor`. La iteración 2 cerró la deuda de
`FIX-012`. La iteración 3 cerró dos huecos de **alcance**: la promesa de la documentación era más
fuerte que lo que la sonda medía. Esta iteración 4 cierra lo **contrario**, y es de otra gravedad:

> **Dos sondas afirmaban sobre ficheros del usuario, y una de ellas le pedía al usuario que borrara
> el suyo.**

Un test que no verifica nada es un test inútil. Un test que **mata de más** es peor: es una guarda
capaz de decirle a alguien que su configuración está rota, cuando la app la abre sin problema. La
regla del repo —*un problema de datos no se documenta y se sigue, se arregla*— aplica aquí sin
matices, y por eso S1 y S2 van primero.

## 2. Los cuatro hallazgos

| # | Severidad | Qué pasaba | Medido por |
|---|---|---|---|
| **S1** | **DATOS** | N1 exigía **JSON válido** en el `PROFILES_FILE` real. Un `profiles.json` corrupto o **vacío (0 B)** —lo que deja un corte de luz o un antivirus que lo trunca— tumbaba la suite, y el mensaje terminaba con *"se borra y la app lo regenera"*: le decía al usuario que borrara sus packs. | `run_tests.py:5993-6000` |
| **S2** | **DATOS** | N1 declaraba "v2 retirado" ante un `profiles.json` **legítimo** con un campo de usuario llamado `factory` o `kill_low_chat`. `Pack` es `extra="allow"`: es un documento válido. La condición `{"factory","kill_low_chat"} & set(registro)` aplicada a cualquier registro bastaba. | `run_tests.py:6008` |
| **S3** | MEDIA | N7 solo recogía los `Assign`/`AnnAssign` **directos** de `arbol.body`. Un logger nombrado dentro de un `if`/`try` no se reconocía, así que un `.addHandler()` de nivel de módulo **pasaba**: FIX-010 colándose por una indirección. | `run_tests.py:6330-6339` |
| **S4** | MEDIA | N7 contaba el **cuerpo de una clase** como permitido (`ClassDef` iba entero a `dentro`). El cuerpo de una clase **se ejecuta al importar**. Y el docstring **y** `architecture.md` §15 decían "dentro de una función **o una clase** (lo permitido)": la documentación afirmaba un criterio **falso**. | `run_tests.py:6376` |

## 3. Los arreglos

### 3.1 S1 — la sonda deja de exigir JSON válido, y deja de mandar

- Si el documento **no se puede leer** (inválido, vacío, ilegible, que no es un mapa), **no se
  afirma nada** y se avisa por `print()` con la ruta y el motivo. Un fichero corrupto o truncado no
  es evidencia de que el v2 haya vuelto: es estado local, gitignored, que la app ya tolera.
- **Ningún mensaje de una sonda termina en una instrucción de borrar el fichero del usuario.** El
  texto del caso v2 se reescribe como observación ("esta sonda no lo borra, no lo renombra y no
  recomienda borrarlo; lo que dice es que su contenido coincide con el esquema retirado, y la
  decisión es del usuario").

### 3.2 S2 — la firma es la combinación, no un campo suelto

Criterio, medido contra el `docs/archive/legacy-root-data/profiles.json` real (420 B): los rasgos se
cuentan **dentro del mismo registro** y hacen falta **dos o más**.

| Rasgo | En el archivado |
|---|---|
| la clave del registro se llama `__system_gaming__` | sí |
| el campo `factory` (el v2 se anidaba a sí mismo) | sí |
| el campo `kill_low_chat` | sí |
| `kind: "system"` | sí |

El archivado acumula los cuatro. Un discriminante único es frágil por definición, porque es
exactamente el nombre que un usuario puede elegir.

**Salidas(argv) que NO disparan la guarda** (medidas, las siete): un campo `factory` suelto, un
`kill_low_chat` suelto, un pack llamado `__system_gaming__` sin campos del v2, el esquema vivo
(raíz `packs`), un campo de usuario en cada uno de dos packs distintos, y un JSON corrupto o vacío.

**Riesgo residual, dicho en voz alta:** un pack de usuario que declarase `factory` **y**
`kill_low_chat` a la vez en el mismo registro seguiría activando la guarda. Es el precio
conscientemente aceptado de exigir combinación, y está escrito en `testing-guide.md` para que nadie
lo lea como un olvido.

### 3.3 S3 — el logger nombrado dentro de un bloque también cuenta

`_plano_de_ejecucion()` aplana el bloque de módulo entrando en `if`/`try`/`for`/`while`/`with`/
`match` a cualquier nivel, **sin cruzar frontera de función, de clase ni de lambda**. Los dos sitios
que dependían de la versión anterior: la recolección de loggers nombrados y el reparto `fuera`/
`dentro`.

**Consecuencia colateral medida durante la propia iteración:** con un `ast.walk` a pelo, una función
anidada en un `if` de módulo (`if True: def main(): logging.basicConfig(...)`) hacía que su cuerpo se
marcara como configurado al importar. Se sustituyó por `_NodosEjecutados`, un `NodeVisitor` que no
entra en el cuerpo de una función ni de una lambda y **sí** en el de una clase. Una comprehension sí
se recorre, porque su elemento se ejecuta de verdad al importar.

### 3.4 S4 — el cuerpo de una clase cuenta como `fuera`

Criterico escrito en los dos sitios (docstring de `_configuraciones_de_logging` y `architecture.md`
§15): lo único permitido es **dentro de una función**. Las tablas `ILEGALES`/`LEGALES` pasan de
8/6 a **14/10** y fijan las dos direcciones, incluidas las que dicen lo contrario: método de clase
= legal, función anidada en un `if` de módulo = legal, `lambda` = legal, comprehension = ilegal.

## 4. La medición, y por qué tiene controles positivos

Medido con `_mutmatrix_t028_iter4.py` en una copia en `%TEMP%` (excluyendo el fichero `.git`,
`git rev-parse --absolute-git-dir` verificado antes de escribir y después de salir, `__pycache__`
purgado en cada escritura): **21 escenarios, 21 con el veredicto esperado**.

La mitad son **controles positivos**, y esa es la parte que la iteración 3 no tenía: una guarda que
mata de más no es una guarda. Además, los dos detectores se **mutan a sí mismos** para demostrar que
la comprobación discrimina y no es tautológica:

- el detector de v2 vuelto a "un campo basta" + un campo de usuario → **ROJO por el control positivo**;
- el detector de v2 anulado (`return False, []`) → **ROJO por el control negativo** (si no, el
  `assert not ...` de abajo pasaría siempre);
- S3 o S4 revertidos + la tabla `ILEGALES` saltándose esas filas + el mutante correspondiente →
  **ESCAPAN**, lo que prueba que la muerte la aporta el arreglo y no otra cosa;
- S3 o S4 revertidos **con** la tabla intacta → **ROJO por la propia autocomprobación**: el detector
  se delata a sí mismo.

**Trampa encontrada midiendo (no supuesta):** el primer mutante de S3 era
`if __name__ == '__main__': logger_mut = logging.getLogger(...)` + `logger_mut.addHandler(...)`. Al
**importar** `config.py` el `__name__` no es `'__main__'`, la asignación no se ejecuta y el módulo
revienta con `NameError` — la suite muere en 0,2 s y sin ninguna aserción, o sea un **falso positivo
de muerte** indistinguible del bueno. La forma válida es la que asigna siempre al importar
(`try/except` con la misma asignación en las dos ramas).

## 5. Lo que NO se toca (verificado, no supuesto)

- `src/` no cambia en esta iteración. `test_get_gaming_pack` y la tabla de 65 filas de
  `testing-guide.md` son **ciertas**: 65 filas, 65 registros, 0 desajustes (el recuento no cambia
  porque ninguna sonda nueva entra en el `__main__`).
- `test_headless_ui()` instancia `PackService()` sin `data_path` sobre el fichero real. Con SHA-256
  antes/después en los tres escenarios, los bytes son idénticos, no hay `.bak` ni `.tmp`, y las 5
  llamadas a `save()` están en acciones de usuario. Es deuda de **lectura**, no de escritura:
  **documentada en `testing-guide.md`, no arreglada.**

## 6. Fuera de alcance

`M10` (el escáner de versión que no pilla un semver sin token) sigue como **deuda aceptada** por
decisión del `mutation-auditor`: la consecuencia es desincronización de la versión de empaquetado, no
seguridad ni datos, y ya está escrito en `architecture.md` §15.
