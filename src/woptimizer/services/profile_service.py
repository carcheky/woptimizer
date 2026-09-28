import json
import os
from typing import Dict, List, Optional
from woptimizer.models import AppData, UserProfile, GamingProfile
from woptimizer.config import PROFILES_FILE, SYSTEM_GAMING_PROFILE_KEY, SYSTEM_GAMING_FACTORY

class ProfileService:
    def __init__(self, data_path: str = PROFILES_FILE):
        self.data_path = data_path
        self._data = AppData()
        self.load()

    def load(self) -> None:
        """Carga los perfiles desde el archivo JSON y asegura la existencia del perfil Gaming."""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    # Convert raw dicts to Pydantic models where appropriate
                    # Though AppData.profiles is Dict[str, dict] for flexibility, we type check on usage
                    self._data = AppData(profiles=raw_data.get('profiles', {}))
            except (json.JSONDecodeError, Exception):
                # Data corrupted, fallback to empty
                self._data = AppData()

        self._ensure_gaming_profile()

    def save(self) -> None:
        """Guarda los perfiles en el disco."""
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(self._data.model_dump(), f, indent=4, ensure_ascii=False)

    def _ensure_gaming_profile(self) -> None:
        if SYSTEM_GAMING_PROFILE_KEY not in self._data.profiles:
            self._data.profiles[SYSTEM_GAMING_PROFILE_KEY] = SYSTEM_GAMING_FACTORY
            self.save()

    def get_all_profiles(self) -> Dict[str, dict]:
        return self._data.profiles

    def get_gaming_profile(self) -> GamingProfile:
        data = self._data.profiles.get(SYSTEM_GAMING_PROFILE_KEY, SYSTEM_GAMING_FACTORY)
        return GamingProfile(**data)

    def save_gaming_profile(self, profile: GamingProfile) -> None:
        self._data.profiles[SYSTEM_GAMING_PROFILE_KEY] = profile.model_dump()
        self.save()

    def reset_gaming_profile(self) -> None:
        self._data.profiles[SYSTEM_GAMING_PROFILE_KEY] = SYSTEM_GAMING_FACTORY
        self.save()

    def get_user_profiles(self) -> Dict[str, UserProfile]:
        res = {}
        for k, v in self._data.profiles.items():
            if k != SYSTEM_GAMING_PROFILE_KEY:
                res[k] = UserProfile(name=k, **v)
        return res

    def get_favorite_profile(self) -> Optional[UserProfile]:
        for k, v in self._data.profiles.items():
            if k != SYSTEM_GAMING_PROFILE_KEY and v.get('is_favorite'):
                return UserProfile(name=k, **v)
        return None

    def create_user_profile(self, name: str, apps: List[str]) -> bool:
        if name in self._data.profiles or name == SYSTEM_GAMING_PROFILE_KEY:
            return False
        
        profile = UserProfile(name=name, label=name, apps=apps)
        # Quitar el name para que no se guarde redundante en el value
        dump = profile.model_dump()
        del dump['name']
        
        self._data.profiles[name] = dump
        self.save()
        return True

    def delete_user_profile(self, name: str) -> bool:
        if name == SYSTEM_GAMING_PROFILE_KEY or name not in self._data.profiles:
            return False
        del self._data.profiles[name]
        self.save()
        return True

    def set_favorite(self, name: Optional[str]) -> None:
        """Marca un perfil como favorito y desmarca el resto."""
        for k, v in self._data.profiles.items():
            if k == SYSTEM_GAMING_PROFILE_KEY:
                continue
            v['is_favorite'] = (k == name)
        self.save()
