from pydantic import BaseModel, Field
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
    id: str
    name: str
    apps: List[str] = Field(default_factory=list)
    is_favorite: bool = False
    is_gaming: bool = False
    default_action: Literal["start", "kill"] = "start"

class AppData(BaseModel):
    """Estructura raíz de persistencia (profiles.json)"""
    packs: Dict[str, Pack] = Field(default_factory=dict)
