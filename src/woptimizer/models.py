from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Literal

class ProcessInfo(BaseModel):
    name: str
    full_name: str
    pid: int
    exe_path: str = ""
    category: str = "⚪ Otros"
    priority: str = "none"
    description: str = "Sin descripción"

class Pack(BaseModel):
    # TASK-031 (E-4): `extra="allow"`. Un campo que ESTA VERSION no conoce NO es
    # corrupcion (proposal.md 3.2): es el unico mecanismo que hace el formato
    # compatible hacia delante, y es justo cuando mas hace falta (un .bak escrito
    # por un build mas nuevo tiene que ser legible por uno mas viejo). Con el
    # `extra="ignore"` por defecto el campo se BORRABA en el primer `save()`, en
    # silencio. Aqui sobrevive al ciclo carga -> guarda, aunque no lo entendamos.
    # `ProcessInfo` NO lleva `extra="allow"`: no se persiste y no lo necesita.
    #
    # OJO, y es la parte que el mutation-auditor de la iteracion 2 measuro como
    # LINEA PORTANTE (L-M6c): en la RAIZ, `extra="allow"` es lo UNICO que impide
    # que una raiz mal escrita (`{"perfiles": ...}` en vez de `{"packs": ...}`)
    # destruya los packs del usuario. Medido: con `extra="ignore"`, `load()` arranca
    # con cero packs y el PRIMER `save()` deja el fichero como `{"packs": ...}` y los
    # packs del usuario desaparecen del disco para siempre. Ese es el motivo por el
    # que `AppData` lleva el mismo `extra="allow"` y por el que la sonda L8 existe.
    # El precio, DECLARADO y no resuelto: el arranque ve cero packs sin avisar
    # (deuda anotada en data-models.md 4.4 y en tasks.md T-18.3).
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    apps: List[str] = Field(default_factory=list)
    keepers: List[str] = Field(default_factory=list)
    target_categories: List[str] = Field(default_factory=list)
    # TASK-063: simetrico de `target_categories`, y NO un renombramiento suyo.
    # Por que no se renombra `target_categories` a `stop_categories` (que seria
    # el nombre simetrico y el mas legible): porque ese campo YA esta en el
    # `profiles.json` de los usuarios (`pack_service.py:239` lo pone en el pack
    # de fabrica), y renombrarlo exige una migracion cuyo fallo silencioso deja
    # el Gaming Mode cerrando de mas o sin cerrar nada. Anadir este campo nuevo y
    # dejar el viejo como estaba es lo que hace `extra="allow"` arriba posible: un
    # build viejo lee un fichero nuevo (sobrevive al ciclo carga -> guarda) y un
    # build nuevo lee un fichero viejo (el default cubre la clave ausente).
    #
    # CONTRATO (escrito aqui porque es lo que hace que `[]` signifique algo):
    #   * default `[]`, y AUSENTE == VACIO a proposito: es lo que deja que un
    #     `profiles.json` viejo cargue sin migracion y sin aviso.
    #   * `[]` significa "no arrancar por categoria", igual que
    #     `target_categories=[]` significa hoy "no apagar por categoria".
    #   * NO es `Optional[List]` ni `None`: un `None` crearia un tercer estado
    #     (ausente / vacio / nulo) que ningun llamante necesita y que este
    #     `extra="allow"` dejaria pasar sin avisar.
    #   * `start_categories INTERSECT target_categories` tiene que ser vacio. Se
    #     IMPONE al escribir (la casilla espejo de la otra lista viene
    #     deshabilitada) y se RESUELVE en el servicio por si un `profiles.json`
    #     escrito a mano trae el conflicto: gana `kill`, porque apagar destruye
    #     estado y arrancar, como mucho, abre una ventana que el usuario cierra.
    #
    # NO hay que migrar nada: la rama legacy de `load()` entrega el registro
    # entero a `Pack` justamente para que "en cuanto `Pack` gane un campo, esta
    # rama lo lea sin que nadie se acuerde" (`pack_service.py:350-353`), y las
    # cinco copias del pack van con `model_copy(deep=True)`.
    start_categories: List[str] = Field(default_factory=list)
    # TASK-031 iteracion 2: `strict=True` en los booleanos. En modo laxo, Pydantic
    # COACCIONA `"true"`, `"1"` y `"si"` a `True` sin avisar, y con `is_gaming` eso
    # convertia un pack normal en un pack de SISTEMA invisible e indeletable: no
    # aparecia en `get_user_packs()` y `delete_pack` decia "No se puede eliminar el
    # pack de sistema" (medido). Un JSON tiene un tipo booleano propio, asi que una
    # cadena en un campo `bool` no es un valor valido: es un error de escritura, y
    # como tal lo clasifica el servicio (corrupcion, recuperable del `.bak`) en vez
    # de coercionarlo en silencio. No rompe nada de lo que escribe la app: `grep`
    # de `src/` solo encuentra booleanos reales. Sonda: L2, filas
    # `is_gaming: "true"` (solo rama moderna) e `is_favorite: "true"` / `1` (las
    # dos ramas). TASK-031 iteracion 3: el valor de esas filas tiene que ser un
    # valor que Pydantic coaccione en modo LAXO, o la fila no puede distinguir
    # `strict=True` de `strict=False` -- con `"si"` las dos filas originales eran
    # verdes con y sin `strict` (mutacion-sobreviviente M4b).
    is_favorite: bool = Field(default=False, strict=True)
    is_gaming: bool = Field(default=False, strict=True)
    default_action: Literal["start", "kill"] = "start"

class AppData(BaseModel):
    """Estructura raíz de persistencia (profiles.json)"""
    # TASK-031 (E-4): mismo `extra="allow"` que `Pack` y por el mismo motivo: un
    # campo raiz desconocido (por ejemplo `profiles` de un fichero legacy) tiene
    # que sobrevivir al ciclo carga -> guarda en vez de borrarse en silencio.
    #
    # TASK-031 iteracion 2: aqui el `extra="allow"` NO es solo "compatibilidad hacia
    # delante", es la proteccion que impide la perdida de datos descrita arriba
    # (mutacion L-M6c: quitar este `extra` deja el fichero como `{"packs": ...}` y
    # borra los packs del usuario). NO esipotetico: cualquier build que escriba este
    # fichero lo hace con `packs` o con `profiles`, y un `.bak` de un build mas nuevo
    # con una clave raiz nueva tiene que sobrevivir aqui. Sonda: L8.
    model_config = ConfigDict(extra="allow")

    packs: Dict[str, Pack] = Field(default_factory=dict)
