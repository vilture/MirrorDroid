#!/usr/bin/env python3
"""
Общие утилиты для проекта MirrorDroid
"""

import os
import platform
import sys


def debug_print(message):
    """Выводит сообщение только в debug режиме"""
    if os.environ.get('MIRRORDROID_DEBUG') == '1':
        print(message)


def get_icon_path():
    """Определяет правильный путь к иконке для упакованного и неупакованного приложения"""
    if getattr(sys, 'frozen', False):
        # Приложение упаковано PyInstaller
        base_path = sys._MEIPASS
        icon_path = os.path.join(base_path, 'app', 'icon.png')
    else:
        # Приложение запущено из исходного кода
        icon_path = 'app/icon.png'

    return icon_path


def is_windows():
    """Определяет, работает ли приложение на Windows"""
    return platform.system().lower() == 'windows'


def is_debug_mode():
    """Проверяет, запущено ли приложение в debug режиме"""
    return any(arg == '--debug' for arg in sys.argv)


def enable_windows_console():
    """Открывает консоль на Windows для вывода логов, если приложение собрано как windowed."""
    if is_windows():
        try:
            import ctypes
            ctypes.windll.kernel32.AllocConsole()
            sys.stdout = open('CONOUT$', 'w', encoding='utf-8', buffering=1)
            sys.stderr = open('CONOUT$', 'w', encoding='utf-8', buffering=1)
        except Exception:
            pass

