# Propuesta: `2026-09-30-ui-hardening` (TASK-027, FIX-003 / FIX-004 / FIX-006)

Auditado por `architect-review` contra el código real del ciclo #20. El encargo se
derivó de `openspec/changes/2026-09-29-bugfix-audit-v3/`, escrito hace dos días.
**Dos de sus tres premisas se han corregido y una es incompleta.** Todo lo de abajo
está medido sobre `src/`, no sobre la especificación heredada.

---

## 0. Resumen ejecutivo

| # | Premisa del encargo | Veredicto | Gravedad |
|---|---|---|---|
| FIX-003 | `start_pack_apps` usa `shell=True` | **CIERTO** y es un vector real de ejecución de comandos | **ALTA (seguridad)** |
| FIX-003 | «quitar `shell=True` y validar rutas absolutas» es el fix | **INSUFICIENTE**: `isabs` es la validación equivocada | **ALTA** |
| FIX-003 | `process_manager_view.py` debe guardar `exe_path` | **CIERTO**, y es la mitad del arreglo | MEDIA |
| FIX-004 | `process_manager_view.py` ordena con `sorted()` | **CIERTO**, y `sorted()` invierte el semáforo | MEDIA |
| FIX-004 | «orden semántico 🟢 → 🟡 → 🔴 → ⚪» | **FALSO**: contradice a `CATEGORY_ORDER` | — (criterio a reescribir) |
| FIX-004 | (no lo menciona) | **SEGUNDO SITIO** del mismo defecto en `pack_manager_view.py` | MEDIA |
| FIX-006 | `toggle_favorite` no permite desmarcar | **CIERTO**, pero **solo en la UI**: el servicio ya lo soporta y ya está testeado | BAJA-MEDIA |
| FIX-006 | `set_favorite(None)` hay que hacerlo pasar | **FALSO**: `set_favorite(None)` existe desde TASK-021 y hay test | — |

**Prioridad de aplicación: FIX-003 → FIX-004 → FIX-006.** FIX-003 es el único de los
tres que es una vulnerabilidad; los otros dos son de calidad percibida.

---

## 1. FIX-003 — el arranque de apps es un vector de ejecución de comandos

### 1.1 Lo que hay (verificado)

```python
# src/woptimizer/services/process_service.py:402-414
def start_pack_apps(self, apps: List[str]) -> Tuple[int, int]:
    import subprocess
    started, failed = 0, 0
    for app in apps:
        try:
            subprocess.Popen(app, shell=True)     # <-- :408
            started += 1
```

Entrada de `apps`: `pack_manager_view.py:322` y `dashboard_view.py:169` pasan
`pack.apps`, que viene de `profiles.json` —un fichero que edita el usuario a mano y
que este producto está pensado para compartir/sincronizar—. No hay ninguna
validación entre el disco y `Popen`.

### 1.2 Lo que el encargo no dice: hoy el contador `started` es una mentira

Medido en esta máquina:

```
Popen("no_such_app_xyz_127.exe", shell=True)  ->  returncode 1, NO lanza excepcion
```

`cmd.exe` responde «no se reconoce como un comando» con un código de salida, así que
`Popen` **no lanza**. El `except` de `:411` no se dispara nunca y `started` cuenta una
app que no arrancó. La notificación que ve el usuario
(`notify_apps_launched(pack.name, started, failed)`) miente en verde. **Cualquier
arreglo de seguridad que no arregle el contador deja esta mentira viva**, y por eso
el contador es un criterio de aceptación de primera clase, no un detalle.

### 1.3 El hallazgo de seguridad dominante: quitar `shell=True` NO basta

Son tres razones, y las tres están medidas:

1. **Un nombre desnudo se resuelve contra el directorio actual antes que el PATH.**
   Con `shell=False`, `CreateProcess` busca primero el CWD. Un `chrome.exe` soltado
   junto a `woptimizer.exe` se ejecutaría **en lugar del Chrome real**. Medido:
   `os.path.isfile("cmd")` → `False`, pero `shutil.which("cmd")` →
   `C:\WINDOWS\system32\cmd.EXE`. Un nombre desnudo nunca es una ruta.
2. **`os.startfile` reabre la puerta que `shell=False` cierra.** `os.startfile`
   delega en `ShellExecute`, que **sí** ejecuta `.bat`, `.cmd`, `.ps1` y `.vbs`
   pasando por su intérprete (`cmd.exe /c`). Cambiar `Popen(shell=True)` por
   `os.startfile` sin una lista blanca de extensiones es cambiar de hugging por
   ahorcamiento.
3. **`os.path.isabs` no es una validación de seguridad.** Medido:

   | entrada | `isabs` | ¿debería aceptarse? |
   |---|---|---|
   | `C:\Program Files\..\..\Windows\System32\cmd.exe` | **`True`** | **no** (traversal) |
   | `\\servidor\comparte\payload.exe` | **`True`** | **no** (ejecución remota) |

   Y el remate: `os.path.commonpath()` sobre la ruta **cruda** también pasa el
   filtro de contención. Medido:

   ```
   commonpath([cruda, 'C:\Program Files']) == 'C:\Program Files'   -> True   (FALSO POSITIVO)
   normpath(cruda) == 'C:\Windows\System32\cmd.exe'
   commonpath([normalizada, 'C:\Program Files'])                  -> False  (correcto)
   ```

   **La contención se comprueba SIEMPRE después de normalizar.** Si se hace antes,
   el traversal pasa las dos comprobaciones.

### 1.4 Lo que NO es el arreglo (antipatrones explícitos)

- **No se blacklistean caracteres.** `C:\Program Files\Rock & Roll\game.exe` es una
  ruta legítima. Un filtro de `& | ; > < ^` rechaza apps reales de Steam y de
  itch.io. La validación es **estructural** (ruta absoluta + normalizada + contenida
  + extensión + existencia), nunca de caracteres. Sin intérprete no hay metacaracteres
  que escapar.
- **No se resuelve con `shutil.which()`.** Eso es exactamente el punto 1.3.1: buscar
  en el PATH es buscar en el CWD.
- **No se reescribe `PackService`.** La decisión es de arranque, no de persistencia.

### 1.5 Decisión de diseño

**Una función de decisión pura y separada del efecto.** Firma obligatoria:

```python
# src/woptimizer/services/process_service.py
_ALLOWED_APP_EXTS = frozenset({".exe", ".com"})

def _resolver_app(self, entrada: str,
                  raices: Optional[Sequence[str]] = None) -> Optional[str]:
    """Devuelve la ruta ABSOLUTA validada, o None si no se puede arrancar.

    `raices` tiene valor por defecto para que el test pueda pasar un directorio
    temporal controlado. Nunca se consulta el PATH ni el CWD.
    """
```

Reglas, **en este orden** (el orden es la seguridad):

1. `entrada` no vacía tras `strip()`. Sin `\x00`.
2. **Rechazar UNC**: `entrada.startswith("\\\\")` o `startswith("//")`.
   `os.startfile` sobre un `\\host\share` es ejecución remota por SMB: el vector
   más valioso de los tres, y el que nadie audita.
3. Si no es absoluta: buscar el nombre desnudo **exclusivamente** dentro de las
   raíces permitidas, con `os.path.join(raiz, entrada)` + `isfile`. Si no aparece,
   `None`. (Cubre `apps=["chrome.exe"]` de fábrica —`pack_service.py:237`— sin
   tocar el PATH.)
4. `normalizada = os.path.normpath(entrada)` — **antes** de cualquier comparación.
5. Contención: `normalizada` debe estar dentro de al menos una raíz permitida
   (tras normalizar *la raíz también*). Se usa `os.path.commonpath` **o**
   `Path.is_relative_to`, siempre sobre la ruta normalizada.
6. Extensión en `_ALLOWED_APP_EXTS` (comparada en minúsculas, con punto).
7. `os.path.isfile(normalizada)`.

**Raíces permitidas** (si `raices is None`): `%ProgramFiles%`,
`%ProgramFiles(x86)%`, `%ProgramW6432%`, `%LOCALAPPDATA%`, `%APPDATA%`,
`%ProgramData%`; las que no existan en el entorno se descartan. Si la lista queda
vacía, se registra un `logger.warning` y **no se arranca nada** (fail-closed).

> Honestidad sobre el modelo de amenaza: esta lista de raíces **no es una
> sandbox**. `%APPDATA%` y `%LOCALAPPDATA%` son escribibles por el usuario, así que
> un atacante local con escritura en disco pasa por aquí. Lo que sí cierra esta
> lista es: *nada se ejecuta a través de un intérprete* (`.bat`/`.ps1`/`.vbs`/`.cmd`
  fuera), *nada se ejecuta desde una compartición remota* (UNC fuera), *nada se
  ejecuta por traversal* (contención post-normalización) y *no se puede colar un
  argumento* (no se pasa ninguno). Eso es hygiene con criterio, y es lo que este
> producto necesita; prometer más sería falso.

**El efecto, en un sitio aparte**, con la resolución del módulo **en tiempo de
llamada** (esto no es estilo, es lo que permite que la sonda muera por la aserción y
no por un `AttributeError`):

```python
def _lanzar(self, ruta: str) -> None:
    startfile = getattr(os, "startfile", None)
    if startfile is None:                     # fuera de Windows: fail-closed
        raise OSError("os.startfile no disponible en esta plataforma")
    startfile(ruta)                           # NUNCA `from os import startfile`
```

`start_pack_apps` recorre `apps`, llama a `_resolver_app`, y para cada resultado:

- `None` → `failed += 1` + `logger.warning` **con el motivo del rechazo** (el
  usuario tiene poder depurar por qué su app no arrancó).
- ruta → `try: _lanzar(ruta); started += 1` / `except OSError: failed += 1` + log.
  **El `started += 1` va DESPUÉS del `try`.**

Opción registrada y NO elegida: `subprocess.Popen([ruta], shell=False)` es más segura
por construcción (no hay `ShellExecute`, luego no hay `.bat`). Se elige `os.startfile`
porque es lo que pide el encargo y porque la lista blanca de extensiones ya cierra ese
hueco. Si un día se cambia, la lista blanca se vuelve innecesaria y el test 1.3
debe **volver a morir** para que nadie lo cambie en silencio.

### 1.6 El escritor: `on_add_to_pack` guarda el nombre, no la ruta

```python
# src/woptimizer/ui/views/process_manager_view.py:334-336
exe_name = procs[0].full_name if procs[0].full_name else procs[0].name
if exe_name not in target_pack.apps:
    target_pack.apps.append(exe_name)
```

`ProcessInfo.exe_path` existe (`models.py:8`) y se rellena
(`process_service.py:251`, `info['exe'] or ""`). **La premisa del encargo es
cierta y la ruta ya está disponible.** Regla: guardar `procs[0].exe_path` cuando no
esté vacía; si está vacía (AccessDenied), la degradación documentada es guardar
`full_name` y aceptar que el arranque lo rechazará con un log. Sin esa degradación
explícita, un proceso sin `exe` deja el pack inservible sin explicación.

---

## 2. FIX-004 — `sorted()` no es «alfabético», es **la inversión del semáforo**

### 2.1 Lo que hay (verificado)

```python
# src/woptimizer/ui/views/process_manager_view.py:176
for cat in sorted(categories.keys()):
```

Medido sobre `CATEGORY_ORDER` real (`config.py:97`):

```
CATEGORY_ORDER : 🟢Nav 🟢Sinc 🟡Chat 🟢Prod 🟡Media 🔴Over 🟡Launch 🔴Anti 🔴Sist ⚪Otros
sorted()       : ⚪Otros  🔴Anti  🔴Over  🔴Sist  🟡Chat  🟡Launch 🟡Media 🟢Nav 🟢Prod 🟢Sinc
primeros chars : 0x1f7e2 0x1f7e2 0x1f7e1 0x1f7e2 0x1f7e1 0x1f534 0x1f7e1 0x1f534 0x1f534 0x26aa
```

`sorted()` ordena por *code point*, y ⚪ (U+26AA) es del plano BMP mientras que 🟢🟡🔴
viven en el plano suplementario. Resultado medido: **«sin clasificar» sale PRIMERO y
los 🔴 «NO CERRAR» salen antes que los 🟢 «SEGURO»**. Es exactamente el orden
contrario al que el semáforo comunica, y el bloque rojo sube al primer golpe de vista.

### 2.2 Segundo sitio, no declarado en el encargo

```python
# src/woptimizer/ui/views/pack_manager_view.py:207
sorted_cats = sorted(list(all_cats))
```

Mismo defecto, en el acordeón de categorías del pack Gaming — el mismo widget que el
ciclo 15 marcó como sensible. Arreglar solo `process_manager_view.py` deja el
defecto vivo en el sitio donde el usuario **configura** qué se mata. Los dos sitios
se resuelven con la misma función.

### 2.3 El criterio de aceptación heredado es FALSO

> «Las secciones en el Gestor de Procesos siguen el orden semántico 🟢 → 🟡 → 🔴 → ⚪»

Eso **no** es `CATEGORY_ORDER` (medido arriba: `CATEGORY_ORDER` entrelaza 🟢Productividad
*después* de 🟡Chat, y pone 🔴Overlays en la 6ª posición y 🟡Launchers en la 7ª). La
descripción de la tarea dice una cosa y el criterio dice otra; **no se pueden cumplir
las dos**. La fuente de verdad es `CATEGORY_ORDER` (`config.py:97`, la que ya usa
`process_service.py:260`), así que **el criterio se reescribe**: el orden es
`CATEGORY_ORDER`, no «por color».

### 2.4 Decisión de diseño

Una sola función, en `config.py` (ya lo importan las vistas: `process_manager_view.py:8`),
para que los dos sitios no puedan divergir otra vez:

```python
def ordenar_categorias(cats) -> list:
    """CATEGORY_ORDER manda; las categorías desconocidas van AL FINAL,
    conservando su orden de entrada. Nunca `sorted()` sobre los emojis."""
```

- Índice de `CATEGORY_ORDER`; `key=idx.get(c, 999)` con **estable** (`sorted` es
  estable), de modo que el 999 solo ordena entre sí a las desconocidas.
- **No** se deriva de `get_safety_badge`: el orden no es un problema de semáforo, es
  un problema de presentación, y `get_safety_badge` es un secreto de otra frontera
  con sus propios tests.

---

## 3. FIX-006 — desmarcar favorito: el servicio ya lo hace, el que no lo hace es la UI

### 3.1 Lo que hay (verificado)

```python
# src/woptimizer/ui/views/pack_manager_view.py:213-215
def toggle_favorite(self, pack_id: str):
    self.pack_service.set_favorite(pack_id)     # siempre el id, nunca None
    self.refresh_packs()
```

`set_favorite` ya acepta `None` y lo implementa (`pack_service.py:652-656`: deja
`is_favorite = (k == pack_id)` en todos, luego `None` los desmarca todos) y
`test_pack_service_favorite_exclusive` **ya lo cubre** (`run_tests.py:820-821`:
`set_favorite(None)` → 0 favoritos). El criterio «`test_pack_service_favorite_exclusive()
sigue pasando sin modificaciones» es cierto hoy y lo seguirá siendo. **FIX-006 es
un bug de una línea en la UI, no un contrato de servicio que haya que cambiar.**
Severidad: baja-media.

### 3.2 Decisión de diseño: de dónde se lee el estado actual

`toggle_favorite` **no** puede usar el `pack` capturado en el render
(`pack_manager_view.py:82`, `lambda p=pack.id`) ni el glifo `⭐/☆` de `:80`: son
instantáneas de un render que puede quedar obsoletas (`reset_gaming_pack` devuelve un
`model_copy`, así que el objeto de la tarjeta anterior ya no es el de `self._data`).

**Elegido:** `self.pack_service.get_all_packs().get(pack_id)` y leer `.is_favorite`
en vivo. Es la misma llamada que hace `refresh_packs` (`:60`), no añade API nueva y
es **por pack**, así que es exacta aunque el fichero tenga dos favoritos.

**Descartado: `get_favorite_pack()`.** Devuelve el *primer* favorito
(`pack_service.py:628-632`). Con dos favoritos (alcanzable editando `profiles.json`
a mano, y el pack de fábrica + uno del usuario), pulsar la estrella del segundo
haría `set_favorite("b")` en vez de desmarcarlo: comportamiento invisible y
dependiente del orden del diccionario. Es un shortcut que no se puede testear bien.

Firma final:

```python
def toggle_favorite(self, pack_id: str):
    pack = self.pack_service.get_all_packs().get(pack_id)
    if pack is not None and pack.is_favorite:
        self.pack_service.set_favorite(None)    # segunda pulsacion = desmarcar
    else:
        self.pack_service.set_favorite(pack_id)
    self.refresh_packs()
```

Producto: desmarcar el pack Gaming deja la portada en su estado vacío
(`dashboard_view.py:100-103`), que es un callejón sin salida *desde la portada* pero
recuperable desde el Gestor de Packs, que es donde vive la estrella. Se acepta el
comportamiento simétrico; lo que **no** se acepta es que quede en silencio, así que
`refresh_packs()` se conserva y el glifo se repinta.

---

## 4. Correcciones obligatorias al encargo de TASK-027

1. El criterio «orden semántico 🟢 → 🟡 → 🔴 → ⚪» es incompatible con
   `CATEGORY_ORDER`. Se sustituye por «el orden es `CATEGORY_ORDER`» (§2.3).
2. Falta el **segundo sitio** de FIX-004 (`pack_manager_view.py:207`) (§2.2).
3. «Validar rutas absolutas» es insuficiente; `isabs` es la validación equivocada y
   hay que normalizar antes de comprobar contención (§1.3).
4. Falta el criterio del **contador honesto**: `shell=True` no lanza y hoy `started`
   cuenta apps que no arrancaron (§1.2).
5. Falta la **degradación** de `on_add_to_pack` cuando `exe_path` está vacía (§1.6).
6. FIX-006 no necesita tocar `PackService` ni sus tests (§3.1).

## 5. Fuera de alcance (deliberadamente)

- **TASK-029 (sistema de diseño).** El glifo de la estrella y los colores de la
  cabecera se van a tocar en otro ciclo; aquí no se mete un hex nuevo.
- **Migrar `apps` de los packs ya guardados** de nombre desnudo a ruta absoluta. Es
  una migración de datos del usuario, y el lector (§1.5, regla 3) ya resuelve el
  nombre desnudo dentro de las raíces: el comportamiento actual sobrevive sin tocar
  el disco.
- **`shell=True` en cualquier otro sitio.** No hay ninguno más en `src/` (verificado
  por grep), pero el test 1 lo deja escrito para el futuro.
