import json
import os

from PyQt5.QtCore import QObject, pyqtSignal

from .utils import debug_print


class LocalizationManager(QObject):
    """Менеджер локализации для поддержки нескольких языков"""

    # Сигнал для уведомления о смене языка
    language_changed = pyqtSignal(str)

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.current_language = self.config_manager.get_app_setting("language", "ru")
        self.translations = {}
        self.load_translations()

    def load_translations(self):
        """Загружает переводы из файлов"""
        # Определяем путь к папке с переводами
        import sys

        # Проверяем режим PyInstaller более надежно
        is_frozen = getattr(sys, 'frozen', False) or hasattr(sys, '_MEIPASS')

        if is_frozen and hasattr(sys, '_MEIPASS'):
            # Приложение упаковано PyInstaller
            translations_dir = os.path.join(sys._MEIPASS, 'translations')
        else:
            # Приложение запущено из исходного кода
            translations_dir = os.path.join(os.path.dirname(__file__), '..', 'translations')

        # Загружаем русский язык
        ru_file = os.path.join(translations_dir, 'ru.json')

        if os.path.exists(ru_file):
            try:
                with open(ru_file, 'r', encoding='utf-8') as f:
                    self.translations['ru'] = json.load(f)
            except Exception as e:
                self.translations['ru'] = {}
        else:
            self.translations['ru'] = {}

        # Загружаем английский язык
        en_file = os.path.join(translations_dir, 'en.json')

        if os.path.exists(en_file):
            try:
                with open(en_file, 'r', encoding='utf-8') as f:
                    self.translations['en'] = json.load(f)
            except Exception as e:
                self.translations['en'] = {}
        else:
            self.translations['en'] = {}

    def set_language(self, language: str):
        """Устанавливает текущий язык"""
        if language in self.translations:
            self.current_language = language
            self.config_manager.set_app_setting("language", language)
            debug_print(f"🌐 Language changed to: {language}")
            # Отправляем сигнал о смене языка
            self.language_changed.emit(language)
        else:
            debug_print(f"⚠️ Language {language} not supported")

    def get_language(self) -> str:
        """Получает текущий язык"""
        return self.current_language

    def get_available_languages(self) -> list:
        """Получает список доступных языков"""
        return list(self.translations.keys())

    def tr(self, key: str, **kwargs) -> str:
        """Получает переведенную строку с fallback на русский язык"""
        # Получаем переводы для текущего языка
        current_translations = self.translations.get(self.current_language, {})

        # Разбираем ключ по точкам для вложенных словарей
        parts = key.split('.')
        translation = current_translations

        try:
            for part in parts:
                if isinstance(translation, dict) and part in translation:
                    translation = translation[part]
                else:
                    # Если ключ не найден в текущем языке, пробуем русский
                    if self.current_language != 'ru':
                        ru_translations = self.translations.get('ru', {})
                        ru_translation = ru_translations
                        try:
                            for ru_part in parts:
                                if isinstance(ru_translation, dict) and ru_part in ru_translation:
                                    ru_translation = ru_translation[ru_part]
                                else:
                                    ru_translation = key
                                    break
                            if isinstance(ru_translation, str):
                                translation = ru_translation
                                break
                        except (KeyError, TypeError):
                            pass

                    # Если и в русском не найден, возвращаем сам ключ
                    if not isinstance(translation, str):
                        translation = key
                    break
        except (KeyError, TypeError):
            translation = key

        # Если получили словарь вместо строки, возвращаем ключ
        if not isinstance(translation, str):
            translation = key

        # Заменяем параметры в строке, если они переданы
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except (KeyError, ValueError):
                debug_print(f"⚠️ Error formatting string '{key}' with parameters {kwargs}")

        return translation

    def get_translation(self, key: str, language: str = None) -> str:
        """Получает перевод для конкретного языка"""
        if language is None:
            language = self.current_language

        return self.translations.get(language, {}).get(key, key)
