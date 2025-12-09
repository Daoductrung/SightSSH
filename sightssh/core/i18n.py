import json
import os
import locale

class TranslationManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TranslationManager, cls).__new__(cls)
            cls._instance.translations = {}
            cls._instance.current_lang = "en"
            cls._instance.load_languages()
        return cls._instance

    def load_languages(self):
        import sys
        if getattr(sys, 'frozen', False):
            # Running in PyInstaller bundle
            # We expect assets to be at sys._MEIPASS/sightssh/assets/lang
            # Or just sys._MEIPASS/assets/lang depending on how we package.
            # We will package 'sightssh/assets' -> 'sightssh/assets'
            base_path = os.path.join(sys._MEIPASS, "sightssh")
        else:
            # Running from source
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        lang_path = os.path.join(base_path, "assets", "lang")
        
        for filename in os.listdir(lang_path):
            if filename.endswith(".json"):
                lang_code = filename.split(".")[0]
                try:
                    with open(os.path.join(lang_path, filename), "r", encoding="utf-8") as f:
                        self.translations[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Failed to load language {lang_code}: {e}")

    def set_language(self, lang_code):
        if lang_code in self.translations:
            self.current_lang = lang_code
            return True
        return False

    def get(self, key, default=None):
        lang_data = self.translations.get(self.current_lang, {})
        return lang_data.get(key, default if default is not None else key)

# Global helper
_tm = TranslationManager()
def tr(key):
    return _tm.get(key)

def set_language(lang_code):
    return _tm.set_language(lang_code)
