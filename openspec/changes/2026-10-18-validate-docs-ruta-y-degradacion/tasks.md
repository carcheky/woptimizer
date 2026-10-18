# tasks.md — TASK-075

Contrato de implementacion. Cada `T-n` nombra el mutante que tiene que morir; un `T-n` sin
mutante nombrado es una capacidad, no una comprobacion.

## T-1 · Una sola funcion de resolucion del repositorio

Extraer **UNA** funcion que resuelva el repositorio con la precedencia de `proposal.md` §7.1
(`--git-dir` > `WOPTIMIZER_GIT_DIR` > `GIT_DIR` > `%LOCALAPPDATA%`) y que la usen **los dos**
consumidores hoy duplicados: `validate_docs.py:306-308` y `:481-483`.

> Por que la extraccion es el cambio y no un detalle: el encargo nombra la linea 300-302, que
> no existe. La derivacion esta en DOS sitios con codigo identico, y un `--git-dir` aplicado a
> uno solo deja el check 5b leyendo un repo y el check 9 otro.

**Mata:** mutante que implementa `--git-dir` en `_comprobar_ancla_de_commits` y no en
`_hashes_que_existen`. Sin el flag, el check 9 sigue con el default, R2 acusa los hashes que
ese repo no tiene y el validador da FAIL con el flag puesto. Verificado hoy: **154 FAIL**
(escenario B de `proposal.md` §2).

## T-2 · `main()` admite `--git-dir` y `--sin-ancla-de-git`

`main()` hoy deriva `root` de `__file__` y **no admite argv** (`validate_docs.py:2546`). Parsear
con `argparse`. Sin flags, el comportamiento es **identico** a hoy, byte a byte.

**Mata:** mutante que pasa los flags pero no los propaga a `validar()`. El producto seguiria
aceptando `--git-dir` y usaria el default: un test que solo comprueba que el flag se acepta
pasa sin medir nada.

## T-3 · `--git-dir` explicito que no es repo = FALLA, con la ruta literal

Criterio: `rev-parse --verify HEAD` con el repositorio del flag. **NO** `os.path.exists()`:
medido que un directorio vacio responde `128` y un repo sin commits responde `0`
(`validate_docs.py:490-494`), y `exists()` no los distingue.

Mismo criterio que `git_safe_commit.validar_repo`, y por el mismo motivo: que los dos
componentes no puedan discrepar sobre que es un repo.

**Mata:** `motivo = None` o `except: return set()` — el error desaparece y el validador sale
`0 FAIL`. Es el falso verde que `proposal.md` §7.3 cierra.

## T-4 · `[SKIP]` para lo saltado, `[OK]` para lo comprobado

`--sin-ancla-de-git` salta los checks que necesitan git. Lo saltado se imprime como `[SKIP]`
**nunca** como `[OK]`, y el informe acaba con el recuento de saltados.

**Mata:** mutante que imprime `[SKIP]` con el formato de `[OK]`, o que reusa el `ok.append` de
la rama "SIN COMPROBAR" que ya existe (`validate_docs.py:650-656`, `:613-618`) para el caso
saltado a proposito. Sin ese muro, `--sin-ancla-de-git` da un verde indistinguible del verde
real, que es el peor desenlace posible de este cambio.

**Medido hoy:** con repo ausente el validador da `145 OK, 1 FAIL` y exit 1. El
`ok.append("SIN COMPROBAR...")` de hoy **no** es un `[SKIP]`: es una linea de `ok` dentro de un
informe que en ese caso sale con 1 FAIL. Con `--sin-ancla-de-git` ya no habra ese FAIL, y ahi
si hace falta el muro.

## T-5 · Decir de que repositorio se leyo

Cuando `GIT_DIR` llegue suelto (sin `GIT_WORK_TREE`), el validador **no falla** —cambiarlo a
fallo tumbaria el bucle— pero lo **nombra en `ok`**, con la ruta literal.

**Mata:** mutante que borra la linea de `ok`. El veredicto no cambia, y por eso es el unico
criterio de este bloque que necesita su propia asercion sobre la CADENA del informe.

## T-6 · Los AC de `tasks.json`, uno a uno, con contraprueba

Los siete AC discriminantes estan en `.taskmaster/tasks.json` (AC-1..AC-7 de TASK-075). Cada
uno nombra su mutante. Ninguno se acepta sin que el `mutation-auditor` lo rompa y lo vea morir.

## T-7 · Documentacion que hoy miente (parte del cambio, no commentary)

1. `release.yml:89-93`: el motivo real **no** es `%LOCALAPPDATA%`. Es que **25 de los 150
   hashes de `rd_journal.json` no son alcanzables desde `origin/main`+`origin/beta`**
   (`proposal.md` §3.A3), luego `fetch-depth: 0` solo daria 25 FAIL de R2. Reescribir el
   comentario con el numero medido y la fecha.
2. `sandbox-rules.md`: anadir **al final del fichero** la seccion que `STATUS.md:81` dice que ya
   existe y no existe. **Prohibido insertar filas o lineas por encima de la linea 61**:
   `validate_docs.py:1277-1278` y `:1772` citan `sandbox-rules.md:55-56` **por numero de linea**.
3. `STATUS.md:81`: la fila dice "DEUDA DE STATUS.md (fila 121)" en el encargo y la fila real es
   la **81**. Corregir la remision cuando esta se escriba alli.

## T-8 · Cierre

- `python run_tests.py` verde, **con el recuento actualizado en los 4 sitios**: `STATUS.md`,
  `AGENTS.md`, `README.md` y la tabla de `docs/ai/testing-guide.md` (`validate_docs.py:121-125`
  y `:154`). El validador **falla en rojo** si uno de los cuatro no cuadra.
- `python validate_docs.py` verde.
- Commit por el wrapper, mensaje con identificador, rama `beta`.

---

## Lo que NO entra aqui

- **TASK-080**: meter el validador en el job `verify`. Bloqueada por los 25 hashes sin pushear.
  Ver `proposal.md` §6.
- `CAUSAS_DE_PERDIDA` (`validate_docs.py:401`) no se toca. Los 25 hashes sin pushear **no estan
  perdidos**; declararlos perdidos seria escribir en el registro la mentira que el ancla
  existe para certificar.
- `git_safe_commit.py` no se toca. Su puerta de paridad (`get_env()`, `:298-302`) es la de **su**
  contrato (`0/1/2/3`), y meter un `2` en `validate_docs.py` romperia un contrato normativo que
  `AGENTS.md` declara. La divergencia se documenta, no se unifica ahi.