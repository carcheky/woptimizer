# Ciclo 27 — Guardas que no guardan: el alcance de un detector se deriva, o no es un detector

**Estado**: planificado por `architect-review` · **cero cambios en `src/`**
**Alcance**: `validate_docs.py`, `run_tests.py`, `STATUS.md`, `docs/ai/testing-guide.md`
**Fuera de `src/woptimizer/**`**: este ciclo no toca el producto. Es el turno de la
Matriz de Rotación que le toca al **tooling que vigila al producto**.

---

## 0. VEREDICTO

**Núcleo: los puntos (1), (2) y (3) del encargo, en UN commit y UNA ronda de auditoría.**
El punto (4) entra como **gratis** porque el test que (1) obliga a escribir ya tiene
el fixture en la mano. Los puntos (5) y (6) **no entran**, y los dos son decisiones,
no trabajos: los detallo con su motivo en §5.

La razón de que (1), (2) y (3) sean un ciclo y no tres está en §2. En una línea: los
tres son **el mismo defecto** — *una promesa de cobertura escrita a mano que nadie
mide* — y arreglarlos por separado produce dos de los tres errores que este repo ya
pagó.

---

## 1. LO QUE ESTÁ MEDIDO (no deducido del encargo)

Todo lo de abajo está comprobado con `ast` y con sondas ejecutadas sobre el árbol
real antes de escribir esta propuesta. Las rutas del encargo que eran hipótesis
resultaron correctas; las que eran oblivious, no.

### 1.1 La rama `if n_tests is None:` es código muerto — CONFIRMADO

`validate_docs.py:331-336`. El productor es `_recuento_de_tests`
(`validate_docs.py:12-45`) y **no tiene ningún `return None` en sus 34 líneas**: o
devuelve la 4-tupla de la línea 44, o propaga. Medido con sonda:

| entrada | comportamiento real |
|---|---|
| `run_tests.py` con error de indentación | lanza `IndentationError` (subclase de `SyntaxError`) |
| `run_tests.py` ausente | lanza `FileNotFoundError` |

O sea: el contrato que la rama declara ("no se puede derivar el número de tests") es
un estado que **el productor no sabe emitir**. La rama es exactamente la clase de
guarda que este repo ya sufrió dos veces: una protección escrita con mucho cuidado
detrás de un producer que nunca la despierta.

**Matiz que el encargo acierta y hay que conservar en el informe**: esto **no produce
falso verde**. `validate_docs.py` termina con `sys.exit(0 if not errors else 1)`
(`validate_docs.py:411`), así que una excepción sin capturar sale con rc=1 y nadie
podría leer un `0 FAIL` donde no lo hay. Es un agujero de **diagnóstico**, no de
**detección**: el orquestador recibe un traceback en vez de un informe que le diga qué
está mal. Por eso la severidad es 🟡 y no 🔴, y por eso el arreglo no se puede vender
como "arregla un fallo de seguridad del validador".

### 1.2 El residuo cosmético del mensaje — CONFIRMADO

`validate_docs.py:340-342`. Cuando `solo_definidos` tiene entradas y `solo_invocados`
está vacío (es el caso *normal* de un test definido y no invocado), el segundo
elemento de la lista se concatena igual y sale `... | invocado y NO definido: .` con
un punto huérfano al final.

### 1.3 La lista de ficheros del guard de `feedback` es fija Y ya está desfasada — CONFIRMADO

`run_tests.py:8124` itera una tupla literal de **dos** ficheros:
`("views/dashboard_view.py", "views/pack_manager_view.py")`.

Medido recorriendo `src/woptimizer/**/*.py` con `ast`: **tres** módulos importan
desde `ui.feedback`:

| módulo | importa |
|---|---|
| `ui/views/dashboard_view.py` | `clausula_mb`, `es_pack_inerte`, `mensaje_banner_cierre`, `mensaje_banner_gaming_inerte`, `mensaje_banner_sin_apps` |
| `ui/views/pack_manager_view.py` | `es_pack_inerte`, `mensaje_cierre_pack`, `mensaje_gaming_inerte`, `mensaje_sin_apps` |
| `ui/views/process_manager_view.py` | `mensaje_cierre_pack` |

El tercero está fuera de la lista. **Hoy no es un bug**: `process_manager_view` solo
importa `mensaje_cierre_pack`, y el guard solo vigila `mensaje_sin_apps` y
`mensaje_banner_sin_apps`. Los tres call-sites reales de los formateadores vigilados
están en los dos ficheros de la lista y los tres son hoy conformes.

**Y por eso el encargo se equivoca en un punto que importa**: el encargo dice que un
tercer módulo "no lo encuentra, y no da AssertionError sino KeyError con traceback".
Medido: no. El `KeyError` con traceback solo saldría si el tercer módulo *llamara* a
un verbo, y hoy no lo hace. **Hoy la lista desfasada no produce ningún síntoma
observable.** Eso es lo que la hace peligrosa: es invisible, y por eso un mutante que
la sustituya por la tupla correcta de tres ficheros **no lo detecta nadie**. Ver §4,
mutante **M5**, que es el que decide si este ciclo está cerrado.

### 1.4 Hallazgo NO listado en el encargo: el guard es ciego a la forma `fb.mensaje_sin_apps(...)`

`run_tests.py:8130` extrae el nombre con `getattr(llamada.func, "id", None)`. Medido:
para una llamada de la forma `feedback.mensaje_sin_apps("N", "apagar")` el nodo es un
`ast.Attribute`, **no tiene atributo `id`**, y el resultado es `None` → la línea 8131
hace `continue` y la llamada **se salta en silencio**.

Hoy no hay ninguna llamada así en `src/` (los tres call-sites son nombres desnudos, con
`from ... import`), así que es un agujero **latente**, no un bug vivo. Pero es el
mismo agujero que el del punto (3) del encargo: el guard afirma cubrir "el contrato de
los llamantes" y hay una forma de escribir una llamada que no cubre. Si alguien
importa el módulo entero en vez de los símbolos —que es la forma idiomática en Python—
el guard se queda mudo. Mutante **M6**.

### 1.5 Estado del validador hoy

`python validate_docs.py` → **`77 OK, 0 FAIL`**, rc=0. El recuento derivado con `ast`
da **78** tests, y los cuatro ficheros que lo declaran (`STATUS.md`, `AGENTS.md`,
`README.md`, tabla de `docs/ai/testing-guide.md`) están de acuerdo. `git_safe_commit
--verify` → `WOPT_REPO_OK`, rc=0.

**Consecuencia operativa que este ciclo dispara solo**: añadir tests cambia el
recuento, y el check 7 exige que los cuatro ficheros lo declaren. El ciclo **no
puede** cerrar en verde sin actualizar los cuatro. No es un extra: es el mecanismo que
este repo eligió y que hay que dejar funcionando.

---

## 2. POR QUÉ (1), (2) Y (3) SON UN CICLO Y NO TRES

No es "son parecidos". Es que **los tres son la misma afirmación**, escrita en tres
sitios, y que ninguno de los tres se puede comprobar sin los otros dos.

> **Lo que un detector promete es "todo lo que hay". Para que eso sea cierto, su
> alcance tiene que derivarse de la realidad, y la derivación tiene que compararse
> contra la realidad medida con `ast`.**

Aplicado:

| punto | el alcance está escrito a mano | qué pasa al mutarlo |
|---|---|---|
| (1) | el estado `None` está escrito a mano en la rama; el productor no lo emite | la rama se queda muerta **en verde** |
| (2) | los ficheros que hay que mirar están escritos a mano en una tupla | la lista desfasada no produce síntoma, porque el tercer módulo hoy no viola nada |
| (3) | que el alcance sea el correcto **no se comprueba en ninguna parte** | el guard puede volverse rama muerta y la suite sigue verde |

El argumento de cierre es concreto y no esesthetics:

1. **(1) sin (3) es un ciclo que repite el bug.** Arreglar (1) es poner el
   `try/except` yideo la rama pasa a existir. Una rama que existe y nadie ejecuta es
   *exactamente* el defecto que se iba a arreglar, un nivel más abajo. La rama recién
   viva no tiene ni un test, así que nadie sabe si funciona — que es la frase del
   propio encargo: *"si la rama nunca se ha ejecutado, nadie sabe si funciona"*.
2. **(2) sin (3) es un arreglo invisible.** La tupla fija no da ningún síntoma hoy
   (§1.3). Cambiarla por la tupla correcta de tres no cambia ningún resultado. El
   único test que distingue "derivé el alcance" de "escribí el alcance correcto a
   mano" necesita **un árbol sintético** con un cuarto módulo, y ese test es (3).
3. **(2) y (3) son la misma edición.** El guard tiene que pasar a ser una función a
   la que se le pueda pasar una raíz, para que un test la apunte a un árbol temporal.
   No se puede hacer la derivación en un commit y la auto-prueba en otro: en el
   primero el guard no es testeable, y en el segundo ya no queda nada que testear.

**Criterio de cierre del ciclo**: un solo commit, una sola ronda del
`mutation-auditor`, y las nueve mutaciones de §4 deben morir por `AssertionError`. Si
**M5** sobrevive, el ciclo **no** está cerrado, aunque todo lo demás esté en verde: M5
es la prueba de que el alcance se sigue escribiendo a mano.

---

## 3. DISEÑO

### 3.1 Punto (1) — el productor, no la rama

El arreglo es en `_recuento_de_tests` (`validate_docs.py:12-22`), **no** en la rama:

```python
def _recuento_de_tests(ruta_run_tests):
    try:
        with open(ruta_run_tests, encoding="utf-8") as f:
            fuente = f.read()
    except OSError:
        return None
    try:
        arbol = ast.parse(fuente)
    except SyntaxError:
        return None
    ...
```

Dos decisiones que hay que respetar:

- **`except SyntaxError`, no `except IndentationError`.** Medido: la sonda lanza
  `IndentationError`, que es subclase de `SyntaxError`. estrechar a `IndentationError`
  dejaría fuera `TabError` y volvería a abrir el mismo agujero por el otro lado.
- **El resto de la función no se toca.** Cuando el recuento es `None`, el `else:` de
  la línea 337 se salta y con él las comparaciones contra `STATUS.md` / `AGENTS.md` /
  `README.md` y la tabla de `testing-guide.md`. Es lo correcto: sin ancla no hay contra
  qué comparar, y saltárselo es lo que evita el "declaren 78, la verdad son 0".
- **No se edita la rama `if n_tests is None:`.** Ya está escrita para el contrato
  correcto. Editar la rama en vez del productor es el arreglo Espejo: deja la
  expectativa escrita a mano y un producer que no puede cumplirla.

Para que la rama sea **alcanzable desde un test** hace falta el mínimo de refactor:
extraer el cuerpo del check 7 a una función con firma
`_comprobar_recuento_de_tests(root, errors, ok)`, y que `main()` la llame. Sin eso, la
rama solo se puede despertar lanzando el validador entero contra el repo entero.

**Alternativa rechazada**: copiar el repo a `%TEMP%`, romper `run_tests.py` allí y
lanzar `python validate_docs.py` como subproceso. No requiere refactor, pero copia
`dist/` (26 MB) y un `.git` que el VFS de Nextcloud tiene corrupto, y depende de
`subprocess`, que en este entorno es la fuente documentada de `spawn EPERM`.

### 3.2 Puntos (2) y (3) — alcance derivado + control sobre árbol sintético

El guard de `run_tests.py:8101-8148` pasa a ser una **función que recibe la raíz**,
con el alcance derivado de la realidad:

- Recorrer `src/woptimizer/**/*.py` con `ast`.
- Seleccionar los módulos cuyo `ImportFrom` termina en `feedback`.
- Aplicar el contrato de llamantes a **todos** los call-sites de esos módulos,
  aceptando las **dos** formas de llamada: `ast.Name` (import directo) y
  `ast.Attribute` (`fb.mensaje_sin_apps`), que hoy se salta (§1.4).

**Por qué esto es total y no "más lista"**: un módulo que **no** importa desde
`feedback` no puede llamar a sus formateadores, y uno que sí lo importa entra solo en
el recorrido. El alcance no está escrito en ningún sitio: sale de medir. La lista de
dos ficheros no era una lista de ficheros, era una **apuesta sobre qué ficheros
importan**, y la apuesta tenía un fichero mal.

El test (§4) monta un árbol temporal con **cuatro** módulos: los dos reales, uno
sintético que importa `feedback` y cablea un verbo, y uno que no importa nada. El
control tiene que morir en el primero y NO morir en el cuarto.

### 3.3 Punto (4) — el mensaje

`huerfanos` (`validate_docs.py:340-342`) solo concatena el segmento de
`solo_invocados` cuando esa lista no está vacía. Dos líneas.

**Por qué entra aquí y no es un punto más**: el test de (1) necesita un tercer fixture
—un `run_tests.py` con un test definido y no invocado— para distinguir *"el mensaje se
emite"* de *"el mensaje es correcto"*. Con ese fixture en la mano, el segmento huérfano
está en la línea que el test acaba de escribir. Separlo sería gastar un ciclo entero
de pipeline por dos líneas.

---

## 4. CRITERIOS DE ACEPTACIÓN Y MUTACIONES EXIGIDAS

### 4.1 Criterios verificables

**A. Productor y rama viva**
1. `_recuento_de_tests` devuelve `None` ante `OSError` y ante `SyntaxError`, y la
   tupla de 4 en el camino sano. `except IndentationError` está **prohibido** (§3.1).
2. `_comprobar_recuento_de_tests(root, errors, ok)` existe y es la que contiene el
   check 7; `main()` la delega. Sin este refactor, A1 no es testeable.
3. Ante un `run_tests.py` con error de sintaxis, el validador **emite un informe** con
   una línea `[FAIL]` que nombra `run_tests.py`, y **no** propaga la excepción.
4. Ante un `run_tests.py` ausente, lo mismo.
5. `python validate_docs.py` sobre el repo real sigue en `0 FAIL` y rc=0.

**B. Alcance derivado y control**
6. El guard de los llamantes es una función que recibe una raíz. **No queda ninguna
   tupla literal de ficheros** en él.
7. Cubre las **dos** formas de llamada: `ast.Name` y `ast.Attribute`. Un
   `fb.mensaje_sin_apps("N", "apagar")` en cualquier módulo importador se marca.
8. El árbol temporal del control tiene ≥3 módulos importadores de `feedback`, uno de
   ellos sintético con un verbo cableado. El guard **lo marca nombrando fichero y
   línea**.
9. Control negativo: un módulo que **no** importa `feedback` y un call-site conforme
   (`pack.default_action`, y los literales `"start"` / `"kill"`, que sí son acciones
   válidas) **no** se marcan. Sin este criterio el guard podría marcarlo todo y
   seguir "en verde".
10. Los **tres** call-sites reales (medidos hoy) siguen conformes: ninguno se marca.

**C. El mensaje**
11. Con un test definido y no invocado, el mensaje **no** contiene el segmento
    `invocado y NO definido: .` ni ningún segmento con lista vacía.

**D. Higiene**
12. ASCII puro en todo `print()` nuevo. Los emojis de categoría van como escapes
    (`\U0001F7E1` para 🟡, `\U000026AA` para `⚪ Otros`, nunca `?` ASCII) — Trampa #16
    y §Emojis de `docs/known-issues.md`.
13. `python run_tests.py`, `python verify_ui_syntax.py` y `python validate_docs.py` en
    verde, y **`validate_docs.py` en rc=0**, lo que obliga a actualizar el número de
    tests en `STATUS.md`, `AGENTS.md`, `README.md` y en la tabla de
    `docs/ai/testing-guide.md`. El número lo deriva el validador con `ast`: se
    actualizan los cuatro ficheros, no se escribe el número a mano en el validador.
14. `docs/ai/testing-guide.md` recibe las filas de los tests nuevos en la tabla, con
    su numeración correlativa.
15. **Cero ediciones bajo `src/`.**

### 4.2 Mutaciones que el `mutation-auditor` DEBE ejecutar

Cada una tiene que morir por **`AssertionError`**, no por crash. Una muerte por
`TypeError` o por `AttributeError` es un mutante que revienta el código, no un test
que lo detecta — la lección del ciclo 26, fila 13 de la tabla retirada.

| id | mutación | qué tiene que morir |
|---|---|---|
| **M1** | `except (OSError, SyntaxError)` → `except OSError` (se cae `SyntaxError`) | el fixture de sintaxis rota deja de dar informe y lanza `IndentationError` (A3) |
| **M2** | `except (OSError, SyntaxError)` → `except SyntaxError` (se cae `OSError`) | el fixture de fichero ausente lanza `FileNotFoundError` (A4) |
| **M3** | la rama `if n_tests is None:` se vuelve rama muerta (`pass`, o `if False and …`) | los tres fixtures de fallo dejan de producir línea `[FAIL]` (A3, A4, A5) |
| **M4** | el `if n_tests is None:` pasa a `ok.append(...)` en vez de `errors.append(...)` | el mismo criterio, y además el resumen contaría un OK donde hay un fallo |
| **M5** | **el alcance derivado vuelve a una tupla literal de TRES ficheros** (los tres importadores reales de hoy) | el control de B8: el cuarto módulo sintético deja de marcarse. **Esta es la mutante que decide el ciclo** (§2) |
| **M6** | el guard vuelve a mirar solo `ast.Name` y descarta `ast.Attribute` | el criterio B7, con un módulo sintético que llama en forma `fb.mensaje_sin_apps(...)` |
| **M7** | el guard marca **todo**, incluidos los literales de acción válidos y `pack.default_action` | el control negativo B9, y los tres call-sites reales de B10 |
| **M8** | el recorrido derivado se limita a `src/woptimizer/ui/views/` (deja fuera un importador fuera de `views/`) | el criterio B8, con el módulo sintético colocado **fuera** de `views/` |
| **M9** | `huerfanos` vuelve a concatenar el segmento de `solo_invocados` sin mirar si está vacío | el criterio C11: vuelve el `invocado y NO definido: .` |

**Mutante de control que el auditor debe correr y declarar explícitamente**: M5 mutado
**más** M4 mutado a la vez, para comprobar que el guard de la rama no se solapa con el
del alcance. Si alguno de los dos muere solo por el otro, hay una dependencia
invisible entre ellos y hay que decirlo en el informe.

**Sobre M5 en particular**: si el dev cierra el ciclo con la tupla de tres ficheros
"porque hoy son tres", el mutante M5 **no tiene a quién matar** y el ciclo se cierra
con el defecto intacto. Es el escenario que este encargo tiene que evitar, y la razón
de que el test se exija sobre **árbol sintético** y no sobre el repo real.

---

## 5. LO QUE NO ENTRA, Y POR QUÉ

### 5.1 Punto (5) — el smoke test de compilación: **no es una tarea, es una decisión**

`STATUS.md:11` y `STATUS.md:65` llevan desde el ciclo #11 un 🟡/⏳ que dice
"pendiente de regenerar", y el checkpoint dice "cada 3 ciclos": ha saltado cinco veces
y se ha ignorado cinco veces. `dist/woptimizer.exe` es de 2026-09-29, 26.900.209 bytes.

**Por qué no es una tarea**: no es código, no lo puede hacer `openspec-dev`, no se
puede mutar (no hay mutación de un binario), y `force_build.py` necesita `subprocess`
en un entorno con `spawn EPERM` documentado. Meterlo en el ciclo lo convierte en un
paso que puede tumbar la ronda sin enseñarnos nada.

**Mi decisión, y es una decisión de architect**: el checkpoint **deja de ser un
contador de ciclos**. Pasa a dispararse por una **condición**: hay un exe released y
el código ha cambiado desde el último build. Un checkpoint que se salta cinco veces
seguido y sigue ahí no es un checkpoint, es un 🟡 de adorno — y un tablero con un 🟡
permanente que nadie mira es peor que uno sin él, porque entrena al lector a ignorar
el semáforo. `STATUS.md` pasa a decir la verdad en una línea: *el ejecutable es un
artefacto de distribución, se regenera al publicar, y su desfase con el código no lo
vigila nadie*. **Pregunta para el propietario, no bloqueante**: ¿el exe se usa a diario
o es solo el artefacto que se descarga? Si se usa a diario, el desfase de 15 ciclos es
un riesgo de seguridad —el doble tap del ciclo 12 y el blindaje anti-brick del 13 no
están dentro— y la respuesta es regenerar ya, no cambiar el checkpoint. El
`architect-review` no puede decidir eso: no sabe qué hace el usuario con el binario.

### 5.2 Punto (6) — el validador no comprueba `docs/ai/`: **deferido con la decisión ya tomada**

Cierto, y más grave de lo que el briefing sugiere: el validador no mira
`architecture.md`, `data-models.md`, `ui-design-system.md` ni `sandbox-rules.md`. Todo
lo que el ciclo 26 escribió ahí está fuera de la red.

**Por qué no entra**: no es un check, es el **diseño de una familia de checks**, y su
superficie es toda la documentación viva del proyecto. Meterlo aquí convierte el
ciclo en el de seis temas que este repo no puede auditar en una ronda.

**La decisión que sí tomo ahora, para que el siguiente ciclo no vuelva a preguntar**:
las afirmaciones de la documentación se verifican en **`run_tests.py`, no en
`validate_docs.py`**. El motivo es que un check del validador **no es mutation-auditable**
—nadie rompe `STATUS.md` a propósito para ver si el check lo nota— y una aserción en la
suite sí: el `mutation-auditor` la rompe y comprueba que muere. Ya existe el
precedente: `test_la_documentacion_del_blindaje_no_puede_desfasarse` re-deriva con
`ast` los 34 nombres de `SYSTEM_PROTECTED_PROCESSES` que `architecture.md` afirma, y
vive en `run_tests.py`, no en el validador. **Siguiente ciclo, Área 5 (Testing &
Calidad), con el diseño ya cerrado y no solo la pregunta.**

### 5.3 Lo que el encargo plantea mal (registrado para que no se repita)

- El punto (2) **no** es "un tercer módulo no lo encuentra y da KeyError con
  traceback". Hoy no hay síntoma: el tercer módulo importa `mensaje_cierre_pack`, que
  el guard no vigila. **La ausencia de síntoma es lo que hace peligroso al mutante
  M5**, y es el motivo de que el test vaya sobre árbol sintético.
- La rama de (1) **no** produce falso verde. Rigorosamente: rc=1 en ambos fallos.
  Es agujero de diagnóstico. La severidad 🟡 es correcta y no debe inflar.

---

## 6. ORDEN DE EJECUCIÓN

1. `openspec-dev`: puntos (1) y (4) en `validate_docs.py` + el test que los prueba.
2. `openspec-dev`: puntos (2) y (3) en `run_tests.py` (el guard a función + el control
   sobre árbol sintético). **Mismo commit que el paso 1** (§2.3).
3. `openspec-dev`: actualizar los cuatro ficheros que declaran el recuento de tests.
4. `mutation-auditor`: las nueve mutaciones de §4.2, más el par combinado M5+M4.
5. `architect-review`: **no** se cierra el ciclo con M5 vivo.
