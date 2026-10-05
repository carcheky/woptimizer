# Arranque por categorias en el Gestor: la premisa era falsa y el hueco que la dejo viva es un mutante sin guardian

**Tarea:** `TASK-068` (fila 🔴 115 de `STATUS.md`, reportada por el dueño el 2026-10-05).
**Área:** UI / modelos de datos. **Depende de:** `TASK-063` (cerrada) y `TASK-067` (cerrada).
**Naturaleza de este documento:** planificación. Cero ediciones bajo `src/`.

---

## 1. La distinción que fija el listón: MEJORA QUE NO OCURRE, no pérdida

Medido sobre el `profiles.json` que el dueño tenía delante: el pack `sync` tiene
`target_categories: ["🟢 Sincronización", "🟡 Launchers Gaming"]` y **`start_categories` vacío**.
Con la lista vacía **no se pierde nada de ese pack**: nadie ha marcado nada que la app
deja de hacer. El modo de fallo es el contrario y es el que se midió: **una mejora
que el usuario pidió y que no ocurre**, y su forma es *ausencia de efecto con un toast
que miente*.

Eso fija el listón antes de elegir nada:

| | Pérdida | Mejora que no ocurre |
|---|---|---|
| Qué se rompe | apps que estaban y no están | apps que nunca llegaron a estar |
| Reversibilidad | recuperable con re-lanzar | ninguna, no había nada que recuperar |
| Qué lo arregla | **no se tolera**: parar el daño | **se tolera con un aviso honesto**, y el arreglo es de llevadero, no de datos |
| Test que lo prueba | el dato sigue ahí después | el aviso dice lo que pasó |

El listón de `TASK-068` es por tanto el de una mejora: **vale con que el usuario se entere**.
Lo que **no** vale es que la app diga que lo hizo.

---

## 2. La premisa del encargo es FALSA en HEAD, en tres puntos

El encargo (y la `description` de `TASK-068`, y la fila 115 de `STATUS.md`) afirma tres
cosas. Las tres son falsas contra el código. Con `archivo:linea`:

### 2.1 «El botón Iniciar ignora `start_categories` por completo» — FALSO

`PackManagerView.start_pack()` **ya suma las dos listas**:

```python
# src/woptimizer/ui/views/pack_manager_view.py:665-671
started, failed = self.process_service.start_pack_apps(apps)
if categorias:
    started_cats, failed_cats = self.process_service.start_pack_categories(
        categorias, pack.target_categories
    )
    started += started_cats
    failed += failed_cats
```

`categorias` sale de `categorias = list(pack.start_categories)` en
`pack_manager_view.py:658`, y el comentario de `:660-664` **cita TASK-063** y dice
exactamente lo mismo que el de la Portada. La puerta del Gestor y la de la Portada
(`dashboard_view.py:503-509`) son **la misma decisión escrita dos veces**, y las dos suman.
No hay ninguna incoherencia entre UI y servicio que arreglar: **ya están de acuerdo.**

### 2.2 «`pack_service.start_pack()` es la puerta que ignora el campo» — FALSO: ese método no existe

`grep 'def start_pack' src/woptimizer` devuelve **dos** métodos, y ninguno es de `PackService`:

- `src/woptimizer/services/process_service.py:812` `start_pack_apps`
- `src/woptimizer/services/process_service.py:886` `start_pack_categories`

**No existe `PackService.start_pack()`.** La puerta de arranque del Gestor es un método
de la **vista** (`pack_manager_view.py:641`), no del servicio, y no delega en un servicio
que «ignore» nada. Quien lea la `description` de la tarea y busque ese método para
arreglarlo no va a encontrar nada, y ese es el modo de fallo que produce la premisa.

### 2.3 «El `filter` por categoría se escribe en el pack al arrancar (`pack_service.py:447`)» — FALSO por partida doble

- `grep 'filter' src/woptimizer/services/pack_service.py` → **cero coincidencias**. El
  atributo `filter` no existe en `PackService`. Lo que existe es `default_action`
  (`models.py:83`), que no se escribe al arrancar.
- La línea `pack_service.py:447` es una **línea de docstring** de `_diagnosticar_y_migrar`
  (código de `TASK-069`, que desplazó el fichero). La citaCaducó al cerrarse `TASK-069`.

No hay efecto colateral que resolver porque no hay nada que resuelva.

---

## 3. El residuo REAL, y por qué se produjo la premisa

### 3.1 El fallo, con la forma que el dueño describió, medido

`start_pack_categories` tiene **tres** ramas de «no se arranca nada» y **solo una cuenta**:

| Rama | `archivo:linea` | ¿Cuenta? | ¿Aviso en UI? |
|---|---|---|---|
| categoría 🔴 (`tier == "danger"`) | `process_service.py:918-923` | **no** — `continue` pelado | **no** |
| la misma categoría está en `target_categories` | `process_service.py:924-929` | **no** — `continue` pelado | **no** |
| sin ningún ejecutable resoluble | `process_service.py:931-940` | sí, `failed += 1` | sí, ámbar |

Las dos primeras sí escriben en el log (`logger.warning`, `:919` y `:925`), pero el log no
lo ve el usuario. Y su consecuencia es la que el dueño describió, con una forma
concreta: con 0 apps y la única categoría marcada omitida, la puerta devuelve
`(0, 0)`, y entonces:

```python
# src/woptimizer/ui/views/pack_manager_view.py:672-673
if failed == 0:
    self.after(0, self._inline_status, f"🚀 {started} apps iniciadas · '{nombre}'.", VERDE)
```

**Un toast VERDE de «0 apps iniciadas»** con la mejora sin ocurrir y sin una sola palabra
de aviso. Es exactamente la clase que el ciclo 26 cerró en la puerta de apagado («el
`started` en verde») y que el propio docstring de `process_service.py:932-935` dice
querer evitar — pero solo para la tercera rama. Las dos primeras se le saltaron.

### 3.2 La premisa falsa es, literalmente, un mutante que hoy sobrevive

Este es el hallazgo quejustify el ciclo. El doble de test de la puerta del Gestor
**ya tiene** los campos para comprobar la suma, y **ningún test los lee**:

```
run_tests.py:9177  self.llamadas_categorias = 0        <- se inicializa
run_tests.py:9178  self.arranque_categorias = (0, 0)   <- se inicializa
run_tests.py:9191  self.llamadas_categorias += 1       <- se incrementa
run_tests.py:9194  return self.arranque_categorias      <- se devuelve
```

`llamadas_categorias`, `arranque_categorias`, `categorias` y `target_categories` tienen
**2, 2, 2 y 1 ocurrencias en todo `run_tests.py` y las cuatro son definición o incremento.
Cero aserciones.** El andamiaje se construyó y la aserción nunca se escribió.

Y el pack del test no puede entrar por esa rama:

```python
# run_tests.py:9659
pack_normal = Pack(id="trabajo", name="Trabajo", apps=list(APPS))   # sin start_categories
# run_tests.py:9889  (la unica asercion del arranque del Gestor)
assert procs.llamadas_arranque == 1 and procs.apps == APPS
```

Con `start_categories == []` el `if categorias:` de `pack_manager_view.py:666` **nunca se
toma** en esa prueba. Consecuencia medida: **borrar `pack_manager_view.py:666-671` deja la
suite de 183 en verde.** El guard textual de `run_tests.py:14927`
(`cod.count("pack.start_categories") >= 2`) tampoco lo caza, porque la línea que borra el
mutante es la `:658` (`categorias = list(pack.start_categories)`) y esa sigue puesta.

Por eso la premisa del encargo no es un descuido de quien leyó: es **la lectura honesta
de un código que ningún test contradice**. Una puerta sin aserción se lee como una puerta
sin comportamiento, y esta se lee como una puerta que ignora el campo.

### 3.3 El otro síntoma que venía en el mismo reporte NO es de esta tarea

«No veo packs en la Portada» no tiene nada que ver con `start_categories`. La Portada
lista **solo favoritos**: `dashboard_view.py:340` `favorites = self.pack_service.get_favorite_packs()`,
y con la lista vacía pinta el rótulo de `dashboard_view.py:352`
«No tienes packs marcados como favoritos (⭐).». Es diseño, no bug: si el pack no está
marcado con estrella, no sale. La perdida de datos que si hubo en este host es
`TASK-069`, y está **cerrada**. Este ciclo no la toca.

---

## 4. La decisión de destino, y por qué la pregunta de (a)/(b)/(c) es **moot**

El encargo pide elegir entre hacer que `start_pack()` sume (a), retirar `start_categories`
del modelo y de la UI (b), o dejarlo y avisar (c). **La medición elimina las tres**:

- **(a) ya está hecha.** `pack_manager_view.py:665-671` es exactamente (a), escrita, con
  su comentario y su conflicto resuelto en el servicio. No hay nada que decidir.
- **(b) no tiene objeto.** Retirar el campo sería borrar una capacidad que la UI promete
  con las casillas `(arrancar)` (`pack_manager_view.py:450-462`), que el modelo valida
  (`models.py:56-66`) y que la Portada usa igual. Y sería una migración de
  `profiles.json`, que es dato del usuario: un trabajo de datos para deshacer una
  decisión que nadie ha pedido. **No se hace.**
- **(c) «dejarlo como está y avisar» es lo que decide este plan**, porque (a) ya está y
  lo que falta es el aviso.

**¿Revierte TASK-063? NO, y no puede.** La razón está medida en el propio commit:
`e0f20db feat(categorias): puerta comun execute_pack con las barreras DENTRO (TASK-063 T-1/T-3)`
es de **2026-10-03 04:47:27**, y el `dist\woptimizer.exe` que el dueño probó es de
**2026-10-03 04:49:42** — dos minutos después. El binario que el dueño ejecutó **ya
tenía la suma**. La decisión de TASK-063 no se revierte: **nunca estuvo ausente del
build que se probó**, y el defecto que el dueño vio es el del toast verde de `:673`,
que es un defecto de la capa de **presentación del recuento**, no de la política.

### 4.1 El 🟢 y el 🟡: dónde está el riesgo real, y por qué no es el que se temía

El encargo teme que arrancar categorías «también las mate» y que ahí estén las
`🟡 Launchers Gaming`. **Es falso: la puerta de arranque no mata nada.** El único efecto
de `start_pack_categories` es `self._lanzar(ruta)` (`process_service.py:951`); no hay
`terminate()` en toda la función, ni en `start_pack_apps`. Arrancar y apagar son puertas
distintas con servicios distintos.

El riesgo real de arrancar es otro, y es de **amplitud, no de destrucción**:

| | Riesgo real | Medida |
|---|---|---|
| 🟢 Sincronización | ninguno: son servicios de fondo sin ventana, es justo para lo que sirve una pack de arranque | sin techo |
| 🟡 Launchers Gaming | **abre N ventanas que el usuario no enumeró** (Steam, Epic, Battle.net, GOG: lo que la DB asocie a la categoría). No destruye nada, pero ocupa RAM y es exactamente la amplitud que el `tray` tuvo que acotar | depende de `_patrones_de_categoria` |

La combinación realmente peligrosa —una categoría en las dos listas— **ya está resuelta a
favor de apagar** en tres capas: la casilla espejo de la UI
(`pack_manager_view.py:428-430`), el contrato del modelo (`models.py:56-60`) y el servicio
(`process_service.py:924-929`). Con eso, **arrancar por categoría no necesita
confirmación**: el contrato escrito de `ui-design-system.md:331` y `:371` dice que
arrancar no es destructivo y no pide nada, y ese contrato se cumple hoy.

---

## 5. La doble pulsación: no aplica, y por qué

La regla de `ui-design-system.md:342` es, textual: *«ningún camino de **kill** nuevo puede
añadirse sin `_require_double_tap`»*, y las tres rutas inventariadas en `:328-329` son las
de apagado. `ui-design-system.md:331` lo dice del arranque sin ambigüedad:
*«`execute_pack` confirma **solo** en la rama `default_action == "kill"`. Arrancar apps no
es destructivo y no pide nada.»*

`PackManagerView.start_pack()` **no** llama a `_require_double_tap` y **no debe** hacerlo:
no es un camino de kill, no hay estado que perder y el usuario pidió arrancar. Añadirle
confirmación sería inventar una cuarta excepción para un caso que el documento excluye
expresamente, y empeoraría el arranque de una pack sin proceso visible.

**La asimetría que sí queda, y que no es de seguridad:** arrancar por categoría abre una
ventana por cada ejecutable, y una de esas puede ser 🟡. Ahí la pregunta es de **UX** (ver
P-1 abajo), no de doble pulsación.

---

## 6. Lo que este ciclo arregla, en una frase

Cerrar el **hueco de verificacion** que produjo la premisa (T-1), hacer que el **refuse
cuente** para que la mejora que no ocurre se vea como tal y no como un éxito verde (T-2),
y **corregir el texto que llama «apps» a un recuento que mezcla apps y categorías** (T-3),
que es la misma mentira que el ciclo 26 cerró en la puerta de apagado
(`ui-design-system.md:387-391`).

---

## 7. Las dos preguntas cerradas al dueño

Ninguna es «arregla el bug»: las dos son política de producto sobre el **techo** del
arranque por categoría, que el código no puede decidir por sí solo. Son la parte de
`TASK-068` que sí le corresponde.

### P-1 — Con 🟡 marcada para arrancar, ¿se acepta abrir N launchers de golpe?

- **(a) Se acepta y el mensaje nombra la categoría.** Consecuencia medible: el toast pasa
  a decir `🚀 4 apps iniciadas · 'X' (1 categoría: 🟡 Launchers Gaming)`. **0 cambios de
  política**, 1 línea de formato, y el usuario ve el alcance en el momento en que ocurre.
- **(b) 🟡 pasa a ser inerte en `start_categories`, igual que 🔴.** Consecuencia medible:
  el predicado de `process_service.py:918` pasa a ser `tier in ("danger", "caution")`, con
  la misma línea simétrica en las dos listas (la de apagado ya la tiene en
  `gaming_service.py:104`). El usuario **no puede** arrancar launchers por categoría nunca;
  para eso tiene la lista `apps` explícita, que abre **un** ejecutable. Se paga con
  capacidad, y se gana que ninguna acción del producto abra algo que el usuario no nombró.
- **(c) Nada.** Consecuencia: 🟡 se abre en bloque y en silencio, que es el estado actual.

**Recomendación del arquitecto: (b).** El motivo no es miedo a 🟡 en sí, es que el producto
ya decidió esto dos veces por el mismo argumento y en el otro lado: la excepción del `tray`
se acotó *precisamente* porque «cerrar por categoría cierra procesos que el usuario nunca
enumeró» (`ui-design-system.md:339`), y TASK-065 la recortó cuando la excepción empezó a
crecer. Abrir N launchers de golpe es la misma amplitud con el signo cambiado, y la
simetría (una sola función debadge, aplicada en las dos listas) cuesta menos que la
asimetría que ya existe hoy: 🔴 bloqueada al arrancar **y** al apagar, 🟡 bloqueada al
apagar y libre al arrancar. Y no cuesta nada al usuario que le importe: el 99 % de los
launchers se abren con un ejecutable, y para eso está la lista `apps`.

### P-2 — Cuando todo lo que el usuario marcó se omite, ¿qué ve?

Hoy ve `🚀 0 apps iniciadas` en **verde**. Tres formas, con su coste medible:

- **(a) El omite cuenta como `failed`.** Consecuencia medible: `continue` pasa a
  `failed += 1; continue` en las dos ramas, y el toast existente
  `⚠️ 'X': 0 iniciadas, 1 con error.` aparece sin tocar la firma. **Dos líneas de
  servicio, cero cambios en las dos vistas, cero cambios en los tres dobles de test.**
  El usuario ve ámbar y un número, pero no el **por qué**.
- **(b) Un tercer estado: `(started, failed, omitidas)`.** Consecuencia medible: cambia la
  firma de `start_pack_categories`, los dos llamantes (`pack_manager_view.py:667` y
  `dashboard_view.py:505`), los tres dobles de test y `ui/feedback.py`. El mensaje puede
  decir el motivo («🔴 es una categoría de riesgo» / «también está marcada para apagar»),
  que es lo que el dueño pidió al reportar «sin ningún aviso». Más caro, y es el único
  camino que **nombra el motivo** en pantalla.
- **(c) Dejar el verde.** Consecuencia: el producto sigue afirmando que hizo algo que no
  hizo. No se recomienda y se escribe para que conste.

**Recomendación del arquitecto: (a) como suelo, (b) como destino.** (a) es la mitad del
trabajo y ya mata el verde; (b) es la que responde de verdad al reporte. Si hay que elegir
una sola, (a) — y P-1(b) evita de paso el caso más común de omisión por conflicto, que es
el que el usuario puede provocar él mismo desde las dos tandas de casillas.

---

## 8. Fuera de alcance, con su razón

- **`TASK-069` y la ruta de datos.** Cerrada. `PROFILES_FILE` sale de `data_dir()` y el
  síntoma de «no veo packs» es el de favoritos, no el de este ciclo (§3.3).
- **La puerta de apagado y `execute_pack`.** No se toca. Su honestidad de recuento ya la
  vigila `run_tests.py:9864-9879` y la fijó TASK-063.
- **`.github/workflows/**`, `.releaserc.json`, `.commitlintrc.json`, `dist/`, `basura/`.**
  Sin relación.
- **`STATUS.md` fila 115.** Su texto es falso (§2) y hay que corregirlo, pero `STATUS.md`
  **no es de la ownership del arquitecto** (§ «Scope»): se entrega aquí el texto de
  reemplazo en `tasks.md` T-5 para que lo aplique quien lo posea. Una fila que afirma un
  bug inexistente es deuda viva, y dejarla es repetir el fallo que este ciclo viene a matar.
