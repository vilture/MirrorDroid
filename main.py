#!/usr/bin/env python3
"""
MirrorDroid - GUI для управления scrcpy
Точка входа приложения
"""

import logging
import os
import sys

from PyQt5.QtWidgets import QApplication, QMessageBox

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow
from core.utils import enable_windows_console, is_debug_mode, debug_print


def check_dependencies():
    """Проверяет наличие необходимых зависимостей"""
    import subprocess
    import platform

    # Определяем ОС и выбираем соответствующие пути
    system = platform.system().lower()
    app_dir = os.path.join(os.path.dirname(__file__), 'app')

    if system == 'windows':
        adb_path = os.path.join(app_dir, 'win', 'adb.exe')
        scrcpy_path = os.path.join(app_dir, 'win', 'scrcpy.exe')
    else:  # linux, darwin, etc.
        adb_path = os.path.join(app_dir, 'linux', 'adb')
        scrcpy_path = os.path.join(app_dir, 'linux', 'scrcpy')

    # Проверяем наличие локального adb
    if not os.path.exists(adb_path):
        return False, f"Локальный adb не найден: {adb_path}"

    if not os.access(adb_path, os.X_OK):
        os.chmod(adb_path, 0o755)  # Делаем исполняемым

    # Проверяем наличие локального scrcpy
    if not os.path.exists(scrcpy_path):
        return False, f"Локальный scrcpy не найден: {scrcpy_path}"

    if not os.access(scrcpy_path, os.X_OK):
        os.chmod(scrcpy_path, 0o755)  # Делаем исполняемым

    # Проверяем работоспособность adb
    try:
        result = subprocess.run([adb_path, 'version'], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return False, "Локальный adb не работает"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "Локальный adb не работает"

    # Проверяем работоспособность scrcpy
    try:
        result = subprocess.run([scrcpy_path, '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return False, "Локальный scrcpy не работает"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "Локальный scrcpy не работает"

    return True, "Локальные зависимости найдены и работают"


def main():
    """Главная функция приложения"""
    # Режим отладки
    DEBUG = is_debug_mode()
    if DEBUG:
        os.environ['MIRRORDROID_DEBUG'] = '1'
        logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
        enable_windows_console()
        debug_print("🔧 Debug mode enabled")
    else:
        logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    # Создаем приложение
    app = QApplication(sys.argv)
    app.setApplicationName("MirrorDroid")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("MirrorDroid")

    # Проверяем зависимости
    deps_ok, deps_message = check_dependencies()
    if not deps_ok:
        QMessageBox.critical(None, "Ошибка зависимостей", deps_message)
        sys.exit(1)

    try:
        # Создаем главное окно
        main_window = MainWindow()
        main_window.show()

        # Запускаем приложение
        sys.exit(app.exec_())

    except Exception as e:
        QMessageBox.critical(None, "Критическая ошибка", f"Произошла ошибка при запуске приложения:\n{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
