#!/usr/bin/env python3
"""
Универсальный скрипт сборки MirrorDroid
Автоматически определяет ОС и использует соответствующий скрипт
"""
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_os_info():
    """Определяет информацию об ОС"""
    system = platform.system().lower()
    machine = platform.machine().lower()

    print(f"Система: {platform.system()} {platform.release()}")
    print(f"Архитектура: {platform.machine()}")
    print(f"Python: {sys.version}")

    return system, machine


def check_dependencies():
    """Проверяет наличие необходимых зависимостей"""
    print("Проверка зависимостей...")

    # Проверяем PyInstaller
    try:
        result = subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'],
                                capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"PyInstaller: {result.stdout.strip()}")
        else:
            print("Установка PyInstaller...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
        print("Установка PyInstaller...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)

    # Проверяем Pillow для обработки иконок
    try:
        result = subprocess.run([sys.executable, '-c', 'import PIL'],
                                capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("Pillow найден")
        else:
            print("Установка Pillow для обработки иконок...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'Pillow'], check=True)
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
        print("Установка Pillow для обработки иконок...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'Pillow'], check=True)

    # Проверяем структуру папок
    app_dir = Path("app")
    if not app_dir.exists():
        print("Папка app/ не найдена!")
        return False

    system, _ = get_os_info()

    if system == 'windows':
        win_dir = app_dir / "win"
        if not win_dir.exists():
            print("Папка app/win/ не найдена!")
            return False
        print("Windows исполняемые файлы найдены")
    else:
        linux_dir = app_dir / "linux"
        if not linux_dir.exists():
            print("Папка app/linux/ не найдена!")
            return False
        print("Linux исполняемые файлы найдены")

    return True


def clean_build():
    """Очищает предыдущие сборки"""
    print("Очистка предыдущих сборок...")

    dirs_to_clean = ['dist', 'build']
    files_to_clean = ['*.spec']

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Удалена папка: {dir_name}")

    for pattern in files_to_clean:
        for file_path in Path('.').glob(pattern):
            file_path.unlink()
            print(f"Удален файл: {file_path}")


def build_application():
    """Собирает приложение"""
    system, machine = get_os_info()

    # Определяем параметры сборки
    if system == 'windows':
        app_name = "MirrorDroid"
        icon_path = "app/icon.png"  # Используем одинаковый путь для кроссплатформенности
        add_data = "app;app"
        print("Сборка для Windows...")
        print("Используется иконка: app/icon.png")
    else:
        app_name = "MirrorDroid"
        icon_path = "app/icon.png"
        add_data = "app:app"
        print("Сборка для Linux...")

    # Команда PyInstaller
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        f'--name={app_name}',
        f'--icon={icon_path}',
        f'--add-data={add_data}',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=json',
        '--hidden-import=subprocess',
        '--hidden-import=threading',
        '--hidden-import=time',
        '--hidden-import=os',
        '--hidden-import=sys',
        '--hidden-import=pathlib',
        '--hidden-import=platform',
        # Добавляем модули приложения
        '--hidden-import=core.localization',
        '--hidden-import=core.config_manager',
        '--hidden-import=core.adb_manager',
        '--hidden-import=core.scrcpy_manager',
        '--hidden-import=core.path_manager',
        '--hidden-import=core.utils',
        '--hidden-import=ui.main_window',
        '--hidden-import=ui.settings_dialog',
        '--hidden-import=ui.camera_settings_dialog',
        '--hidden-import=ui.device_widget',
        'main.py'
    ]

    # Добавляем файлы переводов
    if system == 'windows':
        cmd.extend([
            '--add-data=translations;translations'
        ])
    else:
        cmd.extend([
            '--add-data=translations:translations'
        ])

    # Добавляем Windows-специфичные параметры
    if system == 'windows':
        # Копируем иконку в папку Windows для scrcpy
        import shutil
        win_icon_path = os.path.join('app', 'win', 'icon.png')
        if not os.path.exists(win_icon_path):
            shutil.copy2('app/icon.png', win_icon_path)
            print(f"Скопирована иконка в {win_icon_path}")

        cmd.extend([
            '--add-binary=app\\win\\*.dll;.',
            '--collect-all=PyQt5',
            '--collect-all=PyQt5.QtCore',
            '--collect-all=PyQt5.QtWidgets',
            '--collect-all=PyQt5.QtGui'
        ])

    print("Запуск сборки...")
    print(f"Команда: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Сборка завершена успешно!")
        return True, app_name
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при сборке: {e}")
        print(f"Вывод: {e.stdout}")
        print(f"Ошибки: {e.stderr}")
        return False, None


def check_result(app_name):
    """Проверяет результат сборки"""
    system, _ = get_os_info()

    if system == 'windows':
        exe_path = Path("dist") / "MirrorDroid.exe"
    else:
        exe_path = Path("dist") / "MirrorDroid"

    if exe_path.exists():
        size = exe_path.stat().st_size
        size_mb = size / (1024 * 1024)

        print(f"Исполняемый файл создан: {exe_path}")
        print(f"Размер: {size_mb:.2f} MB")

        # Делаем файл исполняемым на Linux
        if system != 'windows':
            os.chmod(exe_path, 0o755)
            print("Файл сделан исполняемым")

        return True
    else:
        print(f"Исполняемый файл не найден: {exe_path}")
        return False


def main():
    """Главная функция"""
    print("Универсальная сборка MirrorDroid")
    print("=" * 50)

    # Определяем ОС
    system, machine = get_os_info()
    print()

    # Проверяем зависимости
    if not check_dependencies():
        print("❌ Не все зависимости найдены!")
        sys.exit(1)
    print()

    # Очищаем предыдущие сборки
    clean_build()
    print()

    # Собираем приложение
    success, app_name = build_application()
    if not success:
        print("❌ Сборка не удалась!")
        sys.exit(1)
    print()

    # Проверяем результат
    if check_result(app_name):
        print()
        print("🎉 Сборка завершена успешно!")
        print("=" * 50)

        system, _ = get_os_info()
        if system == 'windows':
            print("Для запуска:")
            print("  dist\\MirrorDroid.exe")
            print("или")
            print("  cd dist && MirrorDroid.exe")
        else:
            print("Для запуска:")
            print("  ./dist/MirrorDroid")
            print("или")
            print("  cd dist && ./MirrorDroid")

        print()
        print("Приложение автоматически выберет правильные исполняемые файлы")
    else:
        print("❌ Проверка результата не удалась!")
        sys.exit(1)


if __name__ == "__main__":
    main()
