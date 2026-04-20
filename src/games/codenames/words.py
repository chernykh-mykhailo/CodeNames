import os
from typing import List, Dict, Optional

class WordRepository:
    def __init__(self, data_path: str = "data/games/codenames/words"):
        self.data_path = data_path
        self.cached_sets: Dict[str, List[str]] = {} # key: "lang/set_name"

    def get_languages(self) -> List[str]:
        """Returns list of available language codes (folder names)."""
        if not os.path.exists(self.data_path):
            return []
        return [d for d in os.listdir(self.data_path) 
                if os.path.isdir(os.path.join(self.data_path, d))]

    def get_available_sets(self, lang: str) -> List[str]:
        """Returns list of word set names for a given language."""
        lang_path = os.path.join(self.data_path, lang)
        if not os.path.exists(lang_path):
            return []
        return [f.replace(".txt", "") for f in os.listdir(lang_path) if f.endswith(".txt")]

    def list_available_sets(self, lang: str) -> List[str]:
        """Returns list of word set names for a given language."""
        path = os.path.join(self.data_path, lang)
        if not os.path.exists(path):
            return []
        return [f.replace(".txt", "") for f in os.listdir(path) if f.endswith(".txt")]

    def get_set(self, lang: str, set_name: str) -> List[str]:
        """Loads and returns a specific word set for a language."""
        cache_key = f"{lang}/{set_name}"
        if cache_key in self.cached_sets:
            return self.cached_sets[cache_key]
            
        file_path = os.path.join(self.data_path, lang, f"{set_name}.txt")
        if not os.path.exists(file_path):
            return []
            
        with open(file_path, "r", encoding="utf-8") as f:
            words = [line.strip().upper() for line in f if line.strip()]
            self.cached_sets[cache_key] = words
            return words

    def get_default_ua(self) -> List[str]:
        """Backward compatibility for the initial standard set."""
        return self.get_set("uk", "words_normal")
