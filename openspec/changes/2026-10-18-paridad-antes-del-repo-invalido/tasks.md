# TASK-074 · tareas

Contrato del cambio y matriz medida: `proposal.md`. Orden de ejecución **obligatorio**:
el código antes que el test, porque el test reescrito muere contra el orden viejo y no
hay forma de saber si muere por lo correcto.

## F0 · Antes de nada: congelar la matriz

- [ ] Copiar la tabla de 2.1–2.3 de `proposal.md` al informe final. Es la tercera
      lectura independiente (arquitecto 2026-10-18) y la que se compara con la del
      `mutation-auditor`.
- [ ] No mutar el wrapper real desde este cambio. El mutante se mide con copia en
      `%TEMP%` con raíz propia (así lo hizo la medición del arquitecto), o desde el
      Paso 4 con el protocolo de las 3 reglas de `sandbox-rules.md:264-274`.

## F1 · El reordenamiento (`.taskmaster/git_safe_commit.py`, `main()`)

- [ ] **F1.1** Mover el bloque `if verify and not ok:` (`866-868`) para que quede
      **después** del bloque `if paridad_rota:` (`880-882`). Los dos caben sin más
      cambios: `validar_repo()` ya corrió en `860` y `fallo_repo`/`ok` siguen vivos.
- [ ] **F1.2** Reescribir el comentario de `862-865`: la precedencia D2 **ya no** es
      «el 3 gana al 2» sin más, es «el 3 gana al 2 **cuando el par es entero**». Sin
      esto el código vuelve a mentir en el sentido inverso.
- [ ] **F1.3** Actualizar el comentario de la puerta de paridad (`:870-879`): el
      punto «después de `validar_repo`» sigue siendo cierto, y hay que **añadir** el
      nuevo: «también antes del `if verify and not ok`», con la celda medida.
- [ ] **F1.4** `python .taskmaster/git_safe_commit.py --verify` desde la raíz con el
      par por defecto → tiene que seguir dando `0 WOPT_REPO_OK`. Es el control de
      coste cero del camino bueno.

## F2 · Las sondas (`run_tests.py`)

- [ ] **F2.1** **NUEVA** `test_la_paridad_gana_al_repo_invalido_en_los_dos_modos`.
      Cuatro invocaciones, con `GIT_WORK_TREE` ausente en las de par roto:
      commit+roto → `2`; `--verify`+roto → `2`; commit+entero+roto → `3`;
      `--verify`+entero+roto → `3`. En las dos de par roto, `WOPT_USAGE paridad-git`
      tiene que ser la **última** línea y `WOPT_REPO_INVALIDO` **ausente**. En las dos
      de par entero, al revés. Cámara en `%TEMP%`, `git init` desechable, y
      `_head_del_repo_real()` intacto antes y después.
      **Por qué discrimina:** con `R4-k` (`and ok`) las dos celdas del par roto caen a
      `3` y el primer `assert` falla.
- [ ] **F2.2** **NUEVA** `test_la_puerta_de_paridad_va_despues_de_validar_repo_por_estructura`,
      con `ast` sobre `main()`: el `if` cuyo test es `paridad_rota` tiene que estar
      **después** del nodo que asigna `ok, fallo_repo, git_dir = validar_repo(env)`.
      Si el bloque no se encuentra, la sonda **falla** (no puede quedarse verde sin
      mirar: es la trampa de la que habla `STATUS.md:67`).
      **Por qué discrimina:** `M5` (mover la puerta por encima de `validar_repo`) deja
      la salida idéntica —`validar_repo` no imprime— y solo lo caza el orden del árbol.
- [ ] **F2.3** **REESCRIBIR** `test_la_puerta_de_paridad_va_despues_de_validar_repo`
      (`:19987`): la aserción `== 3` (`:20028`) pasa a `== 2`, y
      `"WOPT_USAGE paridad-git" not in stdout` (`:20037`) pasa a `"in stdout`. El
      nombre se queda; **el docstring hay que rehacerlo entero**, porque el actual
      afirma que el `3` gana al `2` y deja de ser cierto.
- [ ] **F2.4** Añadir las tres sondas al `main()` de `run_tests.py`, detrás del
      marcador headless (ninguna abre ventana), con el comentario de estilo del ciclo.
- [ ] **F2.5** Actualizar el reparto de la suite en los comentarios del marcador
      (205 → 208) y el reparto backend/headless que check 7 deriva con `ast`.

## F3 · El documento (`docs/ai/sandbox-rules.md`)

- [ ] **F3.1** Fila del `2` de la tabla (`:59`): `WOPT_USAGE paridad-git` precede a
      `WOPT_REPO_INVALIDO`, también en `--verify`. **Editar dentro de la fila; no
      insertar filas** (ver `proposal.md` §6: `validate_docs.py:1278` y `:1773` citan
      las líneas 55-56 por número).
- [ ] **F3.2** Fila del `3` (`:60`): «con el par entero», y por qué el par asimétrico
      se va antes.
- [ ] **F3.3** Sección `--verify` (`:190-195`): la celda medida, con fecha y motivo.
- [ ] **F3.4** Regla 7 (`:83-85`): la promesa del `2» deja de ser condicional; dejar
      constancia de que **antes** de este cambio no lo era, porque un lector futuro
      tiene que poder ver que el `3` ganaba por el bloque de `--verify`.
- [ ] **F3.5** `python validate_docs.py` en verde. Si se ha desplazado una cita de
      línea, actualizar la cita: el validador no avisa, solo deja de cuadrar.

## F4 · Cierre y auditoría

- [ ] **F4.1** `python run_tests.py` en verde, y anotar el recuento nuevo.
- [ ] **F4.2** `python verify_ui_syntax.py` sin cambios esperados.
- [ ] **F4.3** Journalizar en `.taskmaster/CHANGELOG.md` el cambio de comportamiento
      como tal: **una** celda de ocho (`--verify` + par roto + repo roto, `3` → `2`).
- [ ] **F4.4** `mutation-auditor`: medir **cuatro** mutantes y pegar los cuatro
      veredictos al informe:
      - `R4-k` (`and ok`) → debe morir en F2.1.
      - `R4-n` (`and not verify`) → debe morir (F2.1 y/o la sonda existente).
      - `M5'` (puerta por encima de `validar_repo`) → debe morir **solo** en F2.2.
      - `M5` histórico (puerta por encima de `verify and not ok`) → es el fix; no se
        mide como fallo.
- [ ] **F4.5** Cerrar TASK-074 en `.taskmaster/tasks.json` y subir el estado del
      wrapper en `STATUS.md` si el tablero lo lleva.

## Riesgos declarados

| Riesgo | Por qué | Mitigación |
|---|---|---|
| `validate_docs.py` se queda mudo tras desplazar la tabla | cita `sandbox-rules.md:55-56` por número de línea | F3.1 sin insertar filas + F3.5 |
| El implementador «arregla» F2.3 poniendo `2` sin tocar F1 | el test nuevo F2.1 falla en la celda de `--verify` | F2.1 cubre las dos columnas, no una |
| Alguien reintroduce `M5` creyendo que es inocuo | `validar_repo` no imprime, luego el fallo es invisible | F2.2 es la única que lo caza |
| Mutación mal medida que corrompe el repo real | precedente: `sandbox-rules.md:254-274` | copia antes de mutar, digest antes y después, `finally` no es garantía |