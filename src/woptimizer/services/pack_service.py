import contextlib
import json
import os
import shutil
from typing import Dict, List, Optional
from pydantic import ValidationError
from woptimizer.models import AppData, Pack
from woptimizer.config import PROFILES_FILE, logger

BACKUP_SUFFIX = ".bak"


class PerfilCorruptoError(ValueError):
    """TASK-030: el profiles.json tiene una FORMA que el servicio no sabe leer.

    No es un bug del codigo: es dato roto. Es la UNICA via por la que una
    `AttributeError` de la rama legacy se convierte en algo clasificable, y se
    valida la FORMA en `_read_json` ANTES de desreferenciar, en vez de ampliar
    `CORRUPTION_ERRORS` con `AttributeError`: ese es un SINTOMA, y tragarselo
    convertiria cualquier bug interno de una linea (un `None` mal desreferenciado,
    un `.get` sobre algo que cambio) en "el archivo esta roto" -> recuperacion
    desde el .bak -> y en el siguiente `save()` los packs que el usuario acaba
    de crear desaparecen. Un `AttributeError` NO deliberado debe PROPAGAR tal
    cual, para que el bug se vea en el log en vez de perder la configuracion.

    Proposito de `ValueError` como base: la rama legacy ya era un `ValueError` de
    facto (`.items()` sobre algo que no es un mapa), asi que no cambia el tipo que
    ve quien llama; lo que cambia es que el mensaje diga el TIPO REAL en vez de un
    `AttributeError` generico.
    """


# TASK-026 (FIX-009): errores que SI son "el archivo esta roto" y pueden, por
# tanto, intentar recuperarse desde el .bak. `OSError` (permisos, EIO, archivo
# bloqueado por el antivirus) queda FUERA a proposito: no es corrupcion y no
# debe entrar en la ruta que regenera y sobrescribe los packs del usuario.
# TASK-030: `PerfilCorruptoError` (forma legacy invalida) entra; `AttributeError`
# NO, por el motivo de su docstring. La clase se define ANTES que la tupla
# porque la tupla la referencia al construir el modulo.
CORRUPTION_ERRORS = (json.JSONDecodeError, ValidationError, TypeError,
                     UnicodeDecodeError, PerfilCorruptoError)

def _hoja_ilegible(pack_id: str, error: ValidationError) -> PerfilCorruptoError:
    """Traduce el `ValidationError` de Pydantic a UN mensaje que sirva delante
    del bloc de notas (proposal.md 3, condicion 1).

    Sin esto, quien abre el fichero lee "1 validation error for Pack / keepers /
    Input should be a valid list [type=list_type, input_value='steam.exe',
    input_type=str] / For further information visit https://errors.pydantic.dev/
    2.13/...": el CAMPO esta, pero el PACK se pierde entre lineas, el tipo real
    se esconde en la notacion de Pydantic y la URL lleva a una documentacion
    que el usuario no ha pedido. El mensaje nombra **campo**, **pack** y
    **tipo real**, que es lo unico accionable sin ser programador.
    """
    problemas = []
    for err in error.errors():
        campo = ".".join(str(parte) for parte in err.get("loc", ())) or "?"
        # `errors()` NO trae `input_type` (solo lo usa el renderer de Pydantic),
        # asi que el "tipo real" se saca del propio valor recibido.
        tipo = type(err.get("input")).__name__
        problemas.append(f"el campo {campo!r} es {tipo} ({err.get('input')!r})")
    return PerfilCorruptoError(
        f"el pack {pack_id!r} no se puede leer: " + "; ".join(problemas) +
        ". Una hoja mal formada es CORRUPTION (se recupera del .bak), no un pack "
        "con un campo raro: 'keepers' es la lista de procesos PROTEGIDOS del "
        "Gaming Mode y normalizarla a [] desarmaria la proteccion sin avisar."
    )


# --- TASK-031 iteracion 2: IDENTIDAD y ERROR DE ESCRITURA ---------------------
# REPARTO DE COMPETENCIAS, que es lo que evita volver a la lista de `isinstance`
# campo a campo que `proposal.md` 2(a) rechazo (y que ya fallo dos veces):
#
#   * el MODELO es dueno de los TIPOS y de los ENUMERADOS (E-2: la rama legacy
#     deja de saltarse el modelo, y aqui los booleanos son `strict`);
#   * el SERVICIO es dueno de la IDENTIDAD (la clave del mapa ES el id del pack) y
#     de la POLITICA de campos desconocidos (hacia delante vs error de escritura).
#
# Son DOS reglas y no una lista de campos: parten de `Pack.model_fields`, asi que
# en cuanto `Pack` gane un campo las cubren las dos sin que nadie se acuerde.
CLAVES_DE_PACK = frozenset(Pack.model_fields)


def _normalizar_clave(clave: str) -> str:
    """Minusculas, sin espacios sobrantes y con `-` en `_`.

    TASK-031 iteracion 3 (M13): NO es cosmetica. Sin ella la colision se decide
    solo con Levenshtein a distancia 1, y una variante de GRAFIA que necesita
    mas de una pulsacion se colaria sin clasificar: `IS-FAVORITE` esta a **11** de
    distancia de `is_favorite` en bruto y a **0** normalizada (misma intencion,
    otra grafia); `IS_GAMING` a 2 y a 0. La coincidencia EXACTA se resuelve antes
    que la distancia, y ese atajo es el que la sonda L9 ejerce con esas dos
    filas. La mutacion "esta funcion es la identidad" no sobrevive: sin ella,
    esas dos filas dejan de clasificarse.
    """
    return clave.strip().lower().replace("-", "_")


def _distancia_de_ediccion(a: str, b: str) -> int:
    """Levenshtein clasico. Las claves son cortas (<= 20) y la lista conocida son 8, asi
    que no hace falta ni matriz optimizada ni corte temprano."""
    fila = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        nueva = [i]
        for j, cb in enumerate(b, 1):
            nueva.append(min(fila[j] + 1, nueva[j - 1] + 1,
                             fila[j - 1] + (ca != cb)))
        fila = nueva
    return fila[-1]


def _colision_de_tecla(campo: str) -> Optional[str]:
    """La clave CONOCIDA que `campo` parece querer escribir a UNA pulsacion de
    diferencia, o None si no se parece a ninguna.

    POR QUE UN CAMPO PARECIDO ES CORRUPCION Y UNO CUALQUIERA NO (la politica que
    `proposal.md` 3.2 dejo sin cerrar, y que el mutation-auditor de la iteracion 2
    demonstro con `keeper`): un `keeper` es un campo del USUARIO, no una
    ampliacion del formato. Aceptarlo en silencio deja `keepers` en su valor por
    defecto `[]` y DESARMA el anti-brick: el Gaming Mode deja de proteger lo que
    el usuario escribio a mano para que lo protegiera. Es el mismo ladrillo que
    `proposal.md` 3 decidio evitar con una hoja mal formada, aqui con una hoja
    bien formada y mal NOMBRADA. La recuperacion desde el `.bak` es el camino
    barato: el fichero se queda en disco, el aviso nombra el campo y el usuario
    corrige una palabra.

    Y POR QUE NO ES UN "FUZZY" que rechace campos legitimos: la lista es CERRADA
    (`CLAVES_DE_PACK`, la de los campos que esta version conoce) y el umbral es
    UNA pulsacion (distancia de edicion 1 sobre el nombre entero). Medido en la
    sonda L9 con los 10 campos extra plausibles que ella usa (`notas`, `note`,
    `color`, `tags`, `hotkey`, `version`, `keep`, `orden`, `emoji`,
    `description`): ninguno colisiona, y el mas cercano es `note` a distancia 2
    de `name`. Un umbral de 2 ya rechazaria `note`, y la sonda incluye esa lista
    justamente para que nadie pueda subirlo.

    CORRECCION DE LA AFIRMACION "CERO FALSOS POSITIVOS" (TASK-031 iteracion 3,
    P5): era FALSA, y la midio el `mutation-auditor` de la iteracion 2. Cero
    falsos positivos es lo que pasa con esos 10 campos, NO lo que garantiza el
    filtro: `names` esta a distancia **1** de `name` e `ids` a distancia **1**
    de `id`. Por eso esta funcion se aplica SOLO a las HOJAS (vease
    `_vigilar_hojas`): en una hoja, un `names` al lado de un `name` es un error
    de escritura de verdad; en la RAIZ, una clave que se parezca a un campo de
    hoja no es un error de escritura de hoja, y clasificarla seria perdida de
    datos del usuario. Sonda: `L12`.
    """
    objetivo = _normalizar_clave(campo)
    for clave in CLAVES_DE_PACK:
        # Variante de la clave de verdad (`" keepers"`, `"is-favorite"`,
        # `"IS-FAVORITE"`): misma intencion, otra grafia. Tambien es un error de
        # escritura, y ESTE camino es el unico que la coge cuando hacen falta mas
        # de una pulsacion (ver `_normalizar_clave`).
        if _normalizar_clave(clave) == objetivo:
            return clave
    distancia, clave = min((_distancia_de_ediccion(objetivo, _normalizar_clave(c)),
                            c) for c in CLAVES_DE_PACK)
    return clave if distancia == 1 else None


def _vigilar_hojas(mapa_packs, rama: str) -> None:
    """TASK-031 iteracion 2: IDENTIDAD y ERROR DE ESCRITURA, en las DOS ramas.

    NO valida tipos: de eso se encarga el modelo (E-2). Esto solo decide DOS
    cosas, y las dos son CORRUPCION silenciosa en el estado anterior:

    1. **La clave del mapa es el id del pack.** Medido con el codigo anterior: un
       `{"packs": {"mi-clave": {"id": "otro-id", ...}}}` se cargaba sin clasificar,
       `get_user_packs()` no lo enseñaba, y `pack_manager_view.py:100`, que
       indexa `get_all_packs()[pack.id]`, reventaba con `KeyError('otro-id')` en el
       desplegable de accion por defecto. Un pack que la app no puede ni abrir ni
       borrar. Se clasifica en vez de normalizar a la clave, porque normalizar
       reescribiria en silencio un campo que el usuario escribio.
    2. **Un campo que parece un error de escritura de uno conocido es
       corrupcion** (`_colision_de_tecla`). El mensaje nombra el campo, el pack y
       la clave que queda sin leer, porque quien repara el fichero es el usuario.

    LO QUE ESTA GUARDA NO APLICA, Y POR QUE (TASK-031 iteracion 3, M8/M9). Esta
    funcion recibe el MAPA DE PACKS, nunca el objeto entero, y las dos reglas son
    afirmaciones sobre las HOJAS. No hay una variante "para la raiz", y no es una
    omision: aplicarlas ahi seria perdida de datos, medido en tres pasos.

      * La **identidad** no tiene sentido en la raiz: no hay ningun `id` al que
        la raiz pueda ser distinta. La regla dice "la clave del mapa de packs es
        el id del pack", y la raiz no es un mapa de packs.
      * El **error de escritura** en la raiz esta PROHIBIDO por medicion, no por
        prudencia: clasificar una raiz mal escrita (`{"packs2": ...}`,
        `{"profiless": ...}`) hace que, en la ruta sin `.bak`, `load()` haga
        `self._data = AppData()` y el siguiente `save()` publique
        `{"packs": {"gaming": ...}}`. Los packs del usuario se pierden IGUAL que
        sin clasificar, y con un aviso de encima (sonda `L8`, mutacion `L-M8a`).
        En una hoja, aceptar un `keeper` deja `keepers` en `[]`; en la raiz,
        aceptar un `packs2` deja el fichero entero en manos de otro build.
      * Y ademas **falso positivo**: `names` esta a distancia 1 de `name` e
        `ids` a distancia 1 de `id`. Una clave raiz que se parece a un campo de
        hoja no es un error de escritura de hoja: es un dato raiz legitimo de un
        build que esta version no conoce, y clasificarlo lo BORRA (misma ruta
        que el punto anterior). La hoja si es el sitio donde esa parecido
        significa algo: alla `name` y `names` conviviendo en el mismo registro
        es un error de escritura de verdad.

    Sonda: `L12` (una clave raiz NUNCA se declara error de escritura, y sobrevive
    al guardado).
    """
    if not isinstance(mapa_packs, dict):
        return   # que lo diga el modelo: la forma la valida el, no esta regla
    for clave, hoja in mapa_packs.items():
        if not isinstance(hoja, dict):
            continue
        ident = hoja.get("id")
        if isinstance(ident, str) and ident != clave:
            raise PerfilCorruptoError(
                f"el pack {clave!r} esta guardado bajo la clave {clave!r} pero su "
                f"campo 'id' dice {ident!r}. La clave del fichero es su identidad "
                f"(la app la usa para encontrarlo), asi que con las dos distintas "
                f"el pack no se puede abrir ni borrar. Pon 'id' igual que la "
                f"clave, o cambia la clave por {ident!r}."
            )
        for campo in hoja:
            if campo in CLAVES_DE_PACK:
                continue
            choque = _colision_de_tecla(campo)
            if choque is not None:
                raise PerfilCorruptoError(
                    f"el pack {clave!r} (rama {rama}) tiene el campo {campo!r}, "
                    f"que parece un error de escritura de {choque!r}. Aceptarlo en "
                    f"silencio dejaria {choque!r} con su valor por defecto: si es "
                    f"'keepers', el Gaming Mode deja de proteger NADA. Corrige el "
                    f"nombre o borra la linea."
                )


DEFAULT_GAMING_PACK = Pack(
    id="gaming",
    name="🚀 Preparar para Gaming",
    is_favorite=True,
    is_gaming=True,
    default_action="kill",
    apps=["chrome.exe"],
    keepers=["steam.exe", "discord.exe"],
    target_categories=["🟢 Sincronización", "🟢 Navegadores", "🟢 Productividad", "🟡 Chat y Comunicación", "🟡 Launchers Gaming"]
)

class PackService:
    def __init__(self, data_path: str = PROFILES_FILE):
        self.data_path = data_path
        self._data = AppData()
        # TASK-031 (T-10.2): el estado de "el fichero del usuario no se pudo
        # leer" es OBSERVABLE, no un `logger.warning` invisible (Trampa #14:
        # "nada se traga en silencio"). La UI lo muestra en su `status_label`.
        self.fichero_danado = False       # el principal no era legible
        self.recuperado_de_backup = False  # se pudo leer el .bak
        self.motivo_danado = ""            # el texto del error, para el mensaje
        self._cached_all_packs: Optional[Dict[str, Pack]] = None
        self.load()

    def invalidate_cache(self) -> None:
        """TASK-040: Invalida la caché inmutable de packs."""
        self._cached_all_packs = None

    def load(self) -> None:
        """Carga los packs del JSON y asegura la existencia del pack Gaming.

        HISTORIA (TASK-026 / FIX-009): antes, `except (json.JSONDecodeError,
        Exception)` -- que es `except Exception` -- regeneraba un `AppData`
        vacio y lo guardaba encima: un apagon durante el `json.dump` borraba
        todos los packs sin aviso, y un `PermissionError` tomaba la misma ruta.

        CONTRATO ACTUAL (TASK-030), dicho sin adornos:

          * SOLO se considera corrupcion lo que esta en `CORRUPTION_ERRORS`
            (`JSONDecodeError`, `ValidationError`, `TypeError`,
            `UnicodeDecodeError` y `PerfilCorruptoError`, que es la forma
            legacy invalida detectada por `_read_json` ANTES de desreferenciar).
            Para esas se intenta el `.bak` y se registra con `logger.warning`.
            `_recover_from_backup()` NO escribe nada.
          * CUALQUIER otro error se PROPAGA tal cual y no se escribe nada:
            `OSError` (permisos, EIO, bloqueo del antivirus) y tambien los
            BUGS INTERNOS (`AttributeError`, `KeyError`, `NameError`...).
            Esto es deliberado: ampliar la tupla para tapar un sintoma
            convertiria un bug de una linea en perdida de packs. NO se anada
            `AttributeError` a la tupla ni se abre un `except Exception`
            (proposal 3.3); un bug debe verse en el log, no tragarse.

        CONTRATO ACTUAL (TASK-031), que CORRIGE el de arriba:

          * `load()` es de SOLO LECTURA. No llama a `save()` por ningun motivo
            (medido: antes lo llamaba DOS veces, desde `_ensure_gaming_pack()` y
            desde aqui). Es el punto que SOSTIENE el diseño de E-1: mientras el
            arranque pueda escribir, cualquier criterio futuro de
            `_ensure_gaming_pack()` vuelve a abrir la puerta a que la rotación
            machaque el `.bak` sano.
          * Sin `.bak` legible NO se regenera a lo bruto. Antes se hacia
            `AppData()` + `_ensure_gaming_pack()` + `save()`, que reESCRIBIA el
            fichero del usuario con un solo pack: una pérdida irreversible y
            sin aviso. Ahora se carga lo legible (que puede ser nada), se marca
            `fichero_danado` y el fichero se QUEDA EN DISCO TAL CUAL, para que el
            usuario o una version posterior lo reparen. La pérdida es
            reversible.
          * El pack `gaming` se asegura EN MEMORIA (`_ensure_gaming_pack()`) y se
            persiste en el primer `save()` real. Se verifico que
            `PROFILES_FILE` no tiene mas consumidores que este `__init__` y que
            `get_gaming_pack()` cae a `DEFAULT_GAMING_PACK`, asi que en una
            instalacion limpia no se crea un `profiles.json` hasta que el usuario
            hace algo: estrictamente mejor, porque un fichero vacio solo confunde.
          * LO QUE `load()` NO PROMETE (y no seAmplia con esta tarea):
              - no es un `load()` "a prueba de todo": un bug interno en
                `_read_json` sigue tumbando el arranque. Es el precio de no
                perder configuracion en silencio;
              - si `save()` falla, el temporal se limpia en su `except` y el
                error original se propaga sin enmascararse.
        """
        if os.path.exists(self.data_path):
            try:
                self._data = self._read_json(self.data_path)
            except CORRUPTION_ERRORS as e:
                self.fichero_danado = True
                self.motivo_danado = f"{e.__class__.__name__}: {e}"
                logger.warning(
                    f"profiles.json ilegible o corrupto ({e.__class__.__name__}: {e}); "
                    f"se intenta recuperar desde {self.data_path}{BACKUP_SUFFIX}"
                )
                if not self._recover_from_backup():
                    # Sin `.bak` legible: se carga lo legible y NADA MAS. El
                    # fichero se queda en disco sin tocar (TASK-031 condicion 3
                    # de proposal.md 3). Escribir aqui lo destruiria.
                    self._data = AppData()
            # OSError y compañía NO se capturan: no son corrupcion y no deben
            # entrar en la ruta que sobrescribe los datos del usuario. Ni los
            # bugs internos (TASK-030): un AttributeError propagado es un bug
            # visible; tragado, es perdida de packs.

        self._ensure_gaming_pack()
        self.invalidate_cache()

    def _read_json(self, path: str) -> AppData:
        """Parsea un profiles.json (principal o .bak) a AppData.

        Aislado de `load()` para que la recuperacion del backup use EXACTAMENTE
        la misma ruta de parseo que el archivo bueno: si el .bak esta en formato
        legacy ('profiles'), tambien se restaura.

        TASK-030: valida la FORMA de la rama legacy y lanza `PerfilCorruptoError`
        (un `ValueError`, luego clasificable como corrupcion) si `profiles` no
        es un mapa o si algun valor no lo es. Deliberado: el `AttributeError`
        que salia de aqui antes NO es corrupcion, es un sintoma, y propagarlo
        es lo correcto.

        TASK-031: la rama legacy deja de SALTARSE el modelo. Antes construia el
        `Pack` con una lista de campos escrita a mano (5 de 8) y por eso
        `keepers` y `target_categories` -- los dos que se perderian -- no se
        leian nunca. Ahora se traduce el registro a un dict moderno y se lo pasa
        a `Pack`: en cuanto `Pack` gane un campo, esta rama lo leera sin que
        nadie se acuerde. `ValidationError` ya estaba en `CORRUPTION_ERRORS`, asi
        que no hace falta ninguna clase de error ni ninguna rama nueva.

        TASK-031 iteracion 2: antes de esto, en las DOS ramas, `_vigilar_hojas()`
        decide identidad y error de escritura (ver su docstring). Se ejecuta
        ANTES de construir el modelo, y por eso el error que lanza es un
        `PerfilCorruptoError` de UNA linea en las dos ramas, no el `ValidationError`
        de 14 lineas de la moderna: quien repara el fichero es el usuario.

        LO QUE ESTA PUERTA NO HACE, a proposito: no decide nada sobre la RAIZ. Un
        `{"perfiles": ...}` (raiz mal escrita) NO es corrupcion, se carga con cero
        packs y su contenido sobrevive al `save()` GRACIAS al `extra="allow"` de
        `AppData`; con `extra="ignore"` el primer `save()` lo destruia (mutacion
        L-M6c, sonda L8). Clasificarlo como corrupcion seria peor: en la ruta sin
        `.bak` `load()` hace `self._data = AppData()` y el siguiente guardado
        borraria los packs del usuario en lugar de conservarlos.

        TASK-031 iteracion 3: ese "GRACIAS al `extra="allow"`" era verdad solo en
        la rama MODERNA, y la diferencia era un agujero de datos (M8). Aqui, la
        rama legacy construia el `AppData` desde cero y descartaba el resto de la
        raiz, de modo que el `extra="allow"` no tenia nada que conservar: un
        `profiles.json` legacy con `favorite` en la raiz perdia ese `favorite` en
        el primer `save()`, en silencio. Arreglado copiando la raiz entera menos
        `profiles` al `AppData` que se construye (sonda `L11`).

        Y la otra mitad del mismo agujero: a la raiz NO se le aplica
        `_vigilar_hojas`, y no es una omision sino una decision medida (sonda
        `L12`, razon completa en el docstring de `_vigilar_hojas`). El contrato
        final sobre la raiz tiene DOS clauses, y las dos estan medidas:
          * una clave raiz desconocida NO se clasifica (L8, L12) -> sobrevive;
          * una clave raiz desconocida NO se borra (L8 en la moderna, L11 en la
            legacy) -> sobrevive al ciclo carga -> guarda.
        """
        with open(path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        if isinstance(raw_data, dict) and 'profiles' in raw_data:
            if 'packs' in raw_data:
                # TASK-031: las dos claves a la vez es CORRUPCION y se nombra el
                # conflicto. Antes la condicion era `'packs' not in raw_data`, de
                # modo que se iba a la rama moderna, `profiles` se ignoraba como
                # clave extra y los packs legacy DESAPARECIAN DEL DISCO en el
                # primer `save()` sin que nada se clasificara. Cualquier
                # resolucion (migrar o descartar) borra packs en silencio, asi que
                # gana la opcion segura: se clasifica y se dice por que.
                raise PerfilCorruptoError(
                    "el fichero tiene las dos claves 'packs' y 'profiles': no se sabe "
                    "cual de las dos manda y quedarse con una sola borra los packs de "
                    "la otra en el siguiente guardado. Separa el fichero o deja solo "
                    "una de las dos claves."
                )
            # TASK-030: se valida la FORMA antes de desreferenciar. Antes,
            # `{"profiles": "texto"}` reventaba con `AttributeError: 'str' object
            # has no attribute 'items'`, y como `AttributeError` NO esta en
            # CORRUPTION_ERRORS (a proposito), el error salia de
            # `PackService.__init__` y la APP NO ARRANCABA. Un solo fichero con
            # la forma equivocada tumbaba el arranque entero.
            perfiles = raw_data['profiles']
            if not isinstance(perfiles, dict):
                raise PerfilCorruptoError(
                    f"'profiles' deberia ser un mapa de perfiles y es "
                    f"{type(perfiles).__name__}"
                )
            # TASK-031 iteracion 2: identidad y error de escritura ANTES de
            # traducir, y en las dos ramas por igual. Se aplica al mapa entero,
            # `__system_gaming__` incluido: la regla no reescribe ese preset, solo
            # puede rechazar un fichero que nadie deberia haber escrito asi.
            _vigilar_hojas(perfiles, "legacy")
            packs_dict = {}
            for k, v in perfiles.items():
                if not isinstance(v, dict):
                    raise PerfilCorruptoError(
                        f"el perfil {k!r} deberia ser un mapa y es {type(v).__name__}"
                    )
                if k == "__system_gaming__":
                    # Preset fijo del PRODUCTO, no dato del usuario: se deja como
                    # esta (fuera de alcance por decision expresa).
                    packs_dict["gaming"] = Pack(
                        id="gaming",
                        name=v.get("label", "🚀 Preparar para Gaming"),
                        is_favorite=True,
                        is_gaming=True,
                        default_action="kill",
                        apps=["chrome.exe"]
                    )
                else:
                    # El UNICO renombrado que existe es `label` -> `name`. Todo
                    # lo demas (apps, keepers, target_categories, is_favorite) se
                    # PASA en vez de descartarse.
                    traducido = dict(v)                     # copia: no se muta el dato del usuario
                    traducido["name"] = v.get("label", k)
                    traducido["id"] = k
                    traducido.pop("label", None)
                    traducido["is_gaming"] = False
                    try:
                        packs_dict[k] = Pack(**traducido)   # <- valida el MODELO
                    except ValidationError as e:
                        # El Pydantic crudo son 14 lineas de diagnostico interno
                        # y no nombra el pack; quien repara el fichero es el
                        # usuario, delante del bloc de notas (TASK-031 T-09.1).
                        raise _hoja_ilegible(k, e) from e
            # TASK-031 iteracion 3 (M8): la rama legacy RECONSTRUIA el `AppData`
            # desde cero (`AppData(packs=packs_dict)`) y se llevaba por delante
            # TODA la raiz que no fuese `packs`/`profiles`. Medido antes de este
            # arreglo: un `profiles.json` legacy real, que trae `favorite` en la
            # raiz, arrancaba, y en el PRIMER `save()` real el fichero quedaba
            # como `{"packs": ...}`: `favorite` (y cualquier otra clave raiz de un
            # build mas nuevo) DESAPARECIA DEL DISCO, en silencio. El
            # `extra="allow"` de `AppData`, que la rama moderna si respeta, aqui
            # no podia hacer nada: el extra no existia porque el objeto se acababa
            # de construir sin el. Un `extra="allow"` que no se copia al objeto
            # no conserva nada.
            #
            # `profiles` SI se descarta, y a proposito: su contenido ya esta en
            # `packs` (traducido), y conservarlo escribiria un fichero con las DOS
            # claves, que la lectura siguiente clasifica como corrupcion (L7).
            # Eso no seria "sobrar informacion": seria un landmine de datos.
            raiz_extra = {k: v for k, v in raw_data.items() if k != "profiles"}
            return AppData(packs=packs_dict, **raiz_extra)
        if isinstance(raw_data, dict):
            # TASK-031 iteracion 2: la misma puerta de identidad y error de
            # escritura que en la rama legacy. El `isinstance` es OBLIGATORIO:
            # `raw_data.get` sobre una lista daria `AttributeError`, que esta
            # fuera de `CORRUPTION_ERRORS` a proposito, y tumbaria el arranque
            # (el sintoma se propaga, la forma la dice el modelo).
            _vigilar_hojas(raw_data.get("packs"), "moderna")
        return AppData(**raw_data)

    def _recover_from_backup(self) -> bool:
        """Restaura los packs desde el .bak. True si se pudo recuperar.

        NUNCA escribe nada: guardar aqui rotaria el principal corrupto encima
        del .bak bueno y perderiamos la unica copia sana.
        """
        bak_path = self.data_path + BACKUP_SUFFIX
        if not os.path.exists(bak_path):
            logger.warning(f"No existe {bak_path}: no hay nada que recuperar.")
            return False
        try:
            self._data = self._read_json(bak_path)
        except CORRUPTION_ERRORS as e:
            logger.warning(f"El backup {bak_path} tampoco es valido ({e.__class__.__name__}: {e}).")
            return False
        except OSError as e:
            # El .bak existe pero no se puede leer (permisos, bloqueo). No es
            # motivo para tumbar la app ni para regenerar a lo bruto.
            logger.warning(f"No se pudo leer el backup {bak_path}: {e}")
            return False
        logger.warning(f"Packs recuperados desde {bak_path}.")
        self.recuperado_de_backup = True
        return True

    def _es_legible(self, path: str) -> bool:
        """Una SOLA definicion de "este fichero es legible para el servicio".

        TASK-031 (E-1). Antes `_rotate_backup()` decidia "el principal NO esta
        corrupto" con `json.load()`, y `load()` decidia lo contrario con
        `_read_json()`: DOS definiciones de lo mismo en el mismo fichero, y el
        docstring de `_rotate_backup()` describia la que NO se ejecutaba. Una
        hoja mal formada (`name: 7`, `keepers: "str"`, `default_action: "PURGAR"`)
        es JSON valido, asi que la rotacion la daba por sana y copiaba el
        principal corrupto ENCIMA del `.bak` bueno. Medido: el `.bak` sano
        moria en 7 de 8 escenarios, y el unico que sobrevivia (H') era el unico
        que la guarda comprobaba de verdad.

        `OSError` NO se traga a proposito: no es corrupcion y debe propagarse
        para que `save()` no escriba "sigo y sobrescribo" (TASK-030 P2).
        """
        try:
            self._read_json(path)
            return True
        except CORRUPTION_ERRORS:
            return False

    def _rotate_backup(self) -> None:
        """Copia la version ANTERIOR de profiles.json a .bak antes de sobrescribir.

        - En una instalacion limpia (no existe el archivo) NO se crea un .bak basura.
        - Si el principal NO es legible PARA EL SERVICIO no se rota: un principal
          roto pisaria el `.bak` bueno, que es justo lo que permite la
          recuperacion de `load()`. "Legible" lo decide `_es_legible()`, es
          decir `_read_json()`: la MISMA puerta que usa `load()`. Antes esta
        comprobacion era `json.load()`, que da por sano un `{"name": 7}` y por
        tanto solo protegia el caso de JSON roto a nivel de sintaxis
        (TASK-031 E-1; la frase anterior de este docstring era FALSA).
        """
        if not os.path.exists(self.data_path):
            return
        if not self._es_legible(self.data_path):
            logger.warning(
                f"No se rota el backup: el principal sigue sin ser legible para el "
                f"servicio ({self.motivo_danado or 'ilegible'})."
            )
            return
        shutil.copy2(self.data_path, self.data_path + BACKUP_SUFFIX)

    def save(self) -> None:
        """Guarda los packs en el disco.

        TASK-026 (FIX-009): rotacion real del backup ANTES de tocar el archivo
        (`open(..., 'w')` trunca) y escritura atomica: se vuelca a un temporal
        en el MISMO directorio y se publica con `os.replace`, de modo que un
        corte de luz no pueda dejar un profiles.json a medias.
        """
        self._rotate_backup()
        tmp_path = f"{self.data_path}.tmp"
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(self._data.model_dump(), f, indent=4, ensure_ascii=False)
            os.replace(tmp_path, self.data_path)
            self.invalidate_cache()
        except Exception:
            # El principal anterior sigue intacto: no se deja un temporal basura.
            # La limpieza NUNCA puede enmascarar el error original.
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
            raise

    def _ensure_gaming_pack(self) -> None:
        """Asegura el pack `gaming` EN MEMORIA (TASK-031: no persiste nada).

        Antes de TASK-031 esta funcion llamaba a `save()`, y `load()` la
        llamaba al final: dos escrituras en el arranque que destruian el `.bak`
        sano. Ahora el pack se asegura aqui y se persiste en el primer `save()`
        REAL (cuando el usuario hace algo). Se verifico por grep que
        `PROFILES_FILE` no tiene mas consumidores que `PackService.__init__` y
        que `get_gaming_pack()` cae a `DEFAULT_GAMING_PACK.model_copy(deep=True)`,
        asi que la app funciona igual sin fichero.
        """
        if "gaming" not in self._data.packs:
            # TASK-021: model_copy() de Pydantic v2 es SHALLOW por defecto, asi
            # que las listas (apps/keepers/target_categories) se COMPARTE con el
            # global de modulo. Si la UI hace `pack.apps.append(...)` sobre el
            # pack gaming (process_manager_view.on_add_to_pack), contaminaba el
            # global y reset_gaming_pack() se convertia en un no-op silencioso.
            # deep=True clona tambien las listas.
            self._data.packs["gaming"] = DEFAULT_GAMING_PACK.model_copy(deep=True)
        else:
            self._data.packs["gaming"].is_gaming = True
            self._data.packs["gaming"].is_favorite = True

    def get_all_packs(self) -> Dict[str, Pack]:
        """TASK-040: Retorna copia defensiva de packs usando caché inmutable de 2 capas (< 0.05 ms)."""
        if self._cached_all_packs is None:
            self._cached_all_packs = {k: p.model_copy(deep=True) for k, p in self._data.packs.items()}
        return {k: p.model_copy(deep=True) for k, p in self._cached_all_packs.items()}

    def update_pack(self, pack: Pack) -> None:
        """TASK-040: Copia el pack en memoria y lo persiste llamando a save() con invalidación de caché."""
        self._data.packs[pack.id] = pack.model_copy(deep=True)
        self.save()
        self.invalidate_cache()

    def mensaje_danado(self) -> Optional[str]:
        """Una linea lista para el `status_label` de la UI, o None si todo bien.

        TASK-031 (T-10.2) / Trampa #14: "nada se traga en silencio". Antes
        "recuperado del .bak" vivia solo en el `logger.warning`, y un usuario no
        abre el log: la recuperacion era invisible por otro camino. La UI pinta
        esto; la LOGICA se queda aqui (la vista no lee ficheros ni decide nada).
        """
        if not self.fichero_danado:
            return None
        if self.recuperado_de_backup:
            return ("Aviso: profiles.json estaba dañado y se ha recuperado "
                    f"desde el .bak. Detalle: {self.motivo_danado}")
        return ("Aviso: profiles.json está dañado y NO hay copia de seguridad "
                f"legible. Se ha arrancado sin tus packs y el fichero se ha dejado "
                f"EN DISCO tal cual para que puedas repararlo. Detalle: "
                f"{self.motivo_danado}")

    def get_gaming_pack(self) -> Pack:
        # TASK-026 (FIX-001): deep=True. `model_copy()` de Pydantic v2 es SHALLOW,
        # asi que sin esto el fallback comparte `apps`/`keepers`/`target_categories`
        # con el global de modulo y cualquier mutacion in situ (la UI las hace al
        # anadir a un pack) contamina DEFAULT_GAMING_PACK. Igual que en
        # _ensure_gaming_pack y reset_gaming_pack.
        return self._data.packs.get("gaming", DEFAULT_GAMING_PACK.model_copy(deep=True))

    def save_gaming_pack(self, pack: Pack) -> None:
        pack.is_gaming = True
        self._data.packs["gaming"] = pack
        self.save()

    def reset_gaming_pack(self) -> None:
        # deep=True: sin esto las listas se comparten con el global de modulo y
        # el reset no desharia cambios hechos in situ. Ver _ensure_gaming_pack.
        self._data.packs["gaming"] = DEFAULT_GAMING_PACK.model_copy(deep=True)
        self.save()

    def get_user_packs(self) -> Dict[str, Pack]:
        return {k: v for k, v in self._data.packs.items() if not v.is_gaming}

    def get_favorite_packs(self) -> List[Pack]:
        """TASK-048: Retorna lista de copias defensivas de packs marcados como favoritos."""
        return [p.model_copy(deep=True) for p in self._data.packs.values() if p.is_favorite]

    def create_user_pack(self, pack_id: str, name: str, apps: List[str]) -> bool:
        if pack_id in self._data.packs or pack_id == "gaming":
            return False
        
        self._data.packs[pack_id] = Pack(id=pack_id, name=name, apps=apps, is_favorite=False, is_gaming=False)
        self.save()
        return True

    def delete_pack(self, pack_id: str) -> bool:
        if pack_id not in self._data.packs:
            return False
        if self._data.packs[pack_id].is_gaming:
            raise ValueError("No se puede eliminar el pack de sistema (Gaming).")
        
        del self._data.packs[pack_id]
        self.save()
        return True

    def set_favorite(self, pack_id: str, value: bool) -> None:
        """TASK-048: Marca o desmarca un pack específico sin alterar los demás.

        Args:
            pack_id: Identificador del pack. Si es None o vacío, lanza ValueError.
            value: True para marcar como favorito, False para desmarcar.

        Raises:
            ValueError: Si pack_id es None o una cadena vacía.
        """
        if not pack_id:
            raise ValueError("pack_id no puede ser None ni vacío.")
        if pack_id not in self._data.packs:
            return
        self._data.packs[pack_id].is_favorite = bool(value)
        self.save()
        self.invalidate_cache()

    def toggle_favorite(self, pack_id: str) -> bool:
        """TASK-048: Lee el estado VIVO de un pack, lo invierte, persiste y devuelve el nuevo valor.

        Args:
            pack_id: Identificador del pack a alternar.

        Returns:
            bool: Nuevo estado de is_favorite.

        Raises:
            ValueError: Si pack_id es None o una cadena vacía.
            KeyError: Si pack_id no existe en los packs cargados.
        """
        if not pack_id:
            raise ValueError("pack_id no puede ser None ni vacío.")
        if pack_id not in self._data.packs:
            raise KeyError(f"Pack '{pack_id}' no encontrado.")
        new_val = not self._data.packs[pack_id].is_favorite
        self._data.packs[pack_id].is_favorite = new_val
        self.save()
        self.invalidate_cache()
        return new_val
