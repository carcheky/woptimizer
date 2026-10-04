# Desbloquear el pipeline: el rojo de `commits` no lo causan los 8 commits que se culpa

**Change-id:** `2026-10-04-desbloquear-pipeline-commitlint`
**Tarea que lo abre:** `TASK-064` (sigue `in_progress`) · **Tarea que lo hace resistente:** `TASK-066` (nueva)
**NO toca:** `.github/workflows/**`, `.releaserc.json`, `.commitlintrc.json`, la proteccion de `main`,
ni `src/woptimizer/**` (cero). Todo lo de aqui es plan; el Paso 3 es de `openspec-dev`.

---

## 1. El sintoma, medido

La corrida [37228601320](https://github.com/carcheky/woptimizer/actions/runs/37228601320) fallo en el
job `Commits convencionales`; `verify`, `release` y `build` quedaron `skipped`. No se publico release
y no se compilo ningun `.exe`. `main` no se mergea mientras tanto.

## 2. Las MEDICIONES que reencuadran el problema

Todo lo de esta seccion se reprodujo con las seis reglas de nivel 2 de `.commitlintrc.json:4-27`
sobre el rango real de cada push. La sonda es reproducible y no depende de la red.

### 2.1 El rango del push que fallo: 8 de 29 (confirma el diagnostico heredado)

`41b8061..4d86908` -> 8 de 29 incumplen. Siete por `header-max-length` (125, 138, 127, 188, 142, 212,
134) y dos cabeceras mas que ademas incumplen `subject-case` (`92368ad` y `c3ced1a`, que empiezan en
mayuscula). Coincide con la tabla de `docs/GITHUB-SETUP-CHECKLIST.md` seccion D-4.

### 2.2 El hallazgo que cambia el plan: los 8 ya NO bloquean nada

`release.yml:49-61` resuelve el rango como `github.event.before..HEAD`. Para el proximo push a `beta`,
`before` es **la punta actual de `beta`**, que ya contiene los 8. Medido:

```
origin/beta   = 4d86908   (los 8 ya estan publicados aqui)
origin/main   = ad9159f
main (local)  = f3d9f6f   33 commits por delante de origin/main, 7 por delante de origin/beta
```

El rango del siguiente push a `beta` es `4d86908..<nuevo>`, y **`4d86908` cae por fuera**: los 8
quedan *abuelos del rango*, no dentro. No hace falta reescribir historia publicada para que el job
pase, y no hace falta relajar ninguna regla para que dejen de mirarse.

> **Por que importa mas de lo que parece.** El guard NO se relaja: sigue teniendo el mismo poder sobre
> todo commit **futuro**. Lo que cambia es el perimetro, y lo cambia el propio resolutor de rango que
> ya esta escrito en el `.yml`. Los 8 pasan a ser historia ya publicada y por tanto inalterable sin
> force-push, el mismo estatus que hoy tienen los commits anteriores a la regla — que es
> exactamente la razon por la que `commitlint.yml:3-7` no lintea el historial entero.

### 2.3 El bloqueante real son OTROS 2 commits, y son locales

```
4d86908..main  ->  7 commits, 2 incumplen
  ef67bf8  fix(tooling): cerrar los seis huecos sin guardian de la puerta de versionado y corregir
           dos afirmaciones documentales (TASK-061)              -> 128 chars
  82f52c2  chore(tooling): dejar de versionar el log de la corrida de la suite, que es un artefacto
           de la sonda y no un fuente del repo (TASK-061)         -> 135 chars
```

Y la medicion que los hace baratos de arreglar:

```
git branch -r --contains ef67bf8   ->  NINGUNA rama remota
git branch -r --contains 82f52c2   ->  NINGUNA rama remota
```

**Ninguno esta publicado.** No hay nada que reescribir en remoto, no hace falta `--force` a ninguna
rama, y la proteccion blanda de `main` no se toca. Son dos cabeceras de dos commits del turno anterior.

### 2.4 Consecuencia: la premisa "un commit corrector no arregla un commitlint rojo" es FALSA tal como esta escrita

`docs/GITHUB-SETUP-CHECKLIST.md` D-4(c) afirma que los commits correctores no funcionan "porque los
8 siguen dentro del rango". Es verdad **para ese push**, que ya esta muerto, y falso para el
siguiente: un push nuevo a `beta` tiene `before = 4d86908`, los 8 quedan fuera, y lo unico que se
mide son los commits nuevos. El que dispara el rojo de verdad no es un commit ya publicado que no se
puede quitar, sino **un commit local que se puede reescribir gratis**. El diagnostico apuntaba al
commit mas caro de arreglar cuando el barato estaba sin mirar.

### 2.5 La premisa "el bucle comitea a `main` porque lo dicen sus ficheros" tambien es FALSA

Medido sobre los dos ficheros que el encargo señalaba:

```
grep -i 'beta|branch|rama|push'  .agents/skills/id-pipeline/SKILL.md        -> 0 coincidencias
grep -i 'beta|branch|rama|push'  .agents/agents/openspec-dev/agent.md    -> 0 coincidencias
```

Lo unico que sale es `mainAgent: false` y `main_window.py`. **Ninguno de los dos ficheros dice que se
comitee a `main`, porque ninguno dice nada de ramas.** Y `git_safe_commit.py` tampoco: cero
coincidencias de `branch`/`rama`/`rev-parse --abbrev-ref`. El bucle no eligio `main`; **nunca se
cambio de rama y la unica puerta de versionado es ciega a la rama.** El worktree esta en `main`
(medido) y por ahi van 52 ciclos.

Corolario para el plan: **no hay ninguna instruccion que corregir, hay una instruccion que
escribir.** Y no basta con escribirla en un sitio, porque la puerta que el bucle usa de verdad no la
lee.

## 3. Decision de diseno

**Opcion elegida: (a') — reescribir SOLO los 2 commits no publicados, mover `beta` con
fast-forward y dejar que el pipeline corra sin reescribir historia publicada ni relajar ninguna
regla. Ademas: la mitad estructural, que es la que evita que el rojo vuelva, va en
`TASK-066` y es parte de este plan, no su consecuencia.**

Formalmente, (a') es (a) reducida a lo que (a) todavia puede costear, mas lo que (d) pretendia
conseguir sin pagar su precio:

1. **Reescribir 2 cabeceras, no 29.** Solo lo no publicado. `git branch -f` / `reset --hard` +
   `cherry-pick --no-commit` + `commit` con el mensaje corto. Los otros 5 commits del rango
   conservan autor y fecha; los 3 que quedan despues cambian de SHA por necesidad de cadena, y eso
   no cuesta nada porque no estan en ningun remoto.
2. **`beta` avanza con fast-forward**, no con `--force`. Se cumple la condicion de O-1: el tramo
   pendiente sale como **pre-release** y la estable se gradu sola al mergear.
3. **La puerta del mensaje se instala en el embudo**, no en el `.yml`. Un commit de 135 caracteres
   no debe poder existir: el dia que pueda volver a existir, el dia vuelve el rojo.
4. **El bucle trabaja en `beta`, que es la rama que la documentacion ya declara de integracion**
   (`docs/ai/release-pipeline.md:22-43`, `docs/GITHUB-SETUP-CHECKLIST.md` seccion 0). No se crea
   ninguna rama nueva.

### 3.1 Por que esta y no las otras

| Opcion | Veredicto | Motivo medido |
|---|---|---|
| (a) Rebasear los 29 y `--force` a `beta` | **Descartada** | Reescribe historia ya publicada para_gain cosmetics: 8 cabeceras que semantic-release **parsea bien** (el limite de 120 es de commitlint, el parser de `conventionalcommits` no lo aplica) y que ya no volveran a entrar en ningun rango (§2.2). Exige `--force` a `beta` y reescribe lo que un force-push ya rompio una vez en este repo: `release.yml:43-48` documenta el `fatal: Invalid revision range` que dejo el pipeline ROJO PARA SIEMPRE. Paga un riesgo real por un beneficio de ancho de linea. |
| (b) Subir `header-max-length` a 220 | **Descartada** | Anula la unica regla que detecta un mensaje mal formado antes de que semantic-release lo ignore en silencio (`release.yml:63-65`, `release-pipeline.md:51`). Relajar el guard para que pase lo que escribio el guard es como un guard deja de guardar. Y el bucle volveria a pasarse en dos ciclos, porque la causa es la longitud que compone, no el limite. |
| (c) Commits de correccion | **Descartada, pero por el motivo equivocado** | La razon escrita en D-4(c) es falsa (§2.4): un push nuevo a `beta` excluye los 8. No se descarta porque no funcione, sino porque **no arregla nada**: el rojo lo causan 2 commits que hay que reescribir igual, y `ci(...)` no publica nada (`release-pipeline.md:18`). Es un no-op disfrazado de correccion. |
| (d) Rama nueva (`develop`) | **Descartada en su forma literal** | `release.yml:8-11` y `commitlint.yml:9-13` solo disparan en `main`, `beta` y el patron de mantenimiento. **Un push a `develop` no corre NADA**: ni commitlint, ni `verify` en Windows, ni release, ni `.exe`. El bucle pasaria N ciclos sin una sola señal de CI, y un rojo que desaparece no es lo mismo que un bug que deja de existir — es el peor modo de fallo posible aqui, porque entrena a no mirar. Ademas anadir la rama a `.releaserc.json:3-10` es cambio de producto para algo que `beta` ya cubre. |
| **(d') `beta` como rama de trabajo** — **la variante buena de (d)** | **ELEGIDA, junto a (a')** | Consigue todo lo que (d) buscaba (el bucle deja de escribir en la rama de publicacion) con lo que (d) temia perder (CI y release siguen corriendo) y sin tocar `.releaserc.json` ni el `.yml`: `beta` ya es la rama de integracion declarada. Efecto colateral que es la mitad del beneficio: como el bucle empuja incrementalmente a `beta` en vez de acumular 33 commits en `main`, **el rango de commitlint de cada push es de 2 a 5 commits**, y un mensaje malo se caza con un rango de uno, que se arregla con un `amend` y no con un rebase de 29. |
| **(a')** | **ELEGIDA** | §3. Verificado que los 2 commits que reencuadran el problema son locales y que los 8 del diagnostico ya estan fuera de todo rango futuro. |

### 3.2 La asimetria deliberada entre las dos puertas del wrapper

`git_safe_commit.py` va a acquire **dos**-branchmas cosas, y **no con el mismo peso**. Es una decision,
no un descuido:

- **La puerta del mensaje es un rechazo duro** (`WOPT_USAGE cabecera-larga`, codigo **2**), en el mismo
  sitio y con la misma forma que la puerta de ancla de TASK-059 (`git_safe_commit.py:460-469`, entre
  `validar_repo` y `add -A`, que es justo donde va: de solo lectura y antes de la primera escritura).
  Se puede porque una cabecera de 135 caracteres **no tiene un caso legitimo**: no hay "pero es que
  este mensaje si es largo", y el que la escribe puede arreglarla en el mismo turno.
- **La rama es un aviso, no un rechazo.** Y el motivo es evidencia ya pagada por este repo:
  `STATUS.md:95(b)` establece que una puerta que solo existe en el wrapper no puede cerrar un
  `commit` escrito a mano. Un rechazo duro sobre `main` solo guardaria el camino guardado —el wrapper—
  y **bloquearia el commit legitimo del dueno en la rama de release**, que es el caso para el que
  `main` existe. El defecto que se cierra aqui es "el bucle no sabe que deberia estar en `beta`", y
  un defecto de instruccion se cierra con instruccion **y con un test que lee la instruccion**, no
  con un `sys.exit` que dejaria al bucle sin salida documentada. El coste —un `git commit` a mano en
  `main` no lo caza nadie— queda **declarado**, no escondido.

## 4. Algoritmo (T-1 a T-5, en `tasks.md`)

Resumen del camino, con lo que hay que medir en cada paso:

1. **T-1** Reescribir las 2 cabeceras de `ef67bf8` y `82f52c2` a <= 120, con autor y fecha intactos.
   Se hace con `git reset --hard` al ancestro comun + `cherry-pick --no-commit` + `commit`, porque
   `git rebase -i` **no esta soportado en este entorno** y porque los dos commits son consecutivos
   (posiciones 4 y 5 de 7 contando desde `beta`), lo que hace la via no interactiva barata.
   Cierre: la sonda dice **0 de 7** y el arbol queda limpio.
2. **T-2** `git push origin main:beta` (fast-forward, **sin `--force`**). Cierre: la corrida sale
   verde en los cuatro jobs, aparece `v1.1.0-beta.N` y lleva `woptimizer.exe` adjunto.
3. **T-3** Graduar a `main` con `git push origin main:main` (fast-forward). Cierre: `v1.1.0` estable
   con `.exe`. **Esto cierra la ultima casilla abierta de TASK-064.**
4. **T-4** Puerta de cabecera en `git_safe_commit.py`. Cierre: tests que discriminan (§5).
5. **T-5** Contrato de rama: worktree en `beta` y la regla escrita donde el bucle la lee. Cierre: el
   test que exige la regla en los tres ficheros, mas la mitad negativa.

## 5. Tests que DISCRIMINAN (y por que fallan sin el fix)

| Test | Por que falla sin el fix |
|---|---|
| **La puerta rechaza la cabecera de 135 chars** — fixture con el texto real de `82f52c2`, invocado como subproceso con `GIT_DIR` a una temporal | Hoy `git_safe_commit.py` **no tiene ninguna comprobacion de longitud**: acepta el mensaje, commitea, imprime `WOPT_COMMIT_OK` y sale con **0**. El test exige codigo **2** + `WOPT_USAGE cabecera-larga` + **cero commits creados**, y las tres cosas son falsas a la vez. Un mutante que baje el limite a 200 pasa el grep y muere en la asercion. |
| **La puerta rechaza antes de stagear** — tras el rechazo, `git diff --cached --quiet` sigue en 0 y `git status --porcelain` no ha cambiado | Sin el fix no hay rechazo, asi que el commit existe; si alguien pone la puerta **despues** de `add -A` (el sitio donde se cuela el error, y el error que ya se cometio con la puerta de ancla), el indice queda modificado y este test lo ve. Es el mismo criterio que ya fijo `tasks.md` de `2026-10-04-marcador-ciclo-y-hashes-journal` para la puerta de ancla. |
| **CONTRAPRUEBA: las 5 plantillas literales de `SKILL.md` pasan** | Mata el fix demasiado fuerte. Una puerta que rechaza el vocabulario del bucle lo atasca en su primer commit, y eso no se ve en ningun test que solo mire la regla: hace falta el corpus de plantillas. |
| **La puerta rechaza `subject-case` con longitud valida** — `chore(architect): T-9 afirma el invariante ...` (96 chars, empieza en mayuscula) | Mata al mutante "solo compruebo la longitud", que es el que un implementador razonable escribe primero. Sin la mitad de `subject-case` ese commit se cuela. El primer caracter es lo que mira `upper-case` de commitlint, no toda la cadena: `92368ad` y `c3ced1a` incumplen por eso y por eso hay que copiar el criterio, no inventarlo. |
| **LA MISMA REGLA QUE EN CI — el clasificador compartido, congelado sobre el corpus real** — las 8 cabeceras largas reales (con su SHA citado en la fixture) se rechazan; 5 cabeceras limpias reales se aceptan | Es el que ata el host al runner. Sin el fix **el clasificador no existe**, y con un limite escrito a mano en el wrapper el test pasa mientras el `.yml` sigue diciendo otra cosa. Congelar el corpus, no derivarlo de `git log`: la historia se mueve y el test debe seguir signifcando lo mismo dentro de tres ciclos. |
| **La regla de rama esta en los tres ficheros, y ninguna plantilla dice `main`** — se extraen del repo igual que el test de las 5 plantillas ya hace | Hoy los tres ficheros tienen **cero** ocurrencias de rama (§2.5), asi que la mitad positiva falla. La mitad negativa es la que importa: mata al mutante "escribe la palabra beta en algun sitio", porque exige una prohibicion explicita que nombre `main`. Sin ella el test pasa con un comment nuevo que no cambia el comportamiento. |
| **El wrapper declara la rama en la que escribe** — `INFO rama: <branch>` en la salida canonica | Sin el fix no sale nada: la rama es una pregunta que hoy el bucle no puede ni hacerse. Este es el que convierte el aviso de §3.2 en algo diagnosticable, y es la precondicion legible del anterior. |

**Mutantes que el `mutation-auditor` tiene que cerrar, por nombre:** `LIMITE_SUBIDO_A_220` (mata la
contraprueba de las plantillas y la del corpus), `PUERTA_TRAS_ADD` (mata el test de "rechaza antes de
stagear"), `SOLO_LONGITUD` (mata el de `subject-case`), `REGLA_EN_UN_COMENTARIO` (mata la mitad
negativa del test de rama), `SIN_INFO_RAMA` (mata el de la rama declarada).

## 6. Lo que este plan NO arregla, escrito para que no se lea como arreglado

- **Los 8 commits de 2.1 se quedan en la historia de `beta`, para siempre.** Su mensaje aparecera largo
  en las notas de `v1.1.0-beta.N`, porque semantic-release los parsea bien y los imprime enteros
  (§3.1). Es cosmetico y es el precio de no reescribir lo publicado.
- **`beta` no esta protegida.** El rojo se evita en el origen (§2.2, T-4), pero nada impide que un
  `--force` a `beta` destruya la referencia de `before` otra vez. Anadirle proteccion blanda a `beta`
  es un cambio de producto y queda fuera; se anota como candidata.
- **La rama es un aviso, no un rechazo** (§3.2). Un `git commit` a mano en `main` no lo caza nadie, y
  es la misma clase de punto ciego que `STATUS.md:95(b)`.
- **El trabajo de 33 commits sale en un unico version estable.** `v1.1.0` absorbera `feat` y `fix` de
  33 commits a la vez, porque semantic-release calcula **un** version por corrida tomando el tipo mas
  alto. Es lo que O-1 acepto al elegir pasar por `beta` primero, y es exactamente lo que el paso 5
  (empujar incrementalmente a `beta` por ciclo) va a impedir que se repita.
