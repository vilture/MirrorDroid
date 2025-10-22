"""
Менеджер путей для разных операционных систем
"""
import os
import platform


class PathManager:
    """Класс для управления путями к исполняемым файлам в зависимости от ОС"""

    def __init__(self):
        self.system = platform.system().lower()
        self.app_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app')

    def get_adb_path(self) -> str:
        """Возвращает путь к ADB в зависимости от ОС"""
        if self.system == 'windows':
            return os.path.join(self.app_dir, 'win', 'adb.exe')
        else:  # linux, darwin, etc.
            return os.path.join(self.app_dir, 'linux', 'adb')

    def get_scrcpy_path(self) -> str:
        """Возвращает путь к scrcpy в зависимости от ОС"""
        if self.system == 'windows':
            return os.path.join(self.app_dir, 'win', 'scrcpy.exe')
        else:  # linux, darwin, etc.
            return os.path.join(self.app_dir, 'linux', 'scrcpy')

    def get_scrcpy_server_path(self) -> str:
        """Возвращает путь к scrcpy-server в зависимости от ОС"""
        if self.system == 'windows':
            return os.path.join(self.app_dir, 'win', 'scrcpy-server')
        else:  # linux, darwin, etc.
            return os.path.join(self.app_dir, 'linux', 'scrcpy-server')

    def is_windows(self) -> bool:
        """Проверяет, является ли система Windows"""
        return self.system == 'windows'

    def is_linux(self) -> bool:
        """Проверяет, является ли система Linux"""
        return self.system == 'linux'



# Глобальный экземпляр для использования в других модулях
path_manager = PathManager()

