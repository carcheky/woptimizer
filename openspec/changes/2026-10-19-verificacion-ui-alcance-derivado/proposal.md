# El alcance de `verify_ui_syntax.py` esta VACIO: verde con el codigo roto

**Tarea:** TASK-081 · **Ciclo:** 67 · **Rama:** `beta`

---

## 0. EL HECHO, MEDIDO

`verify_ui_syntax.py:9-20` no mira la UI: mira **diez rutas escritas a mano**.

```python
files_to_check = [
    'src/woptimizer/ui/app.py',            # 10 entradas, fijadas en 2026-09-28
    ...                                     # y el ultimo toque real de la lista
]                                          # fue bbcc472 (2026-10-18), anadiendo
                                           # UN modulo de un dia de antiguedad
```

El arbol real tiene **12** ficheros `.py` bajo `src/woptimizer/ui/` y los que quedan
fuera de la lista son **`theme.py`** y **`tray_menu.py`**, dos modulos con codigo de
produccion.

Medido en camara desechable, con control positivo:

| Escenario | Modulo roto | Exit | Veredicto |
|---|---|---|---|
| A0 | — (repo intacto) | **0** | control |
| M1 | `ui/theme.py` (**no listado**) | **0** | 🟢 **VERDE** |
| M2 | `ui/tray_menu.py` (**no listado**) | **0** | 🟢 **VERDE** |
| M3 | `ui/app.py` (**listado**) | **1** | 🔴 control positivo: **discrimina** |
| M4 | `ui/views/ajustes_view.py` (**nuevo**) | **0** | 🟢 **VERDE** |

**El guard discrimina sobre su lista (M3) y no ve nada fuera de ella (M1, M2, M4).**
Eso es un guard vaciable, medido, no supuesto.

M4 es el caso que se va a dar: el dia que alguien anada una vista, la puerta de
sintaxis de CI **no lo mirara**.

---

## 1. YA PASO DOS VECES, Y NO FUE SUPUESTO

Historia de solo lectura del repo:

| Fichero | Ultimo commit | Fecha |
|---|---|---|
| `verify_ui_syntax.py` | `bbcc472` | 2026-10-18 |
| `src/woptimizer/ui/theme.py` | `2b81978` | 2026-10-01 |
| `src/woptimizer/ui/tray_menu.py` | `a8b2a89` | 2026-10-04 |

Los dos modulos se crearon **despues** del ultimo toque real de la lista y nunca
entraron. El unico toque posterior (`bbcc472`, TASK-073) anadio `tk_thread.py`, un
modulo de un dia: la lista se actualiza **a mano, cuando alguien se acuerda**, y
dos veces de treinta se acordado.

Y el.repo **ya identifico este agujero y eligio el arreglo que degrada el guard**:
`openspec/changes/2026-09-29-double-tap-confirmation/proposal.md:319-320` lo titula
*«`verify_ui_syntax.py` no valida ficheros nuevos — MENOR»*, y el arreglo fue
**anadir `confirmation.py` a la lista** (`proposal.md:73`, `:271-272`). Setenta y
seis ciclos despues la lista sigue siendo una lista, y ahora esta dos modulos
corta. **El hallazgo era correcto y el arreglo lo mato.**

---

## 2. LA PROPIEDAD ESTRUCTURAL

> **Un guard es vaciable cuando el conjunto de sujetos que mira esta escrito
> como una enumeracion literal dentro del propio guard, y ese conjunto es un dato
> DERIVADO del sistema de ficheros y no una constante del dominio.**

La enumeracion y el conjunto son dos fuentes de verdad que **nadie ata**. El guard
puede responder de si los diez ficheros estan bien sin decir absolutamente nada
sobre el undecimo, y no hay forma de que se entere.

De ahi sale la trampa, y es la que el repo ya piso:

- **Arreglar el caso no arregla la clase.** Anadir el modulo que faltaba mantiene
  la lista viva: se vuelve a caducar en el siguiente modulo, y esta vez sin que
  nadie mire el changelog para notar que el "9 de 9" de 2026-09-29 es un "12 de 12"
  de hoy.
- **Anadir el caso a una lista de permitidos la empeora**, porque las
  comprobaciones especificas solo se aplican a la rama principal.

Y hay una ironia util: **el repo ya tiene la respuesta a cuatro mil quinientas
lineas de distancia.**

```python
run_tests.py:12725    src_files = [p for p in src_dir.rglob("*.py")]     # DERIVADO
run_tests.py:1084     for py_file in src_dir.rglob("*.py"):              # DERIVADO
run_tests.py:8198     archivos = ["src/woptimizer/ui/main_window.py",   # ENUMERADO
                       ...]
run_tests.py:13184    ficheros = ("llms.txt", "llms-full.txt", ...       # ENUMERADO
```

Cuatro guards sobre ficheros del repo. Dos derivan el alcance y por eso no pueden
quedarse cortos. Dos lo escriben a mano y por eso se han quedado.

---

## 3. LO QUE SE ELIGE, Y POR QUE ES EL DE MAYOR CONSECUENCIA

Criterio del repo: **«¿se manifestaria si el codigo o el documento estuvieran mal?»**

Un fallo que solo produce ruido — un rojo con el fichero y la linea nombrados —
es **bomba de mantenimiento, no agujero**. Hace falta texto, tiempo y ruido para
cada iteracion, pero nadie queda creyendo que el codigo esta bien.

Aplicado al inventario medido:

| # | Guard | Se manifestaria con codigo roto? | Clase |
|---|---|---|---|
| **1** | **`verify_ui_syntax.py:9-20`** | **NO. Medido: verde.** Y corre en **CI** (`release.yml:87`) | **AGUJERO** |
| 2 | `test_no_literal_colors_in_views` (`run_tests.py:8198-8203`) | NO: lista 4 de 12 modulos. Pero un color literal no rompe la app | AGUJERO menor |
| 3 | `_copiar_el_esqueleto_del_validador` (`run_tests.py:13184-13186`) | **SI. Medido en las 8 celdas: todo borrado da ROJO** con fichero y linea nombrados | **BOMBA** |
| 4 | otros 24 guards sin contraprueba | sin medir uno a uno | no establecido |

El **1** gana por tres motivos que no se pueden quitar:

1. **Es el unico que corre en CI sin contraprueba.** MEDIDO: `verify_ui_syntax` no
   aparece en **ningun test** del repo; su unica mencion en `run_tests.py` es
   `13177`, dentro de un docstring. Cero contraprueba, cero red.
2. **Ya fallo dos veces de hecho** (`theme.py`, `tray_menu.py`), no en teoria.
3. **Se reproduce sin incidente**, en ocho segundos — ver §5.

El **3** es la misma forma pero **no es agujero**, y formalizarlo seria un error de
diagnostico. Queda documentado como bomba, no se arregla aqui.

---

## 4. EL INVENTARIO DE LA CLASE

Metodo: los **226** tests de `run_tests.py` se separan en **guards estructurales**
(afirman sobre la *forma* de un fichero) y **tests de comportamiento** (afirman
sobre lo que hace el codigo). Solo los guards pueden ser vaciables por enumeracion.

| | Recuento |
|---|---|
| tests de comportamiento | 146 |
| **guards estructurales** | **80** |
| — **(a) sin contraprueba** | **27** |
| — **(b) con contraprueba que NO construye una variante degradada** | **12** |
| — **(c) con contraprueba que construye la variante y exige el rojo** | **41** |

⚠️ **Honestidad del metodo.** El criterio de (b) es *«menciona el control pero no
construye una variante»*, no *«el control es logicamente tautologico»*. El bucket (b)
es una **sobreestimacion**: incluye guards con contraprueba real que mi criterio
estatico no vio construir (por ejemplo `test_la_politica_eol_cubre_todo_script_de_consola_que_existe`,
que si trabaja en `%TEMP%`). Reparto (b)/(c) exacto: trabajo del `mutation-auditor`.
El reparto (a) contra (b+c) si es defendible, porque (a) se detecta por ausencia.

### Ranking de los (a) sin contraprueba

| # | Guard | Nota |
|---|---|---|
| **1** | `verify_ui_syntax.py:9-20` | **ELEGIDO.** Medido, corre en CI, ya fallo dos veces |
| 2 | `test_no_literal_colors_in_views` (`run_tests.py:8198`) | Misma forma. Su control (`8223-8226`) prueba que **el detector** detecta, no que la **lista** este completa |
| 3 | `_copiar_el_esqueleto_del_validador` (`run_tests.py:13184`) | Misma forma, pero **bomba**: medido que todo borrado da rojo |
| 4 | `test_dead_code_ast_guard` (`run_tests.py:12764-12769`) | El «control negativo» es casi tautologico: `assert "X" in monitored` dice que el fichero existe, que es lo mismo que el `assert len(src_files) >= 10` de `12726`. El unico control real es `assert "_get_priority" not in monitored` |
| 5 | `test_la_documentacion_del_blindaje_no_puede_desfasarse` (`run_tests.py:7197`) | Sin medir |
| 6-27 | resto | Sin medir; consecuencia no establecida |

---

## 5. SI EL ARREGLO NECESITA PRODUCTO: SI, Y ESTA MEDIDO

La entrada 3 de la lista del encargo (el guard que indexaba por nombre de fichero)
era invisible sin dos ficheros homonimos en sitios distintos. **Esta no necesita
eso: no necesita incidente.**

```powershell
# ocho segundos, sin incidente, sin tocar el repo
python verify_ui_syntax.py                                  # exit 0
# anadir src/woptimizer/ui/views/ajustes_view.py con "def roto(:" dentro
python verify_ui_syntax.py                                  # exit 0   <- M4
```

Y hay una razon por la que el agujero **no esta compensado**, aunque hoy lo parezca:
`theme.py` y `tray_menu.py` se detectan porque `run_tests.py:279` importa
`woptimizer.ui.app` sin proteccion y de ahi cuelgan por el grafo de imports. Eso es
**cobertura por casualidad**, y depende de que todo modulo tenga un camino de
importacion hasta `app.py`. **M4 no lo tiene: nada lo importa, nada lo detecta.**

---

## 6. DECISION DE DISENO

**R1 — El sujeto se deriva, no se enumera.** `verify_ui_syntax.py` pasa a
`rglob("*.py")` sobre `src/woptimizer/`. Sin lista, no hay lista que envejezca. No es
una tecnica nueva en el repo: ya esta en `run_tests.py:12725` y `:1084`.

**R2 — Sin lista de exentos.** El derivado cubre tambien los `__init__.py`. **No se
anade ninguna lista de permitidos**, porque una lista de exentos es una lista mas
que envejece y degrada el guard en la rama principal.

**R3 — La cifra escrita a mano se retira.** `STATUS.md:11` dice «10 modulos» y
`CHANGELOG.md` ha dicho «8 de 8», «9 de 9» y «10» en distintas épocas. El script
imprime el recuento derivado y `STATUS.md` lo declara **derivado**. Cierra por el
camino corto **D2/D3** para esta fila.

**R4 — El guard mira el PRODUCTO, no la fuente.** ⚠️ **Trampa evitada**: si el guard
comparase `rglob` contra `rglob` seria tautologico, porque las dos mitades serian la
misma expresion. El guard tiene que **ejecutar `verify_ui_syntax.py` de verdad**
contra un arbol sintetico con un modulo roto, y exigir salida 1. El sujeto del guard
es el codigo ejecutado; eso es lo que hace imposible falsearlo con un comentario.

**R5 — La clase se cierra con un guard de FORMA, no de caso.** Un guard con `ast`
que prohibe enumeraciones literales de rutas bajo `src/woptimizer/**.py` en
`run_tests.py`, `validate_docs.py` y `verify_ui_syntax.py`, **salvo que la funcion
derive el alcance** con `rglob`/`os.walk`/`iterdir`/`glob`. El mensaje **nombra**
cada hallazgo.

⚠️ **ElJulie R5 es el punto donde esta la honestidad del encargo.** Sin el, el
siguiente guard con lista escrita a mano aparece igual. Con el, aparecen las dos
pre-existentes (`run_tests.py:8198` y `:13184`) **por el nombre y la linea**, que es
lo que las hace deuda visible en vez de agujero invisible. **R5 no las repara: las
denuncia.** Repararlas es trabajo del ciclo que las recoja, y para entonces ya estan
nombradas.

⚠️ **Y la trampa de la lista de permitidos, explicitamente:** las dos
enumeraciones pre-existentes que R5 encuentra NO pueden entrar en una lista muda de
rutas permitidas. Cada una lleva, **en el docstring de su propio guard**, una frase
que dice (a) por que existe la enumeracion y (b) que la retira. Una entrada sin esas
dos frases es un guard degradado y R5 debe rechazarla.

---

## 7. CRITERIOS DE ACEPTACION

Cada AC lleva el mutante que lo mata, declarado por adelantado.

### AC-1 — El alcance se deriva y no se enumera
`verify_ui_syntax.py` obtiene sus ficheros con `rglob("*.py")` sobre
`src/woptimizer/` y **no contiene ninguna tupla o lista de literales de ruta**.
Comprobado con **`ast`**, no con busqueda de texto.

- **Mata `M-L`** — reintroducir la tupla literal de 10 rutas.
- **Mata `M-R`** — dejar `rglob` escrito en un comentario o en codigo muerto: un
  guard de texto pasaria, uno de AST no.
- *Equivalente vs sin cobertura*: un `rglob` en el modulo pero **sin usarse** para
  la enumeracion es **SIN COBERTURA** y debe morir tambien.

### AC-2 — El recuento es derivado, no escrito
El script imprime el numero que ha derivado, y `STATUS.md` lo declara derivado.
Un guard compara la cifra que imprime el script con la que declara `STATUS.md`.

- **Mata `M-S`** — volver a «10 modulos» como cifra fija.

### AC-3 — CONTRAPRUEBA: un modulo nuevo, no listado por nadie, se detecta
En `%TEMP%`: `src/` real + `verify_ui_syntax.py` + un modulo **nuevo** con error de
sintaxis. Se exige **exit 1** y que la salida **nombre ese modulo**.

- **Mata `M-L`** por la via del **producto**, no del texto: es imposible de falsear
  con un comentario.
- Este es el AC que **no puede sobrevivir sin el fix**, y es el que responde a M4.

### AC-4 — Control positivo de AC-3 (sin el, AC-3 no significa nada)
El mismo arbol **sin** el modulo roto da **exit 0**; y con un modulo **sano**
anadido tambien **exit 0**.

- **Mata `M-C`** — una camara que devuelve exit 1 siempre. Sin este control, AC-3
  lo cumpliria un script permanently roto. Es el control que faltó en el ciclo 66 y
  por eso el mutante `S2` sobrevivio.

### AC-5 — El guard de forma: ninguna enumeracion de rutas bajo `src/`
Con `ast`, en `run_tests.py`, `validate_docs.py` y `verify_ui_syntax.py`: ninguna
funcion contiene una lista o tupla de **dos o mas** literales de ruta bajo
`src/woptimizer/**.py` sin derivar el alcance con `rglob`/`os.walk`/`iterdir`/`glob`.
Cada hallazgo se nombra con fichero y linea.

- **Mata `M-W`** — reintroducir la lista de 4 rutas en `run_tests.py:8198`.
- **Denuncia**, no repara, `run_tests.py:8198` y `run_tests.py:13184`.
- Las excepciones pre-existentes exigen justificacion escrita en el docstring de su
  guard (R5).

### AC-6 — Cierre en verde y sin cifras a mano
`python verify_ui_syntax.py` en exit 0 sobre el repo real con el recuento derivado;
`python run_tests.py` en exit 0; `python validate_docs.py` en 0 FAIL; y ni
`STATUS.md` ni `CHANGELOG.md` con una cifra de modulos UI escrita a mano.

---

## 8. LO QUE ESTA FUERA DE ALCANCE, Y POR QUE

- **`_copiar_el_esqueleto_del_validador` (`run_tests.py:13184`)**: MEDIDO que
  quitar cualquiera de sus entradas da **ROJO con fichero y linea nombrados**. Es
  bomba de mantenimiento, no agujero. Arreglarlo seria trabajo sin agujero que
  cerrar, y R5 lo deja nombrado.
- **`test_no_literal_colors_in_views` (`run_tests.py:8198`)**: suEnumeracion es la
  misma clase y R5 la delata. Reparar su cobertura es un ciclo propio.
- **`test_dead_code_ast_guard` (`run_tests.py:12764-12769`)**: su control negativo
  es casi tautologico, pero ya deriva el alcance con `rglob` y no es un agujero.
- **Los 24 restantes (a)**: sin medir uno a uno. Medirlos es trabajo del
  `mutation-auditor`, no de este ciclo.
- **TASK-080** (activar el validador en CI): **no se toca.** Su propia medicion dice
  que CI no puede dar verde todavia (25 hashes de `rd_journal.json` sin pushear).
  Activarlo hoy rompe el pipeline.

---

## 9. RESTOS DECLARADOS

- `_chk.py` (488 B), `_chk2.py` (211 B) y `_matrix_c26.py` (20 668 B) son
  **scripts sueltos TRACKEADOS en la raiz**, del ciclo TASK-036. No los toca este
  ciclo; se declaran porque `test_no_legacy_test_files_in_root` (`run_tests.py:12649`)
  vigila `test_*.py` y no este patron: **la misma clase de enumeracion, en la raiz.**
- El reparto exacto (b)/(c) de los 80 guards lo cierra el `mutation-auditor`.