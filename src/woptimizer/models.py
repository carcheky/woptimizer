from pydantic import BaseModel, Field
from typing import List, Dict

class ProcessInfo(BaseModel):
    name: str
    full_name: str
    pid: int
    exe_path: str = ""
    category: str = "⚪ Otros"
    priority: str = "none"

class GamingProfile(BaseModel):
    kind: str = "system"
    label: str = "🚀 Preparar para Gaming"
    keepers: List[str] = Field(default_factory=lambda: ["discord"])
    kill_low_chat: bool = True

class UserProfile(BaseModel):
    name: str = ""
    kind: str = "user"
    label: str
    apps: List[str] = Field(default_factory=list)
    is_favorite: bool = False

class AppData(BaseModel):
    """Estructura raíz de persistencia (profiles.json)"""
    profiles: Dict[str, dict] = Field(default_factory=dict)
