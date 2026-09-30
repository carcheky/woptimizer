# Tasks — Cerrar los huecos de alcance del ciclo 21 (TASK-028, iteración 3)

Diseño en [`proposal.md`](proposal.md). Criterio de cierre, el mismo de siempre: **cada fix lleva su
mutación medida, y la mutación tiene que morir por su aserción.**

## BLOQUE 1 — N7: el detector de "configurar el logging al importar"

- [x] **1.1** Escribir el **criterio** antes del código: configurar = adjuntar handler / fijar
      nivel o formato / reemplazar `handlers`; **obtener** el logger no configura (por qué
      `logger = logging.getLogger('woptimizer')` no se toca: es el punto de contrato de §15 y lo
      importan 4 módulos).
- [x] **1.2** `run_tests.py`: helper `_configuraciones_de_logging(codigo, nombre)` con (a) tabla de
      mutadores de logger, (b) tabla de funciones de configuración filtradas por cabecera `logging`,
      (c) los loggers nombrados a nivel de módulo recogidos de los `X = logging.getLogger(...)`,
      (d) separación `dentro` / `fuera` por `FunctionDef` / `ClassDef`.
- [x] **1.3** Reescribir N7 sobre el helper, conservando el control de que el detector encuentra
      algo dentro de `setup_logging`.
- [x] **1.4** Tabla **ILEGALES** (8 formas que tienen que marcarse) y tabla **LEGALES** (6 que no
      pueden marcarse): el detector se prueba contra sí mismo en las dos direcciones.
- [x] **1.5** **Medido** en `%TEMP%` (`_mutmatrix_t028_iter3.py`): **8 mutaciones de producto, 8
      muertas** por `assert not fuera`; **4 mutaciones de sonda** (P7a detector muerto → ROJA por el
      control `dentro`; P7b detector amplio → ROJA por la parte A; P7c parte A anulada + detector
      amplio → ROJA por `falso POSITIVO`; P7d parte A anulada + M16b → **VERDE, el mutante escapa**,
      que es lo que demuestra que la parte A lleva el veredicto).

## BLOQUE 2 — N1: la norma de archivar, sobre la ruta que la app lee

- [x] **2.1** **Comprobar antes de escribir el assert** si el fichero vivo real está o no en
      `_app_dir()`. **Medido: SÍ está** (`src/woptimizer/profiles.json`, 670 B, esquema v3, estado
      local, ignorado por git, no versionado). Por tanto la aserción literal del encargo
      (`not os.path.exists(...)`) **es imposible** y se sustituye.
- [x] **2.2** Afirmar primero que `PROFILES_FILE == _app_dir()/profiles.json` (para que la sonda no
      vigile una ruta que la constante ya no nombre).
- [x] **2.3** Comprobación **por contenido** de la ruta viva: si hay documento, no puede declarar
      `__system_gaming__` / `factory` / `kill_low_chat` en la raíz `profiles`. JSON ilegible → fallo
      con motivo (la app lo marcaría como dañado).
- [x] **2.4** **Medido**: **3 mutaciones de producto, 3 muertas** (copia byte a byte, copia
      **reformateada**, v2 que no es el archivado) + **P1a** (mirar `packs` en vez de `profiles`):
      **el mutante escapa** → la comprobación es portante.
- [x] **2.5** `docs/archive/legacy-root-data/README.md`: la ruta viva ya estaba dicha; añadir **por
      qué no se copia allí** (`load()` tiene rama legacy: se abriría de verdad).

## BLOQUE 3 — Documentar, no arreglar

- [x] **3.1 M10 (categoría): DEUDA ACEPTADA.** El escáner de versión no pilla un semver sin token de
      versión. Dictamen del auditor: aceptable; la consecuencia es desincronización de **empaquetado**,
      no seguridad ni datos. Escrito en `architecture.md` §15 y en `proposal.md` §3 para que el
      próximo que lo lea sepa que es una **decisión**. **No se arregla.**
- [x] **3.2** `architecture.md` §11: `Aquí se transcribe el rango medido, no elAuditado.` → el rango
      **medido** (`process_service.py:33-48`, con `ast`), **no el que venía en el encargo**.
- [x] **3.3** `docs/ai/testing-guide.md`: matriz medida de la iteración 3.
- [x] **3.4** `docs/ai/testing-guide.md`: **anotar** la trampa de `run_tests.py:8` (el `TextIOWrapper`
      sustituto cierra el `stdout` del host al liberarse; importar la suite desde otro proceso rompe
      la salida del host). **No se cambia el runner.**

## BLOQUE 4 — Cierre

- [x] **4.1** `python verify_ui_syntax.py` en verde.
- [x] **4.2** `python run_tests.py` en verde (**65 sondas**, 65 en verde; las dos modificadas siguen
      siendo las mismas, ahora con más cobertura: el recuento no sube porque **no hay sondas nuevas**,
      hay dos **más anchas**).
- [x] **4.3** `python validate_docs.py` en verde.
- [x] **4.4** `git status --porcelain` con **solo** los ficheros de esta iteración, `git ls-files
      docs/archive` con los **3** ficheros, y `git rev-parse --absolute-git-dir` apuntando al gitdir
      desacoplado (**nunca** al de una copia en `%TEMP%`).
- [x] **4.5** Commit por `python .taskmaster/git_safe_commit.py "test(task028): cerrar huecos de
      alcance del ciclo 21"`, comprobando el **código de salida** (0 = commit o no-op).

## Lo que esta iteración NO hace (a propósito)

- **No** reimplementa nada de la iteración 2: los 16 supervivientes del ciclo 21 están cerrados.
- **No** arregla M10 (§3): es una decisión, con su dictamen escrito.
- **No** cambia `run_tests.py:8` (§3.4): anotado, no tocado.
- **No** toca `src/`: los dos puntos son de medición, no de producto.
- **No** borra el `src/woptimizer/profiles.json` real: es estado local del propietario y lo
  regenera la app.
