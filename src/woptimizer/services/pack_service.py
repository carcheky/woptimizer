import json
import os
from typing import Dict, List, Optional
from woptimizer.models import AppData, Pack
from woptimizer.config import PROFILES_FILE

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
        self.load()

    def load(self) -> None:
        """Carga los packs desde el archivo JSON y asegura la existencia del pack Gaming."""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    
                    if 'profiles' in raw_data and 'packs' not in raw_data:
                        packs_dict = {}
                        for k, v in raw_data['profiles'].items():
                            if k == "__system_gaming__":
                                packs_dict["gaming"] = Pack(
                                    id="gaming",
                                    name=v.get("label", "🚀 Preparar para Gaming"),
                                    is_favorite=True,
                                    is_gaming=True,
                                    default_action="kill",
                                    apps=["chrome.exe"]
                                )
                            else:
                                packs_dict[k] = Pack(
                                    id=k,
                                    name=v.get("label", k),
                                    apps=v.get("apps", []),
                                    is_favorite=v.get("is_favorite", False),
                                    is_gaming=False,
                                    default_action="start"
                                )
                        self._data = AppData(packs=packs_dict)
                    else:
                        self._data = AppData(**raw_data)
            except (json.JSONDecodeError, Exception):
                self._data = AppData()
                self._ensure_gaming_pack()
                self.save()

        self._ensure_gaming_pack()

    def save(self) -> None:
        """Guarda los packs en el disco."""
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(self._data.model_dump(), f, indent=4, ensure_ascii=False)

    def _ensure_gaming_pack(self) -> None:
        if "gaming" not in self._data.packs:
            # TASK-021: model_copy() de Pydantic v2 es SHALLOW por defecto, asi
            # que las listas (apps/keepers/target_categories) se COMPARTE con el
            # global de modulo. Si la UI hace `pack.apps.append(...)` sobre el
            # pack gaming (process_manager_view.on_add_to_pack), contaminaba el
            # global y reset_gaming_pack() se convertia en un no-op silencioso.
            # deep=True clona tambien las listas.
            self._data.packs["gaming"] = DEFAULT_GAMING_PACK.model_copy(deep=True)
            self.save()
        else:
            self._data.packs["gaming"].is_gaming = True

    def get_all_packs(self) -> Dict[str, Pack]:
        return self._data.packs

    def get_gaming_pack(self) -> Pack:
        return self._data.packs.get("gaming", DEFAULT_GAMING_PACK.model_copy())

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

    def get_favorite_pack(self) -> Optional[Pack]:
        for pack in self._data.packs.values():
            if pack.is_favorite:
                return pack
        return None

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

    def set_favorite(self, pack_id: Optional[str]) -> None:
        """Marca un pack como favorito y desmarca el resto."""
        for k, v in self._data.packs.items():
            v.is_favorite = (k == pack_id)
        self.save()
