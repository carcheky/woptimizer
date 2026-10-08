# Arnés de tests: `git` que hereda stdin en 37 llamadas, y 2 pre-vuelos que no comprueban nada

**Tarea:** TASK-072 · **Módulo:** `run_tests.py` · **Complejidad:** `low` (subida a `medium`, ver §6)
**Fecha:** 2026-10-08 · **Paso 2 del bucle `id-pipeline`** (planificación, cero ediciones bajo `src/`)

---

## 1. El encargo, y lo que de él se sostiene

La entrada de `tasks.json` afirma tres cosas. **Dos son medias y una es falsa.** Las tres se
auditan aquí contra el código y contra medición propia en este host, porque una premisa
falsa en un ticket de arnés se paga en el test que se escriba después.

### 1.1 SE SOSTIENE: el defecto de código existe y está donde dice

`run_tests.py:12745`:

```python
def _git_de_fixture(args, cwd):
    ...
    for _intento in (1, 2, 3):
        r = subprocess.run(
            ["git"] + args, cwd=cwd, env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=120,   # <-- sin stdin=
        )
```

Sin `stdin=`, el hijo hereda el descriptor 0 del arnés. El defecto es real, la ubicación es
la correcta, y el arreglo `stdin=subprocess.DEVNULL` es el más barato que lo mata.

**Medido — 37 llamadas** a `_git_de_fixture` en `run_tests.py` (no 40). El envoltorio es el
punto único: arreglarlo protege las 37, no una.

### 1.2 FALSA: «se queda bloqueado esperando entrada por consola indefinidamente» (en este host)

Medido el 2026-10-08 con fixture propia en `%TEMP%`, tres variantes de `stdin`:

| `stdin` del padre | `git cat-file --batch-check` | rc | ms | stdout |
|---|---|---|---|---|
| heredado (TTY, `isatty() == True`) | sin `stdin=` | **0** | **91,9** | `''` |
| `DEVNULL` | `stdin=DEVNULL` | 0 | 87,8 | `''` |
| pipe abierto, nunca escrito ni cerrado | sin `stdin=` | **TIMEOUT 15 s** | — | — |
| `DEVNULL` | `stdin=DEVNULL` | 0 | 174,0 (padre) | — |

**Conclusión medida:** el bloqueo depende de **qué hay en el descriptor heredado**, no de que
falte el argumento. Con TTY no hay bloqueo; con un pipe sin EOF, sí. En este host el arnés
corre hoy con TTY, luego **no se cuelga hoy aquí**. La premisa del ticket describe un
escenario (agente desatendido, `stdin` heredado como pipe abierto) que es **posible pero no
el actual**.

Esto **no invalida el arreglo**: `stdin=DEVNULL` convierte el caso "heredado" —sea TTY, sea
pipe, sea fichero— en "EOF inmediato", y con eso la variable desaparece. Un arreglo cuya
premisa está mal redactada puede seguir siendo el correcto; lo que no puede es entregarse
sin decir cuál era la premisa.

### 1.3 NO MEDIDA: la cola de descriptores al expirar el timeout

El ticket afirma que, expirados los 120 s, «el árbol de proceso hijo retiene los descriptores
de tubería abiertos, causando que el arnés se cuelgue sin reportar el final de la suite».
**No se ha reproducido y no se reproduce en este plan.** Se trata como no medida: no puede
sostener un criterio de aceptación, y afirmarla en el `notes` de la tarea es documentación
de una Medición inexistente. Se sustituye por el hecho medido de §4.

---

## 2. HALLAZGO NUEVO: los dos `pre-vuelo` son TAUTOLÓGICOS (esto es lo grave)

El encargo señalaba un call site, `run_tests.py:20303`. **Hay dos**, y ninguno comprueba
nada — ni antes ni después del arreglo de `stdin`:

```python
# run_tests.py:20186
assert HASH_MUERTO not in _git_de_fixture(
    ["cat-file", "--batch-check"], d_hist), "pre-vuelo: HASH_MUERTO existe"

# run_tests.py:20303
assert h not in _git_de_fixture(["cat-file", "--batch-check"], d_hist), (
    f"pre-vuelo: el hash muerto de la fixture {h} existe de verdad")
```

`git cat-file --batch-check` **lee los nombres por stdin**. `_git_de_fixture` no le pasa
`input=`. Sin entrada, git responde `rc=0` y **stdout vacío** —medido, §1.2, las dos filas de
la tabla. Por tanto `HASH_MUERTO not in ''` es `True` **siempre**, para cualquier hash,
 exista o no. Los dos asserts no pueden fallar.

Tres consecuencias, y la tercera es la que obliga a cambiar el plan:

1. **No son pre-vuelos: son decorativos.** Su función declarada (que el `mutation-auditor`
   y el lector dan por buena) es la de no dejar que una fixture vacía valide el check 9.
2. **El mensaje asserta lo contrario de lo que el código demuestra.** El texto dice
   «el hash muerto … existe de verdad», y la operación (`not in`) afirma que **no**
   aparece en la salida. El texto es el del caso positivo con el operador del negativo.
   Quien lo lea sin el código cree que hay una comprobación de existencia; no la hay.
3. **El criterio de aceptación nº 2 es IMPOSIBLE de satisfacer tal como está escrito**, y no
   por ser discriminante sino por ser falso: pide «el pre-vuelo de `cat-file --batch-check`
   en menos de 50 ms sin consumir timeouts». Medido, la invocación tarda **87,8–91,9 ms**
   *con el arreglo puesto*, en este host. Un criterio que exige 50 ms de algo que cuesta
   88 ms obliga a la implementación a hacer algo que no es el arreglo (o a mentir en el
   reloj). Se **reescribe** en §5.

---

## 3. La primitive correcta: `cat-file` hay dos usos distintos, y no son el mismo arreglo

El encargo, y con razon, advierte de no tratar los dos usos como uno. Se confirma que
son dos, con dos arreglos distintos:

| # | Llamada | Lee stdin | Arreglo |
|---|---|---|---|
| **A** | `validate_docs.py:523` (`_hashes_que_existen`, invocado en `run_tests.py:20522`) | **Sí, legítimamente**: `input="\n".join(pedidos) + "\n"`, ~100 hashes del journal real en una sola llamada | **NO SE TOCA.** Con `input=`, Python cierra el pipe tras escribir → EOF. Medido: devuelve una línea por hash (`<sha> commit 132` / `deadbee missing`). Es la primitive correcta para «¿existen estos N objetos?» y cambiarlo sería un desatino contra el docstring de `validate_docs.py:466` (un `cat-file -t` por hash serían ~100 subprocesos) |
| **B** | `run_tests.py:20186` y `:20303` | **No debería**: quiere la existencia de **un** hash, ya como argumento | Cambiar a `cat-file -e` (§4) |

## 4. Diseño

Dos arreglos **independientes y acumulativos**, porque son dos defectos distintos en las
mismas dos líneas. El segundo es el que hace que el primero valga algo.

### 4.1 `stdin=subprocess.DEVNULL` en el envoltorio — invariante de las 37 llamadas

Una línea, `run_tests.py:12756`. Convierte cualquier descriptor heredado en EOF inmediato.
Coste marginal cero, y es lo que hace segura la llamada aunque mañana alguien escriba un
`git` que lea stdin en cualquiera de las otras 36.

### 4.2 Un helper de existencia, con `cat-file -e`, que **no lee stdin**

`git cat-file -e <hash>` decide existencia por **argumento**. Medido:

| comando | rc | ms | stdout |
|---|---|---|---|
| `git cat-file -e <hash real>` | 0 | 104,4 | `''` |
| `git cat-file -e deadbee` | 128 | 96,8 | `fatal: Not a valid object name deadbee` |

El `rc` es la respuesta, y el comando **no abre stdin**, luego no depende de §4.1 para no
cuelgarse: esbelt-and-braces, que es exactamente lo que un pre-vuelo necesita.

**Trampa de implementación, y es la que decide el helper:** `_git_de_fixture` lanza
`AssertionError` tras 3 intentos si `returncode != 0`. Como `cat-file -e` responde **128**
para «no existe» —que es justo lo que el pre-vuelo quiere saber— **no puede usarse con
`_git_de_fixture` tal cual**: el helper tiene que distinguir «git falló» de «el objeto no
existe». Diseño, `_objeto_existe_en_fixture(hash_, cwd)` → `bool`:

- `rc == 0` → `True`.
- `rc == 128` → `False` (respuesta válida: el objeto no está).
- cualquier otro rc → reintento por `spawn EPERM`, y tras 3 intentos `AssertionError` con el
  `stderr` literal, en la misma clave que el envoltorio existente: *un fallo de git no se
  pierde como falso verde*.
- `timeout=120`, `stdin=DEVNULL`, y la misma purga de `GIT_DIR`/`GIT_WORK_TREE`.

Los dos call sites pasan a `assert not _objeto_existe_en_fixture(HASH_MUERTO, d_hist)`, con
el mensaje corregido al signo real («**no** existe»), y — esto es lo que mata la tautología —
se añade el **caso positivo**: el mismo helper sobre `HASH_REAL` tiene que devolver `True`.
Sin ese caso positivo el helper podría devolver `False` siempre y seguir verde.

### 4.3 Lo que NO se hace, con motivo

- **NO se baja el `timeout=120`.** Coste: `timeout` no causa el cuelgue, lo acota; con
  `stdin=DEVNULL` (§4.1) y `cat-file -e` (§4.2) desaparece la causa, y bajar el reloj solo
  añade falsos negativos en un host cuyo VFS de Nextcloud ya hace lentas las fixtures. Los
  ~90–105 ms medidos contra 120 s son tres órdenes de magnitud: el reloj no es el coste.
- **NO se toca `validate_docs.py:523`.** Uso legítimo de batch-stdin (§3, caso A).
- **NO se toca el pre-vuelo de `run_tests.py:20189`** (`git log --format=%h`): ese sí
  comprueba algo (`HASH_REAL in <salida>` con salida real) y no lee stdin.

---

## 5. Criterios de aceptación (reescritos; los originales no discriminan)

| # | Original | Veredicto | Reemplazado por |
|---|---|---|---|
| 1 | `stdin=DEVNULL` en `_git_de_fixture` | válido, tautológico como criterio (lee el código) | se conserva + **nuevo #4** |
| 2 | «pre-vuelo < 50 ms sin consumir timeouts» | **IMPOSIBLE**: medido 87,8–91,9 ms con el fix puesto | **#2'** (abajo) |
| 3 | suite completa desatendida hasta `ALL TESTS PASSED` | válido pero **no atribuible**: un rojo lo explicaría igual | se conserva como criterio de humo, **no** como prueba del fix |

- **AC-1.** `_git_de_fixture` pasa `stdin=subprocess.DEVNULL` a `subprocess.run`
  (`run_tests.py:12756`), y lo hace **en los tres intentos**, no solo en el primero.
- **AC-2'.** Test discriminante del bloqueo — ver §7.
- **AC-3.** `test_el_pre_vuelo_de_un_hash_muerto_distingue_existe_de_no_existe`: con la
  fixture real de `run_tests.py:20179`, exige **las dos** respuestas del helper:
  `_objeto_existe_en_fixture(HASH_REAL, d_hist) is True` y
  `_objeto_existe_en_fixture(HASH_MUERTO, d_hist) is False`. **Por qué discrimina:** con el
  código actual la salida de `cat-file --batch-check` sin `input=` es `''` para cualquier
  entrada, luego la afirmación «`HASH_REAL` está en la salida» es `False` y el assert
  revienta. Es la contraprueba que hoy no existe.
- **AC-4.** Guard estructural: `ast` sobre `run_tests.py` real exige **cero** llamadas a
  `git cat-file --batch-check` **sin** `input=` en el fichero. Mata la reaparición por
 yoste de la forma exacta, y documenta por qué el único `--batch-check` legítimo (el de
  `validate_docs.py`) no está aquí.
- **AC-5.** `validate_docs.py` sigue en **0 FAIL** y el reparto derivado **no cambia de
  par** al añadir los tests nuevos; los cuatro declarantes (`STATUS.md`, `AGENTS.md`,
  `README.md`, tabla de `docs/ai/testing-guide.md`) se actualizan **juntos** a la cifra que
  derive el check 7.
- **AC-6.** Cero ediciones bajo `src/woptimizer/**`. Ficheros de código tocados:
  `run_tests.py` y, solo si el reparto lo obliga, `validate_docs.py` (no debería).

---

## 6. Deuda conexa en `STATUS.md` (esta tarea la resuelve y la empeora)

- **`STATUS.md:101` — la fila 🔴 de TASK-072. Se cierra**, con su redacción original
  conservada y el verbo corregido: el defecto es la **herencia de stdin en las 37
  llamadas**, no «un cuelgue hoy». Añadir el hallazgo del tautológico en el mismo bloque:
  los dos `pre-vuelo` eran decorativos desde antes de este ciclo.
- **Deuda NUEVA que este cambio crea y hay que registrar:** al convertir dos decorativos en
  comprobaciones reales, el check 9 empieza a **depender de que la fixture tenga el commit**.
  Hoy `run_tests.py:20189` ya lo exigía, así que la dependencia **ya existía** y no es
  nueva — pero ahora hay **dos** comprobaciones donde había un decorativo, y si alguien
  vacía la fixture el fallo pasa a ser de git en vez de de aserción. Anotado en la fila para
  que no se lea como riesgo nuevo.
- **Deuda que este cambio NO toca y queda viva:** `TASK-075` (`validate_docs.py` anclado a
  `%LOCALAPPDATA%`, no corre en CI) y `TASK-074` (asimetría de códigos 2/3). El test de
  §7 tiene que vivir en `run_tests.py` **por TASK-075**, no en `validate_docs.py`: un guard
  que solo corre donde el problema duele es el modo de fallo del validador lento.
- **Comprobado, no supuesto:** el check 8 (`validate_docs.py:1720 _anclas_resolubles`) resuelve
  una cita `run_tests.py:12754` por **existencia del fichero** (S1) y, si trae identificador,
  por **contenido** (S2) — **el número de línea no se resuelve**. Añadir líneas en
  `run_tests.py` **no rompe** las anclas del panel. Aun así, `STATUS.md:101` se actualiza a
  mano porque su texto es lo que un humano lee.

---

## 7. El test discriminante (el punto que el encargo marca como fallido)

### 7.1 Por qué el criterio nº 2 no mide

Un assert de milisegundos sobre una invocación que **ya es rápida** no distingue el código
bueno del malo: con el bug puesto y sin él, la invocación baja en ambos casos, porque en
este host el caso «heredado» es una TTY y no bloquea (§1.2). Para que el mutante muera, el
test tiene que **construir el escenario que el bug no soporta**, no esperar al que el host
ofrece por casualidad.

### 7.2 `test_el_envoltorio_git_no_hereda_stdin_y_no_cuelga_en_desatendido`

**Construye un padre desatendido de verdad:** un hijo que hace una llamada de git **que lee
stdin**, lanzado con `stdin=` un **pipe abierto que el padre no escribe ni cierra** — que
es exactamente el modo de fallo medido, y no una aproximación.

```python
r, w = os.pipe()                     # pipe ABIERTO: EOF nunca llega
p = subprocess.Popen([sys.executable, hijo_py, cwd_repo],
                     stdin=r, stdout=PIPE, stderr=PIPE, text=True)
os.close(r)                          # el padre NO escribe en w y NO lo cierra
out, err = p.communicate(timeout=10) # <-- aqui muere el mutante
```

**Por qué discrimina, en una frase:** el mutante (quitar `stdin=DEVNULL`) hace que el
`git cat-file` del hijo herede ese pipe sin EOF, se bloquee leyendo, y `communicate(timeout=10)`
reviente con `TimeoutExpired` — **medido: TIMEOUT a 15 s sin el arreglo, rc=0 en 174 ms
con él** —, mientras que la suite sigue verde en el resto porque hoy el host le regala una
TTY y por eso no se cuelga nunca.

El hijo invoca el **envoltorio real** de `run_tests.py` (import o `exec` del fichero), no una
réplica: si el test copiara la llamada, mutar el envoltorio no lo tocaría y sería otro
decorativo.

**Variante de refuerzo, misma prueba, coste ~0:** el hijo ejecuta **dos** comandos, uno que
no lee stdin (`rev-parse`) y otro que sí (`cat-file --batch-check`), y el assert exige que
**ambos** voltan. Sin eso, un helper que se pasara `stdin` solo en un camino seguiría verde.

### 7.3 Los otros dos mutantes que tienen que morir

| Mutante | Por qué muere |
|---|---|
| **M1** quitar `stdin=DEVNULL` de `_git_de_fixture` | §7.2: `TimeoutExpired` |
| **M2** `cat-file -e` → volver a `cat-file --batch-check` sin `input=` | AC-3: `HASH_REAL` no aparece en la salida vacía → assert |
| **M3** helper que devuelve `False` siempre | AC-3: el caso positivo (`HASH_REAL is True`) |
| **M4** borrar el guard estructural (#4) | AC-4: el `ast` encuentra `--batch-check` sin `input=` |

M3 es el que justifica el caso positivo: sin él, «siempre `False`» y «siempre `True»» son
indistinguibles.

---

## 8. Ficheros

| Fichero | Acción | Quién |
|---|---|---|
| `run_tests.py` | `:12756` `stdin=DEVNULL`; nuevo `_objeto_existe_en_fixture`; `:20186` y `:20303` al helper + caso positivo; 3 tests nuevos | **Paso 3** |
| `.taskmaster/tasks.json` | `acceptance_criteria` y `notes` de TASK-072 | **este ciclo** |
| `openspec/changes/2026-10-08-arnes-hang-stdin-git/{proposal,tasks}.md` | este documento | **este ciclo** |
| `STATUS.md:101` | cerrar la fila 🔴 con el verbo corregido; anotar el tautológico | **Paso 3** |
| `AGENTS.md`, `README.md`, `docs/ai/testing-guide.md` | recuento, solo si el check 7 lo exige | **Paso 3** |

**Fuera de alcance, explícitamente:** `src/woptimizer/**` (cero ediciones), `validate_docs.py`
(su `--batch-check` es legítimo), `.github/workflows/**`, `dist/`.

---

## 9. Visto bueno

**Visto bueno CON CONDICIONES** para implementar. El arreglo `stdin=DEVNULL` es correcto y
barato, pero **no por el motivo que dice el ticket**: la premisa del cuelgue es falsa en
este host, y el criterio nº 2 es insatisfacible por medición (50 ms pedidos, 88 ms reales).
Sin las dos correcciones de §2 y §4.2, este ciclo entregaría un arreglo real accompanied de
un decorativo que sigue sin medir y de un criterio que obliga a mentir.