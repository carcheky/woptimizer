# TASK-074 · La paridad del par GIT va ANTES del veredicto del repo

> MEDIDO el 2026-10-18 con cámaras desechables en `%TEMP%`. El wrapper medido es el
> REAL por subproceso desde `REPO_ROOT`, y el mutante se midió sobre una **copia**
> con raíz propia en `%TEMP%`, nunca sobre el repo. Digest del wrapper real
> `1533b1521193` antes y después de las tres corridas: **CUADRA**.

## 1. Qué pedía la tarea, y qué hay de verdad

La tarea (`.taskmaster/tasks.json` → `TASK-074`) dice, en una frase: *falta una fila
en `test_la_puerta_de_paridad_va_despues_de_validar_repo` que exija código 2 en el
camino de commit con repo no verificable*. **Las tres partes de esa frase son
medibles, y las tres están mal:**

| Premisa del encargo | Medido | Veredicto |
|---|---|---|
| «con el mutante `R4-k` el código 2 no sale, degrada a `3`» | El código real de esa celda **es 2**. Lo que degrada a 3 es el mutante. | Confunde el mutante con el código. |
| «falta una fila en la sonda de posición» | `test_la_puerta_de_paridad_va_despues_de_validar_repo` (`run_tests.py:19987`) mide **`--verify`**, no el commit. Con `R4-k` puesto sigue dando 3 → **la fila no la mata: el mutante la sobrevive**. | El AC nombra una sonda que no puede ver la celda. |
| «DEUDA DE STATUS.md (fila 125)» | `STATUS.md` tiene 123 líneas y TASK-074 aparece en el **backlog** (`STATUS.md:35`), no en `## ⚠️ Deuda Técnica Conocida`. | Ancla obsoleta. |

**El hallazgo de fondo:** el AC es imposible de satisfacer tal como está escrito, y
por el motivo opuesto al que supone el encargo. La celda `commit + par asimétrico +
repo no verificable` **ya sale con 2 hoy**, sin tocar nada. Lo que sale con 3 es la
**otra** celda — la de `--verify` —, y esa es la que el documento promete en 2 y el
código no cumple.

## 2. La matriz medida

Ocho celdas: (commit | `--verify`) × (paridad rota | par entero) × (repo
verificable | no verificable). El modo no es un detalle: cambia el resultado.

### 2.1 Código real (`.taskmaster/git_safe_commit.py`, HEAD `303c520`)

| modo | paridad | repo | rc | línea canónica | ¿medida por alguna sonda? |
|---|---|---|---|---|---|
| commit | rota | verificable | `2` | `WOPT_USAGE paridad-git` | **nadie** |
| commit | rota | **no verificable** | `2` | `WOPT_USAGE paridad-git` | **nadie** ← la celda de la tarea |
| commit | entera | verificable | `0` | `WOPT_NOOP arbol limpio` | `test_el_cero_esta_sobrecargado...` |
| commit | entera | no verificable | `3` | `WOPT_REPO_INVALIDO GIT_DIR no existe...` | `test_git_safe_commit_fail_safe` |
| `--verify` | rota | verificable | `2` | `WOPT_USAGE paridad-git` | `..._tambien_cubre_el_modo_verify` |
| `--verify` | rota | **no verificable** | `3` | `WOPT_REPO_INVALIDO GIT_DIR no existe...` | `..._va_despues_de_validar_repo` ← **contradice el doc** |
| `--verify` | entera | verificable | `0` | `WOPT_REPO_OK <git_dir>` | `..._tambien_cubre_el_modo_verify` |
| `--verify` | entera | no verificable | `3` | `WOPT_REPO_INVALIDO ...` | `test_git_safe_commit_fail_safe` |

**Dos de las ocho celdas no las mide nadie:** las dos del camino de commit con par
asimétrico. Y la única celda donde `R4-k` es observable es una de esas dos.

### 2.2 Mutante `R4-k` (`if paridad_rota:` → `if paridad_rota and ok:`)

`git_safe_commit.py:880` es la única ocurrencia del texto: el mutante es aplicable.
MEDIDO sobre el código real, cambia **una sola celda de las ocho**:

| celda | sin mutante | con `R4-k` |
|---|---|---|
| commit + rota + no verificable | `2 WOPT_USAGE paridad-git` | **`3 WOPT_REPO_INVALIDO`** |

Las otras siete no se mueven. En `--verify` el mutante es **invisible**, porque el
bloque `if verify and not ok:` (`git_safe_commit.py:866-868`) sale antes que la
paridad: de ahí que la sonda de posición siga verde con el mutante puesto.

### 2.3 Opción (i) medida: la paridad entre `validar_repo` y `verify and not ok`

Reordenado sobre la copia de cámara, y con sus dos mutantes:

| celda | código real | reordenado | +`R4-k` | +`R4-n` (`and not verify`) |
|---|---|---|---|---|
| commit + rota + verificable | `2` | `2` | `2` | `2` |
| commit + rota + no verificable | `2` | `2` | **`3`** | `2` |
| commit + entera + verificable | `0` | `0` | `0` | `0` |
| commit + entera + no verificable | `3` | `3` | `3` | `3` |
| `--verify` + rota + verificable | `2` | `2` | `2` | **`0 WOPT_REPO_OK`** |
| `--verify` + rota + **no verificable** | **`3`** | **`2`** | **`3`** | `3` |
| `--verify` + entera + verificable | `0` | `0` | `0` | `0` |
| `--verify` + entera + no verificable | `3` | `3` | `3` | `3` |

**El reordenamiento cambia exactamente UNA celda de ocho.** Es el cambio de
comportamiento del wrapper que hay que journalizar, y es uno solo.

## 3. Decisión: es un problema de ORDEN y de DOCUMENTO, no de test que falte

**Se adopta la opción (i): el `2` de la paridad precede al `3` del repo, también en
`--verify`.** El orden vigente es un accidente topológico, no una política: `main()`
comprueba `not ok` **dos veces**, en `866` (apertura de `--verify`) y en `941`
(camino de commit), y la puerta de paridad (`:880`) ha caído entre las dos. El mismo
defecto da dos códigos según el modo.

Tres razones, y la primera es la que decide:

1. **Una precondición que se comprueba sin salir del proceso no puede ir detrás de
   una que necesita salir.** `paridad_rota` se calcula leyendo `os.environ`
   (`git_safe_commit.py:299`); no pregunta a git nada. D2 —la precedencia escrita en
   `main()`:862-865— justifica que el `3` gane al `2` porque *«si no el 3 describiría
   un problema del repo que en realidad nunca llegó a mirarse»*. Con par asimétrico,
   `validar_repo` **mira un par impuesto**, no el del llamante: `work_tree =
   env.get("GIT_WORK_TREE") or REPO_ROOT` (`git_safe_commit.py:459`). Es
   literalmente la situación que D2 dice que no debe ocurrir.
2. **El remedy es único y accionable.** Con media pareja hay dos arreglos posibles, y
   el primario es siempre «pon las dos variables»; el del repo puede no hacer falta.
3. **La alternativa se descarta por un fallo medido.** Dejar el `3` por delante
   obligaría a comprobar la paridad más tarde, y la alarma de ancla
   (`git_safe_commit.py:926`) depende de `GIT_WORK_TREE`: con par asimétrico podría
   disparar un `3` «el repositorio declara el árbol X y la invocación pretende Y»
   cuando la verdad es «no me diste el árbol». Diagnóstico falso, que es peor que el
   que se arregla.

### 3.1 Contrato de códigos de salida resultante

| Código | Cuándo | Línea canónica |
|---|---|---|
| `0` | commit real | `WOPT_COMMIT_OK <hash> <mensaje>` |
| `0` | nada que comitear (NOOP) | `WOPT_NOOP <motivo>` (sin hash) |
| `0` | `--verify` con par entero y repo sano | `WOPT_REPO_OK <git_dir>` |
| `1` | fallo de `git`: `status` / `add` / `diff` / `commit` / hash | `WOPT_FAIL <operacion> <detalle>` |
| `2` | uso incorrecto, **incluida media pareja** (`GIT_DIR` o `GIT_WORK_TREE` sueltas) | `WOPT_USAGE paridad-git <detalle>` |
| `3` | repo no verificable **con el par entero** | `WOPT_REPO_INVALIDO <detalle>` |

Precedencia, en orden, y todas medidas:

```
get_env()            -> paridad_rota           (0 salidas, sin git)
PUERTA DE PARIDAD    -> 2                      ANTES de todo lo demas, y antes del 3
validar_repo()       -> (solo lectura, no imprime)
--verify + not ok    -> 3
alarma de cwd        -> 2
alarma repo/arbol    -> 3
--verify             -> 0 WOPT_REPO_OK
commit: not ok       -> 3
NOOP                 -> 0 WOPT_NOOP
puerta del mensaje   -> 2
puerta de cabecera   -> 2
add / diff / commit / hash -> 1
commit ok            -> 0 WOPT_COMMIT_OK
```

### 3.2 Qué se rompe para quien hoy depende del `3`

**Una cosa, y se declara:** `--verify` con par asimétrico **y** repo no verificable
pasa de `3` a `2`. Quien lo herede ve «pon las dos variables» en lugar de «el repo no
es verificable», y es el mensaje correcto: el par es la causa primaria.

**Nada más se mueve**, y está medido en las ocho celdas: las cuatro invocaciones de
`test_git_safe_commit_fail_safe` usan `GIT_WORK_TREE = root` en todas
(`run_tests.py:1600`), luego el par nunca está roto ahí y sus `3, 3, 2, 0` quedan
intactos. `test_el_wrapper_no_versiona_desde_un_cwd_ajeno_ni_un_arbol_ajeno` también
va con par entero.

## 4. El patrón que hay que cerrar: la sonda de posición deja de mirar

`test_la_puerta_de_paridad_va_despues_de_validar_repo` **muere** con el reordenamiento
(su aserción `== 3`, `run_tests.py:20028`, pasa a `2`). Y al reescribirla aparece un
coste que hay que decir en voz alta, no tapar:

> **Tras el reordenamiento, `M5` —mover el bloque de paridad antes de `validar_repo`—
> pasa a ser un mutante EQUIVALENTE.** `validar_repo` (`git_safe_commit.py:441-486`)
> no imprime ni escribe nada, luego mover la puerta por encima de ella no cambia ni
> `stdout` ni el código de salida. Hoy `M5` es visible solo de rebote, porque la sonda
> medía en realidad la posición respecto al `if verify and not ok`, no respecto a
> `validar_repo`: su nombre y lo que mide no coinciden.

Por eso el paquete lleva **un test estructural (AST)**, no una aserción de
comportamiento: `test_la_puerta_de_paridad_va_despues_de_validar_repo_por_estructura`.
El idioma ya existe en el repo (`test_el_contrato_de_codigos_esta_atado_a_cada_linea_wopt`
y `test_toda_linea_wopt_de_main_esta_en_la_tabla_y_cierra_una_salida`).

Es la tercera vez que aparece el patrón «una comprobación sin contraprueba no es una
comprobación» (ciclos 60 y 62): por eso cada aserción nueva lleva su mutante y su
contraprueba, y ningún par se acepta sin las dos.

## 5. Sondas: qué mide cada una y qué mutante la mata

| Sonda | Celdas | Mutante que la mata | Contraprueba (qué mutante prueba que sigue mirando) |
|---|---|---|---|
| `test_la_paridad_gana_al_repo_invalido_en_los_dos_modos` (**nueva**) | commit+rota+roto → `2`; `--verify`+rota+roto → `2` | `R4-k` (`and ok`): las dos celdas caen a `3` | `R4-n` (`and not verify`): mata la columna de `--verify` (`0 WOPT_REPO_OK`). Si la sonda mirase una sola columna, uno de los dos sobreviviría. |
| ↳ controles dentro de la misma sonda | par **entero** + repo roto → `3` en ambos modos; y `"WOPT_USAGE paridad-git" not in stdout` | un `2` indiscriminado | Sin los controles, un wrapper que devolviera `2` siempre passaría el `2` de arriba. |
| `test_la_puerta_de_paridad_va_despues_de_validar_repo` (reescrita) | `--verify` + rota + roto → `2` | `R4-k` | control de par entero + repo roto → `3`, en la misma sonda |
| `..._por_estructura` (**nueva**, AST) | el `if paridad_rota:` está después del nodo que asigna `validar_repo(...)` | mover el bloque por encima | si el test dejara de encontrar el bloque, **falla**; no puede quedarse verde sin mirar |
| `test_la_puerta_de_paridad_tambien_cubre_el_modo_verify` (existente) | `--verify` + rota + sano → `2`; par entero → `0` | `R4-n` (ya lo mata) | ya tiene control negativo |
| `test_git_safe_commit_fail_safe` (existente) | `3, 3, 2, 0`, todo con par entero | — | no le afecta el cambio |

## 6. Documento: dos puntos que mienten, corregidos como parte de la tarea

`sandbox-rules.md` promete el `2` «también en `--verify»» (regla 7, líneas 83-85, y
la sección `--verify`, líneas 190-195) sin mencionar que el `3` del repo le ganaba.
Con el reordenamiento la promesa pasa a ser cierta, pero **hay que declararla**, y
en tres sitios:

1. **Fila del `2` en la tabla de códigos (línea 59):** que `WOPT_USAGE paridad-git`
   precede a `WOPT_REPO_INVALIDO`, incluso en `--verify`.
2. **Fila del `3` (línea 60):** que el repo no verificable sejudica «con el par entero».
3. **Sección `--verify` (190-195):** añadir la celda medida, con la fecha y el motivo.

> ⚠️ **No insertar filas nuevas en la tabla de códigos.** `validate_docs.py:1278` y
> `validate_docs.py:1773` citan `docs/ai/sandbox-rules.md:55-56` por número de línea
> para distinguir una fila que **TABULA** el contrato de una que lo **DECLARA**.
> Añadir filas desplaza esas dos líneas y deja las citas obsoletas. Ampliar el texto
> dentro de la fila existente, y correr `python validate_docs.py` al final.

## 7. Fuera de alcance, y por qué

- **No se toca `src/`.** `git_safe_commit.py` es tooling del bucle, no producción.
- **No se toca `AGENTS.md`:** el cambio no altera ninguna regla del bucle.
- **No se redefine la alarma de ancla** (TASK-072): solo se le hace caso al orden.
- **No se reescribe `WOPT_NOOP` ni su sobrecarga:** intactos, `0` solo en sus dos casos.