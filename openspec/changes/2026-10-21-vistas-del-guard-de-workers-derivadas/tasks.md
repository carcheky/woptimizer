# Tareas — TASK-082 · el conjunto de vistas del guard de workers se deriva

**Ciclo 68** · rama `beta` · **cero ediciones bajo `src/woptimizer/`**.
Contrato completo en `proposal.md` (§7 = criterios de aceptación).

---

## Orden de ejecución

| # | Tarea | Fichero | Estado |
|---|---|---|---|
| 1 | Hoist de `_vistas_del_disco` a ámbito de módulo, con el directorio **derivado** de la ubicación del módulo | `run_tests.py` | ☐ |
| 2 | `VISTAS_INVENTARIADAS` deja de ser la fuente: el guard abre el **derivado** y la literal queda como **declaración comparada** | `run_tests.py` | ☐ |
| 3 | `_arbol_de` deja de llevar el directorio de vistas escrito a mano | `run_tests.py` | ☐ |
| 4 | `RUTAS_VIGILADAS` se queda solo con `confirmation.py` (las 3 entradas de vista son redundantes: el default del `.get()` ya las aporta) y `ESPERADOS` deja de ser una tercera copia | `run_tests.py` | ☐ |
| 5 | Guard de forma (AC-1): una sola fuente de verdad; el helper **no** puede estar anidado | `run_tests.py` | ☐ |
| 6 | Test de producto (AC-2): vista nueva en `%TEMP%` → ROJO nombrando la infracción; control positivo → VERDE | `run_tests.py` | ☐ |
| 7 | Contraprueba del detector (AC-3): el derivado es el disco y abre ≥1 fichero; derivado vacío → ROJO | `run_tests.py` | ☐ |
| 8 | Cierre (AC-4): suite verde, `verify_ui_syntax.py` verde, `validate_docs.py` 0 FAIL, `git status --porcelain` vacío, commit `(TASK-082)` en `beta` | repo | ☐ |
| 9 | Recuento de citas por número de línea movidas, en el informe de mutación | `mutation-report.md` | ☐ |

> El conjunto de vistas está escrito **cuatro veces**: `VISTAS` (`:27617`), las claves de
> `RUTAS_VIGILADAS` (`:27622`), `ESPERADOS` (`:27631`) y `VISTAS_INVENTARIADAS` (`:9410`, en
> el **otro** guard). **Solo una** de las cuatro está atada al disco.

---

## Detalle de cada una

### 1 · Hoist de la derivación

`_vistas_del_disco` vive **anidada** en `test_ninguna_vista_programa_after_a_mano`
(`run_tests.py:27652`), con sangría de 4 espacios. **Por eso no se puede reutilizar** y el
segundo guard escribe el conjunto a mano.

- Subirla a **ámbito de módulo**, con docstring propio.
- El directorio de vistas sale de la **ubicación del módulo** (`Path(__file__)`), no de
  `os.path.join(raiz_repo, "src", "woptimizer", "ui", "views")` escrito a mano (que hoy
  aparece duplicado en `run_tests.py:9311` y `:27676`).
- `__init__.py` fuera, **a propósito**: no es una vista (misma regla que hoy).

### 2 · La literal pasa a ser declaración

En `test_los_workers_de_pack_solo_publican_por_after` (`run_tests.py:9410`):

- `vistas_en_disco = _vistas_del_disco(...)` → **derivado**.
- `assert set(VISTAS_INVENTARIADAS) == vistas_en_disco` → **rojo que nombra la
  diferencia** (una vista nueva, o una vista que se ha ido).
- el `for` abre **`vistas_en_disco`**, no la literal.
- La cifra `== 10` (`:9416`) **se queda**: es un tripwire deliberado, no un alcance.

> ⚠️ **No** sustituir la literal por el derivado y ya: eso perdería el aviso. Se quiere
> **el rojo que nombra** la vista nueva **Y** que la vista nueva se audite.

### 3 · `_arbol_de`

Hoy abre `os.path.join(raiz_repo, "src", "woptimizer", "ui", "views", nombre)`
(`run_tests.py:9311`). Que reciba la ruta ya resuelta por el caller derivado.

### 4 · AC-1 · guard de forma

Con `ast`, sobre `run_tests.py`:

- el conjunto que el guard de workers abre **no puede** ser una enumeración literal
  escrita dentro del propio guard;
- el helper que lo deriva **no puede** estar anidado dentro de una función (si lo está, es
  inaccesible para el otro guard y la copia a mano vuelve);
- una sola fuente de verdad para el conjunto de vistas.

Cada hallazgo se nombra con **fichero y línea**. **SIN lista muda de permitidos**: si hace
falta tolerar algo, va en el docstring del infractor con (a) por qué existe y (b) qué la
retira — la misma regla que AC-5 de TASK-081.

### 5 · AC-2 · producto

En `%TEMP%`: `src/woptimizer/` real + una vista **nueva** cuyo worker toca la vista fuera
de la puerta + la lista de vistas actualizada (como haría el dev) → **ROJO** nombrando la
infracción. **Control positivo**: la misma vista sin tocar la puerta → **VERDE**.

Es el AC que no puede sobrevivir sin el fix. Sin el control positivo, un guard que siempre
da ROJO cumpliría el AC.

### 6 · AC-3 · contraprueba del detector

1. El derivado devuelve **exactamente** los `.py` de `src/woptimizer/ui/views/` menos
   `__init__.py`, y **eso** es lo que el guard abre. Un derivado **vacío** → ROJO.
2. El conjunto abierto y el derivado **coinciden** con la declaración.

### 7 · AC-4 · cierre

```powershell
python run_tests.py            # ALL TESTS PASSED.  exit 0
python verify_ui_syntax.py    # exit 0, ALCANCE_DERIVADO=22
python validate_docs.py       # 0 FAIL
python .taskmaster/git_safe_commit.py "fix(tools): el conjunto de vistas del guard de workers se deriva (TASK-082)"
```

Rama `beta`. **Nunca `main`.** `git status --porcelain` vacío antes de comitear.

### 8 · Recuento de citas movidas

Las citas de `run_tests.py` que usa la propuesta (`:9410`, `:27617`, `:27652`, `:27683`,
`:27715`) **se mueven** al insertar líneas por encima. Medir y **actualizar** las que
sigan vivas, o sustituirlas por derivación. Es el residuo `P2` de `STATUS.md`.

---

## Mutantes declarados

| id | Qué rompe | Veredicto esperado |
|---|---|---|
| **M-V1** | la literal vuelve a ser la fuente | **MUERTO** (AC-1 y AC-2) |
| **M-V2** | vista nueva en disco, literal sin actualizar | **EQUIVALENTE** — rojo por construcción (ruido). Su supervivencia **no** es un fallo |
| **M-V3** | la derivación devuelve una lista vacía o fija | **MUERTO** (AC-3). Si nadie lo mata, el guard vuelve a ser vaciable |
| **M-V4** | el helper no se hoista y la copia a mano vuelve | **MUERTO** (AC-1) |

---

## Fuera de alcance (y por qué)

* `src/woptimizer/**` — invariante del repo.
* El alcance de AC-5 (`run_tests.py:28993`) — **#2** del ranking, agujero **latente**: su
  propio ciclo.
* `_copiar_el_esqueleto_del_validador` (`run_tests.py:13209`) — MEDIDO: todas las celdas
  dan ROJO con fichero y línea → bomba de mantenimiento, no agujero.
* Ampliar la llave del detector AC-5 a basenames — MEDIDO (E3): AC-1 y AC-3 **ya** cazan
  esa forma → es ruido.
* `TASK-080` y `TASK-068` — bloqueadas, no se tocan.
* `STATUS.md` — lo cierra el orquestador: está citado por número de línea en **9 sitios de
  código vivo** y ~19 más en changelogs y journal.
