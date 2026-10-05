import contextlib
import filecmp
import json
import os
import shutil
from typing import Dict, List, Optional, Set
from pydantic import ValidationError
from woptimizer.models import AppData, Pack
from woptimizer.config import (PROFILES_FILE, PROFILES_FILE_NAME, logger,
                               candidatos_de_datos, elegir_ruta_de_datos)

# TASK-069: los nombres de `config` se toman con el `from ... import (a, b, c)`
# de toda la vida, sin `importlib`. El comentario anterior de este sitio
# afirmaba que ESA FORMA FALLA en este interprete cuando `services/pack_service.py`
# esta presente, y lo sostenia con una medicion en un arbol minimo montado en
# `%TEMP%`. MEDIDO de nuevo, y NO SE REPRODUCE: con el arbol real y
# `pack_service.py` presente, el import de cinco nombres a la vez funciona
# (CPython 3.13.8). La linea 9 de este mismo fichero -- 25 lineas por encima de
# aquel comentario -- ya usaba ESA forma con `PROFILES_FILE`, `PROFILES_FILE_NAME`
# y `logger`, y nunca fallo. Un comentario que describe un bug del interprete
# que no existe manda a la siguiente persona a diagnosear el interprete en vez
# del bug, asi que se borra en vez de suavizarse.

BACKUP_SUFFIX = ".bak"
# TASK-069, ronda 2 (el hallazgo que MATA al dueño de su unica copia sana). El
# `.bak` es un ANILLO DE UNA SOLA PLAZA: cada `save()` recycling la plaza con la
# version anterior del principal. La migracion mete una TERCERA generacion en un
# anillo de dos, y el.recycling se come una de las dos antiguas sin avisar.
# MEDIDO (caso C): destino inexistente, `.bak` del dueño con `viejo01` y origen
# con 3 packs. Tras la carga el `.bak` sigue intacto; tras el `save()` el `.bak`
# pasa a los 4 ids de la copia y queda byte a byte igual al ORIGEN, y `viejo01`
# --que no estaba ni en el origen ni en el destino-- DESAPARECE. El `.bak` es lo
# UNICO que el usuario tiene si el destino se corrompe, y la migracion lo
# destruia en su primer guardado.
#
# El sufijo del rescate va PEGADO al del `.bak`, y no al del principal, para que
# un observador del directorio de datos vea la cadena entera:
# `profiles.json` -> `profiles.json.bak` -> `profiles.json.bak.rescate[.N]`.
RESCATE_SUFFIX = ".rescate"
MAX_INTENTOS_DE_RESCATE = 100


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
        # TASK-069 (T-1): el estado de AUSENCIA, que hasta ahora no existia.
        # `fichero_danado`/`motivo_danado` solo se activan con CORRUPCION
        # (`load()`, el `except CORRUPTION_ERRORS`), luego "el usuario perdio sus
        # packs" era indistinguible de "instalacion limpia": los dos casos
        # llegaban a la UI con `mensaje_danado() is None`. Esto es lo que hace
        # la AUSENCIA observable, que es la mitad del dano.
        self.ruta_sin_packs = ""           # destino vacio, con su ruta
        self.packs_en_otra_ruta = ""       # candidato que SI tiene datos
        self.migrado_desde = ""            # origen del que se copio (T-3)
        self.migracion_fallida = ""        # motivo, si la copia no cuadro
        # TASK-069 (T-4): `_ensure_gaming_pack()` repone el Gaming de FABRICA
        # cuando no esta, y ese default tiene 5 `target_categories` y 2
        # `keepers` (`DEFAULT_GAMING_PACK`, definido mas abajo en este mismo
        # fichero; la cita por numero de linea de este comentario era FALSA y
        # apuntaba al centro de `_vigilar_hojas()`). Perder el fichero del
        # usuario no daba "packs vacios": daba un Gaming Mode MAS AGRESSIVO y
        # la DESAPARICION de la lista anti-brick que el codigo creia puesta. Es
        # un fallo de SEGURIDAD, y por eso la reposicion se DECLARA.
        self.gaming_repuesto = False
        self.motivo_gaming_repuesto = ""
        # TASK-069, ronda 2: los ESTADOS de lo que la precedencia deja fuera y de
        # lo que la rotacion ha tenido que apartar para no destruirlo. Los dos
        # son datos del USUARIO y por eso son observables, no `logger.warning`
        # mudo (Trampa #14). Lo que se declara aqui es la MEDIDA, no la
        # preferencia: ver `mensaje_danado()`.
        self.packs_solo_en_el_origen = ""   # hay packs que SOLO estan en el origen
        self.packs_que_no_han_venido: Set[str] = set()
        self.bak_rescatado = ""             # generacion apartada antes de rotar
        self.motivo_bak_rescatado = ""
        # TASK-069 (T-3): la busqueda de la ruta antigua SOLO tiene sentido para
        # el DESTINO REAL de la app. Un `data_path` inyectado es una peticion de
        # "este fichero y ninguno mas", y con ella la busqueda se apaga sola.
        # El MOTIVO de verdad, medido, esta en `_candidatos_para`.
        self.candidatos = self._candidatos_para(self.data_path)
        self._cached_all_packs: Optional[Dict[str, Pack]] = None
        self.load()

    @staticmethod
    def _candidatos_para(data_path: str) -> List[str]:
        """Los candidatos de la ruta antigua, o `[]` si `data_path` no es el
        destino real de la app. La razon de que exista, MEDIDA, y no la que se
        leia antes en este sitio:

        * Que se mantenga. El motivo bueno no es "siete tests empiezan a
          escribir" -- MEDIDO, y al quitar la guarda entera la suite sigue en
          verde: ese numero no se reproduce. El motivo bueno es que
          `src/woptimizer/profiles.json` EXISTE en el arbol de trabajo, y es la
          ruta que `candidatos_de_datos()` devuelve al correr desde el codigo.
          Sin la guarda, cualquier `PackService(data_path=<temporal que aun no
          existe>)` se encontraria con ese fichero y lo migraria dentro del
          temporal: los datos del escritorio del que desarrollo pasan a ser los
          datos del test, y un test que espera "no hay nada" lee packs ajenos.
          Que hoy la suite verde no depende de la guarda sino de QUE tests hay
          escritos, y esa es exactamente la razon por la que no se quita una
          guarda porque hoy nadie la nota.
        * Que no la esconda. La guarda apaga la busqueda y con ella el
          diagnostico, asi que el estado "destino vacio, origen ni mirado" no
          puede ser un Gaming de fabrica en silencio: `mensaje_danado()` lo
          declara por el `not self.candidatos` de su ultima rama. MEDIDO: sin
          esa rama, con un `data_path` inyectado `mensaje_danado()` devolvia
          `None` mientras `_ensure_gaming_pack()` reponia 5 categorias y 2
          keepers.
        * Lo que NO le pasa a un usuario. La app construye el servicio una vez
          (`__main__.py`), sin `data_path`, o sea con el destino real, y ahi la
          guarda no apaga nada. Esta guarda solo apaga cuando alguien INYECTA una
          ruta distinta, que en este repo son los tests. El override
          `WOPTIMIZER_DATA_DIR` tampoco la salta: `PROFILES_FILE` se calcula en
          la importacion con ese override ya aplicado, luego las dos rutas
          coinciden.

        La comparacion es por `normcase` + `abspath` porque en Windows
        `C:\\Users\\x` y `c:\\users\\X` son el mismo fichero y una comparacion
        cruda haria que un test que pase la ruta en otra caja se saltara la
        guarda sin querer.

        Guardian: `test_un_data_path_inyectado_no_busca_la_ruta_antigua`.
        """
        if os.path.normcase(os.path.abspath(data_path)) != \
                os.path.normcase(os.path.abspath(PROFILES_FILE)):
            return []
        return candidatos_de_datos()

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

        PRECEDENCIA (TASK-069), que es un CONTRATO y no un detalle de orden:
        el DESTINO manda SIEMPRE que se pueda leer, y el ORIGEN (el
        `profiles.json` de la 1.0.0) es solo el ultimo recurso. El motivo es
        cronologico y no negociable: el destino es donde el usuario ha ido
        guardando packs desde la 1.1.0, o sea lo MAS NUEVO, y el origen es una
        foto de como tenia las cosas antes. Si el origen se llegara a leer --
        o peor, a pisar `self._data` -- cuando el destino ya es valido, el
        usuario veria sus packs viejos y daria por perdidos los nuevos, SIN
        AVISO, y el primer `save()` escribiria los viejos encima de los
        nuevos: la misma familia de dano que este ciclo vino a cerrar, un paso
        mas alla. Con la precedencia correcta el ORIGEN se lee solo cuando el
        destino es ilegible y no hay `.bak`, que es la unica situacion en la
        que arrancar con el origen es mejor que arrancar con cero packs.
        Guardian: `test_el_destino_manda_sobre_el_origen_si_el_destino_se_puede_leer`.

        LO QUE LA PRECEDENCIA DEJA FUERA, escrito en la ronda 2 del auditor porque
        la regla sin su consecuencia es media regla:

          * **destino legible y VACIO** (`{"packs": {}}`) + origen con packs: gana
            el destino, NO se copia nada y el destino NO se cuenta como "sin
            packs" (`ruta_sin_packs` sigue vacio, porque el destino existe). Los
            packs del origen no vuelven. Hoy es un hecho medido y sin una sola
            palabra de aviso;
          * **destino legible con menos packs que el origen**: gana IGUAL. La
            precedencia es ESTRICTA y el numero de packs NO entra: no fusiona y
            no gana el que tiene mas. El guardian de arriba lo fija como
            comportamiento correcto, y esta frase fija su PRECIO;
          * en los dos, la unica respuesta del servicio es DECIRLO
            (`_anotar_packs_que_solo_viven_en_el_origen`), porque la decision de
            si esos packs deben volver es del dueno y esta escrita como pregunta
            en `docs/ai/data-models.md`, no como comportamiento oculto.
        """
        # El `if` de abajo ES la precedencia. Leer el origen antes -- o dejar que
        # pise `self._data` despues de leer un destino valido -- es la perdida
        # silenciosa que el guardian de arriba deja sin poder volver a pasar.
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
                    # TASK-069 (T-3, condicion 4): antes de resignarse a `AppData()`
                    # vacio --que es arrancar con cero packs-- se intenta el ORIGEN.
                    # Es la REVERSION de la migracion: si el destino se corrompio
                    # a mitad, los packs del usuario siguen en el fichero de la
                    # version anterior y se pueden leer. No se escribe nada.
                    if not self._leer_del_candidato():
                        self._data = AppData()
            else:
                # TASK-069, ronda 2: el destino SE PUEDE LEER, luego por la
                # precedencia de arriba gana y no se copia nada. Lo que la
                # precedencia NO dice, y no se puede adivinar leyendo el
                # destino, es si el origen tiene packs que aqui no estan. Sin
                # esta linea el usuario con 3 packs heredados y un destino de 1
                # no se entera de nada: no hay migracion, no hay fusion y no hay
                # ni una palabra en el log. Solo se ANOTA, nunca se fusiona: la
                # precedencia es un contrato cerrado y esta funcion no lo abre.
                self._anotar_packs_que_solo_viven_en_el_origen()
            # OSError y compañía NO se capturan: no son corrupcion y no deben
            # entrar en la ruta que sobrescribe los datos del usuario. Ni los
            # bugs internos (TASK-030): un AttributeError propagado es un bug
            # visible; tragado, es perdida de packs.
        else:
            # TASK-069 (T-1 y T-3). La AUSENCIA es el caso de esta tarea y hasta
            # aqui no decia NADA. Dos pasos, y el orden es el del contrato:
            # primero se DIAGNOSTICA (T-1, cero escrituras) y despues, solo si
            # hay algo que recuperar, se MIGR A (T-3).
            #
            # T-2 y T-3 son una sola unidad: cambiar la ruta SIN migrar deja al
            # usuario sin packs de forma DEFINITIVA, que es peor que hoy. Por eso
            # esta rama no es opcional aunque `load()` siga siendo de solo
            # lectura con respecto al FICHERO DEL USUARIO: lo que se escribe
            # aqui es un destino NUEVO, nunca el fichero que ya existia.
            self._diagnosticar_y_migrar()

        self._ensure_gaming_pack()
        self.invalidate_cache()

    def _hay_packs_legibles(self, directorio: str) -> bool:
        """¿Hay en `directorio` un `profiles.json` que el servicio sepa leer?

        Inyecta la DECISION de `elegir_ruta_de_datos()` y es el UNICO sitio que
        mira el disco por un candidato. Usa `_es_legible()`, o sea `_read_json()`:
        la MISMA puerta que `load()`. Un `os.path.exists` a secas daria por bueno
        un fichero corrupto y la migracion copiaria breakage al destino nuevo,
        que es la ultima copia sana del usuario.
        """
        if not directorio:
            return False
        return os.path.exists(os.path.join(directorio, PROFILES_FILE_NAME)) and \
            self._es_legible(os.path.join(directorio, PROFILES_FILE_NAME))

    def _diagnosticar_y_migrar(self) -> None:
        """T-1: NOMBRAR el candidato. T-3: COPIARLO con relectura y reversion.

        LA RESTRICCION DURA DE ESTE METODO, y es la que gobierna todo el
        diseno: **mover datos de usuario sin copia es IRREVERSIBLE.** Un fallo a
        mitad destruye lo que el usuario tenia, que es exactamente lo que
        denuncia TASK-069. Por eso hay CUATRO condiciones y se cumplen las
        cuatro:

          1. **NUNCA `move`, NUNCA `os.replace`, NUNCA `unlink`.** Solo
             `shutil.copy2` (que preserva el mtime) y **el origen se queda
             donde esta**. Precedente en este mismo fichero: `_rotate_backup()`
             (:546) ya usa `copy2` para el caso hermano de la rotacion.
          2. **Destino primero, y solo si se relee.** Se copia, se reabre el
             destino y se parsea con el **mismo `_read_json()`** que usa el resto
             del servicio, y se comparan los ids y el numero de packs. Si la
             relectura falla o no cuadra, **no se borra nada** y se avisa: el
             destino a medias se queda para que se pueda inspeccionar.
          3. **El origen intacto es un CRITERIO, no una intencion.** Lo verifica
             `test_la_migracion_deja_el_origen_intacto_byte_a_byte` con `sha256`
             del origen y de su `.bak` antes y despues. Sin esa fila, un
             `shutil.move` disfrazado de migracion pasa la suite entera.
          4. **Reversion.** Con el destino ilegible la resolucion **cae al
             origen** y devuelve los mismos packs, con `fichero_danado`
             observable. Es la respuesta al "y si la migracion se corrompe a
             mitad", y por eso tiene un test PROPIO: sin el, "copio y me olide" y
             "se volver" darian el mismo veredicto.

        LO QUE ESTE METODO NO ES: no es un `load()`. No cambia la semantica de
        `load()` como "solo lectura" respecto al fichero que ya existia; escribe
        un destino NUEVO y solo cuando el destino no existe. Un `load()` sobre
        un `profiles.json` presente no llega aqui.
        """
        self.ruta_sin_packs = self.data_path
        candidatos = self.candidatos
        destino, con_datos = elegir_ruta_de_datos(
            self.data_path, candidatos, self._hay_packs_legibles)
        # `elegir_ruta_de_datos` devuelve `("", [])` en la instalacion limpia, que
        # es el caso legitimo y mayoritario: aqui NO se avisa de nada. Es la
        # contraprueba que mata al mutante SIEMPRE_AVISAR.
        if destino or not con_datos:
            return

        self.packs_en_otra_ruta = con_datos[0]
        # El nombre de la ruta se CONSTRUYE con `os.path.join`, no concatenando
        # el directorio con el fichero. MEDIDO: `f"{con_datos[0]}{PROFILES_FILE_NAME}"`
        # producia `...\\legacyprofiles.json`, una ruta que NO EXISTE, y el aviso
        # de T-1 -- que existe para que el usuario vaya a buscar sus packs --
        # leia una ruta que no lleva a ninguna parte. Peor que no avisar. El
        # mutante `T1_AVISA_RUTA_EQUIVOCADA` devuelve el concatenado y lo mata el
        # test que exige que la ruta nombrada exista de verdad.
        ruta_candidata = os.path.join(con_datos[0], PROFILES_FILE_NAME)
        logger.warning(
            f"No encuentro tus packs en {self.data_path}. Hay packs en "
            f"{ruta_candidata}."
        )
        self._migrar_desde(con_datos[0])

    def _anotar_packs_que_solo_viven_en_el_origen(self) -> None:
        """Anota los packs que existen en el ORIGEN y no en el destino. NUNCA copia.

        Se invoca SOLO cuando el destino se ha leido bien, o sea cuando la
        precedencia ya ha decidido que el destino gana. Aqui no hay nada que
        reparar: la PRECEDENCIA es correcta y esta escrita. Lo que no estaba
        escrito, MEDIDO en la ronda 2 del auditor, es la CONSECUENCIA, y es la
        que toca datos:

          * el destino EXISTE pero esta VACIO (`{"packs": {}}`) y el origen trae
            3 packs: el destino gana, no se copia nada, `migrado_desde` y
            `packs_en_otra_ruta` salen vacios y el mensaje era el del Gaming.
            Los 3 packs heredados NO VOLVEN y NADIE LO DIJE. Y lo que el usuario
            acaba guardando es un Gaming de FABRICA, o sea mas agresivo que el
            suyo;
          * el destino trae 1 pack y el origen trae 3: GANA EL DESTINO tambien.
            El numero de packs NO entra en la precedencia, que es ESTRICTA: no
            fusiona, no gana el que tiene mas, y antes de este metodo no lo
            decia ni el log.

        Que sea una ANOTACION y no una fusion es lo que hace que este metodo no
        pueda romper el contrato que el guardian
        `test_el_destino_manda_sobre_el_origen_si_el_destino_se_puede_leer` fija.
        Decide el producto si esos packs deben volver (es una PREGUNTA ABIERTA
        al dueno, escrita en `docs/ai/data-models.md`); lo que no es opcion es
        que la decision se lleve en silencio.
        """
        if not self.candidatos:
            return
        for candidato in self.candidatos:
            origen = os.path.join(candidato, PROFILES_FILE_NAME)
            if not self._hay_packs_legibles(candidato):
                continue
            try:
                packs_origen = set(self._read_json(origen).packs)
            except CORRUPTION_ERRORS:
                # `_hay_packs_legibles` y `_read_json` discrepan solo si el
                # fichero cambia entre las dos llamadas. No se decide nada con
                # una lectura que falla: la precedencia manda igual y no se
                # inventa una historia.
                continue
            faltan = packs_origen - set(self._data.packs)
            if faltan:
                self.packs_solo_en_el_origen = candidato
                self.packs_que_no_han_venido = faltan
                logger.warning(
                    f"El destino {self.data_path} se ha leido bien y por la "
                    f"precedencia GANA, pero hay {len(faltan)} packs que solo "
                    f"estan en {origen}: {sorted(faltan)}. No se copia nada y no se "
                    f"fusiona: si los quieres, copia ese fichero a "
                    f"{self.data_path} con la app cerrada."
                )
            return

    def _leer_del_candidato(self) -> bool:
        """REVERSION de T-3: lee del ORIGEN sin escribir nada. True si pudo.

        Se invoca SOLO cuando el destino existe pero es ilegible y no hay `.bak`
        que lo repare, o sea cuando la alternativa era arrancar con cero packs.
        Leer el origen devuelve los MISMOS packs que devolveria una migracion
        intacta, con la diferencia de que no toca el disco: el destino corrupto se
        queda en su sitio para que el usuario lo repare, y el origen intacto se
        queda para que la proxima version lo encuentre.

        No es la misma puerta que `_migrar_desde()` y no la delega: migrar COPIA
        y relee el destino, y aqui no hay nada que copiar. Lo que comparte es el
        criterio de "este candidato sirve", `_hay_packs_legibles()`, y por eso las
        dos mitades de la migracion no pueden discrepar sobre que fichero es
        bueno.
        """
        for candidato in self.candidatos:
            origen = os.path.join(candidato, PROFILES_FILE_NAME)
            if not self._hay_packs_legibles(candidato):
                continue
            self._data = self._read_json(origen)
            self.packs_en_otra_ruta = candidato
            self.migrado_desde = candidato
            self.invalidate_cache()
            logger.warning(
                f"El destino {self.data_path} no se puede leer y no hay .bak legible; "
                f"se han leido los packs del ORIGEN {origen} SIN escribir nada. El "
                f"destino se queda en disco tal cual para que puedas repararlo."
            )
            return True
        return False

    @staticmethod
    def _cuadra(referencia: AppData, destino: AppData) -> bool:
        """¿La copia en disco tiene EXACTAMENTE los packs que tenia el origen?

        TASK-069 (T-3, condicion 2). Vive en su propia funcion, y no por gusto:
        MEDIDO, el mutante `SIN_RELECTURA`--convertir esta comprobacion en
        `if False`-- **SOBREVIVIA a la suite entera**, porque en el camino feliz
        la copia siempre cuadra y el `if` no llega a ejecutarse nunca. Una
        comprobacion que solo se puede matar en el camino que no se prueba no es
        una comprobacion. Como metodo estatico y con la comparacion como UNICO
        contenido, el test la puede ejercitar con dos `AppData` que NO cuadran y
        el mutante muere ahi, sin disco.

        Se comparan los CONJUNTOS de ids Y el numero de packs, y no solo el
        numero: dos diccionarios distintos pueden tener la misma cantidad.
        """
        return (set(destino.packs) == set(referencia.packs)
                and len(destino.packs) == len(referencia.packs))

    def _migrar_desde(self, origen_dir: str) -> None:
        """La COPIA de T-3. Condiciones 1, 2 y 4 de `_diagnosticar_y_migrar()`.

        La 3 (origen intacto) no se puede afirmar aqui dentro --afirmarla es lo
        que hace el `sha256` del test--, pero se cumple por construccion: lo
        unico que se hace con el origen es `copy2` LEYENDOLO.
        """
        origen = os.path.join(origen_dir, PROFILES_FILE_NAME)
        # Se parsea el ORIGEN antes de tocar el destino, para no crear un
        # destino nuevo a partir de algo que el servicio no sabe leer.
        try:
            referencia = self._read_json(origen)
        except CORRUPTION_ERRORS as e:
            self.migracion_fallida = (
                f"el packs de {origen} no se puede leer ({e.__class__.__name__}: {e})")
            logger.warning(f"No se migra nada: {self.migracion_fallida}")
            return

        try:
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            # CONDICION 1: `copy2`, y el ORIGEN SE QUEDA. Ni `move`, ni
            # `os.replace`, ni `unlink` en ningun punto de este metodo.
            shutil.copy2(origen, self.data_path)
        except OSError as e:
            # Un `OSError` NO es corrupcion: se registra y se sigue con lo que
            # hubiera, sin propagar, porque tumbar el arranque por no poder
            # escribir el destino nuevo seria peor que arrancar sin migrar.
            self.migracion_fallida = f"no se pudo copiar a {self.data_path} ({e})"
            logger.warning(f"No se migra nada: {self.migracion_fallida}")
            return

        # CONDICION 2: se relee el DESTINO con la MISMA puerta y se CUADRA con
        # el origen. Un "migro bien" sin relectura no es una migracion.
        try:
            destino = self._read_json(self.data_path)
        except CORRUPTION_ERRORS as e:
            self.migracion_fallida = (
                f"la copia en {self.data_path} no se puede leer "
                f"({e.__class__.__name__}: {e}); el original sigue en {origen}")
            logger.warning(f"MIGRACION CORRUPTA: {self.migracion_fallida}")
            # No se borra nada: el origen esta intacto y el destino se queda
            # para poder inspeccionarlo.
            return
        if not self._cuadra(referencia, destino):
            self.migracion_fallida = (
                f"la copia en {self.data_path} no cuadra con el origen: "
                f"{sorted(destino.packs)} contra {sorted(referencia.packs)}; "
                f"el original sigue en {origen}")
            logger.warning(f"MIGRACION INCOMPLETA: {self.migracion_fallida}")
            return

        self._data = destino
        self.migrado_desde = origen_dir
        self.invalidate_cache()
        logger.warning(
            f"Packs migrados por COPIA desde {origen} a {self.data_path}. El "
            f"ORIGINAL SE QUEDA en {origen}: esto no se puede deshacer moviendo, "
            f"y por eso no se movio."
        )

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
        - Y si el `.bak` que se va a machacar guarda packs que NO estan en el
          destino ni en el origen de la migracion --o sea, en NINGUN sitio mas--
          NO se rota sin apartar antes esa generacion (TASK-069 ronda 2). La
          guarda anterior cubria "el principal esta roto"; esta cubre "el `.bak`
          es el UNICO sitio donde vive algo", que es el caso que la destruccion
          que vaso la migracion. Guardian:
          `test_la_rotacion_no_macha_el_bak_que_guarda_lo_unico`.
        """
        if not os.path.exists(self.data_path):
            return
        if not self._es_legible(self.data_path):
            logger.warning(
                f"No se rota el backup: el principal sigue sin ser legible para el "
                f"servicio ({self.motivo_danado or 'ilegible'})."
            )
            return
        bak_path = self.data_path + BACKUP_SUFFIX
        if os.path.exists(bak_path) and not self._rescatar_bak_si_guarda_lo_unico(bak_path):
            # No se puede apartar lo unico que hay: se deja el `.bak` como esta.
            # Un anillo congelado es un inconvenience; un anillo que se come la
            # unica copia del usuario es el fallo que este ciclo vino a cerrar.
            return
        shutil.copy2(self.data_path, bak_path)

    def _ids_recuperables(self) -> Set[str]:
        """Los ids de pack que se pueden volver a leer si el `.bak` se machaca.

        Son los del DESTINO tal y como esta en disco ahora mismo, mas los del
        ORIGEN de la migracion mientras siga ahi y siga legible. La migracion es
        una COPIA y el origen se queda (T-3, condicion 1), luego esos ids son
        reconstruibles sin el `.bak`.

        `OSError` NO se traga y `CORRUPTION_ERRORS` si: un origen que ya no se
        puede leer no hace RECONSTRUIBLE a nadie, asi que un `.bak` ilegible no
        cuenta como generacion recuperable. Es lo que hace que la degradacion
        vaya a "no se rota" en vez de a "se rota y se pierde".
        """
        recuperables: Set[str] = set()
        with contextlib.suppress(CORRUPTION_ERRORS):
            recuperables |= set(self._read_json(self.data_path).packs)
        if self.migrado_desde:
            origen = os.path.join(self.migrado_desde, PROFILES_FILE_NAME)
            with contextlib.suppress(CORRUPTION_ERRORS):
                recuperables |= set(self._read_json(origen).packs)
        return recuperables

    def _rescatar_bak_si_guarda_lo_unico(self, bak_path: str) -> bool:
        """Aparta el `.bak` si guarda packs que no viven en ningun otro sitio.

        True si se puede seguir y rotar (o no habia nada que apartar). False si
        NO se ha podido apartar y el `.bak` se queda intacto.

        EL PORQUE DE ESTA FUNCION, MEDIDO (el hallazgo mas grave de la ronda 2, y
        toca datos del usuario): la rotacion es un anillo de UNA plaza y la
        migracion introduce una TERCERA generacion en un anillo de DOS. Con el
        destino inexistente, un `.bak` previo del dueño y un origen con 3 packs,
        tras el `save()` de la migracion el `.bak` pasa a ser copia del origen
        y el pack que solo vivía en el `.bak` desaparece sin dejar rastro. El
        `.bak` es lo UNICO que el usuario tiene si el destino se corrompe, luego
        reciclarlo a ciegas es peor que no migrar.

        Y el criterio NO es "el `.bak` es distinto del destino" -- que seria la
        regla trivial y que dejaria sin proteger el caso del `.bak` identico. Es
        "**¿hay ALGO aqui que no se pueda recuperar de ningun otro sitio?**", que
        es la misma pregunta que se hace la migracion con `_cuadra()` y la que
        hace que este metodo no pueda machacar nada sin dar algo a cambio.

        NUNCA `move` ni `unlink`: el rescate es `copy2`, y el `.bak` se queda
        donde esta para que la ANIJA de la rotacion siga siendo la de siempre.
        """
        try:
            bak = self._read_json(bak_path)
        except CORRUPTION_ERRORS as e:
            # Un `.bak` ilegible no guarda nada: se avisa y se rota, porque
            # dejarlo puesto no salvaría a nadie y congelaría el anillo.
            logger.warning(
                f"El backup {bak_path} ya no es legible para el servicio "
                f"({e.__class__.__name__}: {e}); no hay nada que apartar y se rota."
            )
            return True

        unicos = set(bak.packs) - self._ids_recuperables()
        if not unicos:
            # El `.bak` no guarda nada que no se pueda releer: rotar es gratis.
            return True

        destino_rescate = self._ruta_de_rescate_libre(bak_path)
        if destino_rescate is None:
            logger.warning(
                f"No se rota el backup: {bak_path} guarda {sorted(unicos)} y no se "
                f"ha encontrado hueco libre para apartarlo tras "
                f"{MAX_INTENTOS_DE_RESCATE} intentos."
            )
            return False
        try:
            shutil.copy2(bak_path, destino_rescate)
        except OSError as e:
            # No se puede escribir el rescate: se congela el anillo en vez de
            # comerse la unica copia. Es el mismo criterio de TASK-030 P2: un
            # `OSError` no se convierte en "sigo y sobrescribo".
            logger.warning(
                f"No se rota el backup: {bak_path} guarda {sorted(unicos)} y no se ha "
                f"podido apartar en {destino_rescate} ({e.__class__.__name__}: {e})."
            )
            return False

        self.bak_rescatado = destino_rescate
        self.motivo_bak_rescatado = (
            f"el backup anterior guardaba {sorted(unicos)}, que no estaban en "
            f"{self.data_path} ni en el origen de la migracion, y rotar lo habria "
            f"borrado: se ha apartado en {destino_rescate} antes de reciclar el "
            f"backup"
        )
        logger.warning(
            f"Backup APARTADO antes de rotar: {bak_path} -> {destino_rescate}. "
            f"Guardaba {sorted(unicos)} y no estaban en ningun otro sitio. Es una "
            f"COPIA: nada se mueve ni se borra."
        )
        return True

    def _ruta_de_rescate_libre(self, bak_path: str) -> Optional[str]:
        """Un nombre libre para el rescate, o `None` si no lo hay.

        `profiles.json.bak.rescate`, y `...rescate.2`, `.3`... si ese ya existe.
        Un rescate ya IDENTICO (mismos bytes) reutiliza su sitio en vez de
        multiplicar ficheros: el caso normal es que se repita el mismo `.bak`, y
        cien copias del mismo contenido no son una red, son ruido.
        """
        base = bak_path + RESCATE_SUFFIX
        for intento in range(1, MAX_INTENTOS_DE_RESCATE + 1):
            candidata = base if intento == 1 else f"{base}.{intento}"
            if not os.path.exists(candidata):
                return candidata
            with contextlib.suppress(OSError):
                if filecmp.cmp(candidata, bak_path, shallow=False):
                    return candidata
        return None

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
            # TASK-069 (T-4): la reposicion se DECLARA, y no es cosmetica.
            # `_ensure_gaming_pack()` convierte "no esta" en "esta el de FABRICA",
            # y ese default tiene 5 `target_categories` y 2 `keepers`
            # (`DEFAULT_GAMING_PACK`, el pack por defecto de este mismo fichero:
            # la cita por numero de linea que estaba aqui, ":231-240", era FALSA
            # y apuntaba al centro de `_vigilar_hojas()`, y el mismo error
            # seguia vivo en `docs/ai/data-models.md`). Perder el
            # `profiles.json` del usuario NO daba packs vacios: daba un Gaming
            # Mode MAS AGRESSIVO (cinco categorias donde el usuario escogio dos) y
            # la DESAPARICION de la lista anti-brick de TASK-023/030, que el
            # codigo creia puesta y no lo estaba. Es un fallo de SEGURIDAD, y por
            # eso el estado es observable y el mensaje NOMBRA lo repuesto: un
            # usuario que ve "5 categorias y los keepers steam/discord" sabe lo
            # que tiene delante; el que no lo ve, cree que es el suyo.
            #
            # Y `_ensure_gaming_pack()` se llama al FINAL de `load()`, sea cual
            # sea la puerta por la que se han cargado los packs. Eso significa
            # que la reposicion ocurre por TRES puertas y no por una, y T-4
            # declaraba solo la primera. MEDIDO en la ronda 2 del auditor, las
            # otras dos son (a) destino ilegible y sin `.bak` legible, con el
            # origen ALSO ilegible -- o sea, ambos ficheros rotos -- y (b) el
            # destino legible pero VACIO. En las dos el mensaje de corrupcion o
            # el de la ausencia tapaban la reposicion y el `save()` siguiente
            # dejaba el fichero del usuario con un solo pack, el de fabrica.
            self.gaming_repuesto = True
            self.motivo_gaming_repuesto = (
                f"el pack Gaming no estaba y se ha repuesto por el de fabrica: "
                f"{len(DEFAULT_GAMING_PACK.target_categories)} categorias "
                f"({', '.join(DEFAULT_GAMING_PACK.target_categories)}) y los "
                f"keepers {', '.join(DEFAULT_GAMING_PACK.keepers)}"
            )
            logger.warning(
                f"Pack Gaming REPUESTO por el de fabrica: "
                f"{len(DEFAULT_GAMING_PACK.target_categories)} categorias y los "
                f"keepers {', '.join(DEFAULT_GAMING_PACK.keepers)}. Si tenias un "
                f"Gaming Mode propio, no se ha recuperado: revisa las categorias y "
                f"los keepers, que son los que deciden que se apaga."
            )
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

        TASK-069 (T-1, T-3, T-4): se suman TRES estados que antes NO tenian
        nombre y que son los que hacen "perdidos" distinguible de "limpio":

          * `ruta_sin_packs` + `packs_en_otra_ruta` -> la AUSENCIA con el
            candidato. Antes `fichero_danado` solo se activaba con CORRUPCION, y
            la ausencia es justo el caso de esta tarea: los dos llegaban aqui
            como `None`.
          * `migrado_desde` / `migracion_fallida` -> el resultado de la COPIA.
          * `gaming_repuesto` -> el Gaming de FABRICA sin que nadie lo pidiera,
            que son 5 categorias y 2 keepers que el usuario no eligio.

        EL ORDEN va de mas grave a menos:

          1. `fichero_danado` (corrupcion): lo de siempre, con su `.bak`.
          2. `ruta_sin_packs` + `packs_en_otra_ruta`: la AUSENCIA con candidato.
             Antes `fichero_danado` solo se activaba con CORRUPCION, y la
             ausencia es justo el caso de esta tarea: los dos llegaban aqui
             como `None`, o sea "perdidos" era indistinguible de "limpio".
          3. `migrado_desde` / `migracion_fallida`: el resultado de la COPIA.
          4. `gaming_repuesto`: el Gaming de FABRICA sin que nadie lo pidiera.

        Y LA CONDICION DE (4), que no es cosmetica: la reposicion se anuncia
        cuando HAYYA UN FICHERO (`ruta_sin_packs` vacio) o cuando hay una perdida
        que narrar. En una instalacion limpia no se dice nada, y ese `None` es
        una contraprueba con dientes: es lo que mata al mutante `SIEMPRE_AVISAR`,
        con el que el caso legitimo y mayoritario --una instalacion nueva--
        avisaria de un problema que no tiene y presentaria un Gaming de fabrica
        como si fuera una incidencia. El gaming de fabrica en la PRIMERA
        ejecucion no es un fallo: es lo que el producto promete, y esa es la
        razon por la que (4) no se sale sola.

        Y LA TERCERA FORMA DE (4), TASK-069: `ruta_sin_packs` Y `candidatos`
        vacio. Es el estado en el que la busqueda de la ruta esta APAGADA
        --`_candidatos_para` no busca cuando el `data_path` inyectado no es el
        destino real-- y entonces no hay packs que narrar ni mensaje que dar, con
        el Gaming de fabrica reponido y 5 categorias que el usuario no eligio.
        MEDIDO: sin esta rama, `mensaje_danado()` devolvia `None` ahi, que es
        justo el Gaming de fabrica en silencio que T-4 vino a quitar. No es lo
        mismo que la instalacion limpia: alli se BUSCO y no se encontro nada, y
        aqui no se busco; por eso el discriminante es `not self.candidatos` y
        no `ruta_sin_packs` a secas.

        TASK-069, RONDA 2. Tres estados mas, y los tres son de esta misma
        familia -- lo que el servicio HACE se escribe; lo que el servicio DEJA
        FUERA y no declara, se denuncia:

          * `packs_solo_en_el_origen`: el destino se lee bien y gana, y hay packs
            que solo viven en el origen. Cubre los dos casos medidos que la
            precedencia no nombraba (destino existente y VACIO, y destino con
            menos packs que el origen). No fusiona y no copia: la precedencia
            es un contrato cerrado y aquí solo se DECLARA su consecuencia.
          * `bak_rescatado`: una generacion del `.bak` se ha apartado porque iba
            a ser machacada por una rotacion y guardaba packs que no estaban en
            ningun otro sitio.
          * Y el `extra` de la reposicion del Gaming se aplica TAMBIEN en la
            rama de corrupcion, que antes la perdia entera.

        Y POR QUE LA REPOSICION DEL GAMING SE DECLARA EN CADA RAMA Y NO EN UNA
        SOLA: porque `_ensure_gaming_pack()` se llama al final de `load()` sea
        cual sea la puerta, luego ocurre por tres y el mensaje sale por la
        primera que se cumple. Un estado que se declara en una rama y se calla en
        las otras dos no esta declarado: esta medio declarado, y el
        `save()` siguiente persiste el Gaming de FABRICA en el fichero del
        usuario sin que el mensaje haya dicho ni una palabra de ello.
        """
        mensaje = self._mensaje_del_estado()
        # El RESCATE va FUERA de la cadena de ramas y se ANADE al final, y es la
        # segunda vez que esta misma funcion se cambia por lo que la anterior
        # callaba. MEDIDO: como rama propia, el rescate no aparecia nunca en el
        # caso de la migracion --que es justo el caso que lo produce-- porque la
        # rama de la AUSENCIA (`ruta_sin_packs`) devuelve antes. Un hecho que le
        # pasa al usuario no puede depender de que otro estado este primero en
        # una lista de `if`.
        if self.bak_rescatado:
            nota = f"Aviso: {self.motivo_bak_rescatado}."
            return f"{mensaje} {nota}" if mensaje else nota
        return mensaje

    def _mensaje_del_estado(self) -> Optional[str]:
        if self.fichero_danado:
            # TASK-069, ronda 2. LA REPOSICION SE NOMBRA AQUI TAMBIEN, y es el
            # segundo punto ciego que cerro el mismo agujero: con el destino
            # ILEGIBLE y el ORIGEN ALSO ilegible, `gaming_repuesto` es True
            # (`_ensure_gaming_pack()` se llama igual al final de `load()`) y el
            # `return` de esta rama se comia el motivo. MEDIDO: el mensaje
            # nombraba la corrupcion y NO el Gaming de fabrica que el
            # `save()` siguiente iba a dejar en el fichero del usuario. Un
            # mensaje que declara una perdida y calla la otra sigue siendo un
            # mensaje incompleto, y aqui la otra es la de SEGURIDAD.
            extra = (f" {self.motivo_gaming_repuesto}." if self.gaming_repuesto else "")
            if self.recuperado_de_backup:
                return ("Aviso: profiles.json estaba dañado y se ha recuperado "
                        f"desde el .bak. Detalle: {self.motivo_danado}{extra}")
            return ("Aviso: profiles.json está dañado y NO hay copia de seguridad "
                    f"legible. Se ha arrancado sin tus packs y el fichero se ha dejado "
                    f"EN DISCO tal cual para que puedas repararlo. Detalle: "
                    f"{self.motivo_danado}{extra}")
        if self.ruta_sin_packs and self.packs_en_otra_ruta:
            extra = (f" {self.motivo_gaming_repuesto}." if self.gaming_repuesto else "")
            return (f"Aviso: no encuentro tus packs en {self.ruta_sin_packs}. Hay "
                    f"packs en {os.path.join(self.packs_en_otra_ruta, PROFILES_FILE_NAME)}: "
                    f"copia ese fichero a {self.ruta_sin_packs} para recuperarlos."
                    f"{extra}")
        if self.migracion_fallida:
            return (f"Aviso: tus packs NO se han migrado a la ruta nueva. "
                    f"{self.migracion_fallida}")
        if self.migrado_desde:
            extra = (f" {self.motivo_gaming_repuesto}." if self.gaming_repuesto else "")
            return (f"Aviso: tus packs estaban en "
                    f"{os.path.join(self.migrado_desde, PROFILES_FILE_NAME)} y se "
                    f"han copiado a {self.data_path}. El original se ha dejado "
                    f"intacto donde estaba.{extra}")
        if self.packs_solo_en_el_origen:
            # TASK-069, ronda 2, y es el caso que la precedencia escrita no
            # cubria. MEDIDO: destino legible y VACIO con 3 packs en el origen, y
            # destino con 1 pack contra 3 en el origen. En los dos gana el
            # destino, no se copia nada y no hay fusion; lo que faltaba era
            # DECIRLO. Sin esta rama los dos devolvian el mensaje del Gaming (o
            # `None`) y el usuario se enteraba de que sus packs no habian vuelto
            # por la via de que no estaban. La precedencia es correcta y no se
            # toca: lo que se declara es su CONSECUENCIA.
            extra = (f" {self.motivo_gaming_repuesto}." if self.gaming_repuesto else "")
            return (f"Aviso: {self.data_path} manda por la regla de precedencia y sus "
                    f"packs han ganado, pero hay {len(self.packs_que_no_han_venido)} "
                    f"pack(s) que solo existen en "
                    f"{os.path.join(self.packs_solo_en_el_origen, PROFILES_FILE_NAME)}: "
                    f"{sorted(self.packs_que_no_han_venido)}. No se ha copiado nada y "
                    f"no se fusiona nada; si los quieres, copia ese fichero a "
                    f"{self.data_path} con la app cerrada.{extra}")
        if self.gaming_repuesto and not self.ruta_sin_packs:
            # El fichero EXISTIA y no traia el pack `gaming`: algo se llevo el
            # Gaming del usuario de un fichero que sigue ahi. Eso si se cuenta,
            # y el mensaje NOMBRA lo repuesto en vez de dar un "packs restaurados"
            # generico.
            return f"Aviso: {self.motivo_gaming_repuesto}."
        if self.gaming_repuesto and self.ruta_sin_packs and not self.candidatos:
            return (f"Aviso: {self.ruta_sin_packs} esta vacio y no se ha buscado "
                    f"ninguna ruta antigua, asi que no hay packs que recuperar. "
                    f"{self.motivo_gaming_repuesto}.")
        return None

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
