import os
import platform
import subprocess
from typing import List, Dict, Optional, Tuple, Any

from PyQt5.QtCore import QObject, pyqtSignal

from .path_manager import path_manager
from .utils import debug_print


def run_subprocess_safe(cmd, **kwargs):
    """Запускает subprocess с параметрами для скрытия консоли на Windows"""
    if platform.system().lower() == 'windows' and os.environ.get('MIRRORDROID_DEBUG') != '1':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        kwargs['startupinfo'] = startupinfo

    return subprocess.run(cmd, **kwargs)


class AdbManager(QObject):
    """Менеджер для работы с ADB командами"""

    device_list_changed = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.devices = []
        # Используем PathManager для определения пути к ADB
        self.adb_path = path_manager.get_adb_path()

    def get_devices(self) -> List[Dict[str, str]]:
        """Получает список подключенных устройств"""
        try:
            result = run_subprocess_safe(
                [self.adb_path, 'devices', '-l'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return []

            devices = []
            lines = result.stdout.strip().split('\n')[1:]  # Пропускаем заголовок

            for line in lines:
                if line.strip():
                    # Разбираем строку, учитывая что разделитель может быть пробелами
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        device_id = parts[0]
                        status = parts[1]

                        # Извлекаем дополнительную информацию
                        device_info = {
                            'id': device_id,
                            'status': status,
                            'connection_type': self._get_connection_type(device_id),
                            'model': self._get_device_model(device_id),
                            'name': self._get_device_name(device_id)
                        }
                        devices.append(device_info)

            self.devices = devices
            self.device_list_changed.emit(devices)
            return devices

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            debug_print(f"⚠️ Error getting device list: {e}")
            return []

    def _get_connection_type(self, device_id: str) -> str:
        """Определяет тип подключения устройства"""
        if ':' in device_id:
            return 'wireless'
        return 'wired'

    def _get_device_model(self, device_id: str) -> str:
        """Получает модель устройства"""
        try:
            result = run_subprocess_safe(
                [self.adb_path, '-s', device_id, 'shell', 'getprop', 'ro.product.model'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return "Unknown"

    def _get_device_name(self, device_id: str) -> str:
        """Получает имя устройства"""
        try:
            result = run_subprocess_safe(
                [self.adb_path, '-s', device_id, 'shell', 'getprop', 'ro.product.device'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return "Unknown"

    def connect_device(self, ip: str, port: int = 5555) -> Tuple[bool, str]:
        """Подключается к устройству по IP"""
        try:
            result = run_subprocess_safe(
                [self.adb_path, 'connect', f'{ip}:{port}'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                if 'connected' in result.stdout.lower():
                    return True, "Успешно подключено"
                else:
                    return False, result.stdout.strip()
            else:
                return False, result.stderr.strip()

        except subprocess.TimeoutExpired:
            return False, "Таймаут подключения"
        except Exception as e:
            return False, f"Ошибка подключения: {e}"

    def disconnect_device(self, device_id: str) -> Tuple[bool, str]:
        """Отключает устройство"""
        try:
            result = run_subprocess_safe(
                [self.adb_path, 'disconnect', device_id],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return True, "Успешно отключено"
            else:
                return False, result.stderr.strip()

        except Exception as e:
            return False, f"Ошибка отключения: {e}"

    def is_device_connected(self, device_id: str) -> bool:
        """Проверяет, подключено ли устройство"""
        for device in self.devices:
            if device['id'] == device_id and device['status'] == 'device':
                return True
        return False

    def get_device_info(self, device_id: str) -> Optional[Dict[str, str]]:
        """Получает информацию о конкретном устройстве"""
        for device in self.devices:
            if device['id'] == device_id:
                return device
        return None

    def refresh_devices(self):
        """Обновляет список устройств"""
        self.get_devices()

    def get_cameras(self, device_id: str) -> List[Dict[str, Any]]:
        """Получает список камер для устройства"""
        try:
            # Используем локальный scrcpy для получения списка камер
            # Используем PathManager для определения пути к scrcpy
            scrcpy_path = path_manager.get_scrcpy_path()
            result = run_subprocess_safe(
                [scrcpy_path, '-s', device_id, '--list-cameras'],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode != 0:
                return []

            cameras = []
            lines = result.stdout.strip().split('\n')

            for line in lines:
                if '--camera-id=' in line and 'List of cameras:' not in line:
                    # Парсим строку вида: --camera-id=0    (back, 4096x3072, fps=[15, 24, 30, 60])
                    parts = line.split('--camera-id=')
                    if len(parts) > 1:
                        camera_info = parts[1].strip()
                        # Извлекаем ID камеры
                        camera_id = camera_info.split()[0]

                        # Извлекаем тип камеры (back/front)
                        camera_type = "unknown"
                        if "(back," in camera_info:
                            camera_type = "back"
                        elif "(front," in camera_info:
                            camera_type = "front"
                        elif "(external," in camera_info:
                            camera_type = "external"

                        # Извлекаем максимальное разрешение
                        resolution = "unknown"
                        if "(" in camera_info and ")" in camera_info:
                            resolution_part = camera_info.split("(")[1].split(")")[0]
                            if "," in resolution_part:
                                resolution = resolution_part.split(",")[1].strip()

                        cameras.append({
                            'id': camera_id,
                            'type': camera_type,
                            'max_resolution': resolution,
                            'description': f"{camera_type} ({resolution})"
                        })

            return cameras
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            debug_print(f"⚠️ Error getting camera list: {e}")
            return []

    def get_camera_sizes(self, device_id: str, camera_id: str) -> List[str]:
        """Получает доступные размеры для конкретной камеры"""
        try:
            # Используем PathManager для определения пути к scrcpy
            scrcpy_path = path_manager.get_scrcpy_path()
            result = run_subprocess_safe(
                [scrcpy_path, '-s', device_id, '--list-camera-sizes'],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode != 0:
                return []

            sizes = []
            lines = result.stdout.strip().split('\n')
            current_camera = None

            for line in lines:
                if f'--camera-id={camera_id}' in line:
                    current_camera = camera_id
                elif current_camera == camera_id and line.strip().startswith('- '):
                    # Парсим строки вида: - 1920x1080 или - 1280x720 (fps=[120, 240, 480])
                    size = line.strip()[2:].strip()
                    # Убираем дополнительную информацию в скобках
                    if '(' in size:
                        size = size.split('(')[0].strip()
                    if 'x' in size and size not in sizes:
                        sizes.append(size)
                elif '--camera-id=' in line and camera_id not in line:
                    current_camera = None

            return sorted(sizes, key=lambda x: (int(x.split('x')[0]) * int(x.split('x')[1])), reverse=True)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            debug_print(f"⚠️ Error getting camera dimensions: {e}")
            return []

    def get_camera_fps_options(self, device_id: str, camera_id: str) -> List[int]:
        """Получает доступные FPS для конкретной камеры"""
        try:
            # Используем PathManager для определения пути к scrcpy
            scrcpy_path = path_manager.get_scrcpy_path()
            result = run_subprocess_safe(
                [scrcpy_path, '-s', device_id, '--list-camera-sizes'],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode != 0:
                return [15, 24, 30, 60]  # Стандартные значения

            fps_options = []
            lines = result.stdout.strip().split('\n')
            current_camera = None

            for line in lines:
                if f'--camera-id={camera_id}' in line:
                    current_camera = camera_id
                    # Извлекаем FPS из строки вида: (back, 4096x3072, fps=[15, 24, 30, 60])
                    if 'fps=[' in line:
                        fps_part = line.split('fps=[')[1].split(']')[0]
                        fps_options = [int(x.strip()) for x in fps_part.split(',')]
                elif '--camera-id=' in line and camera_id not in line:
                    current_camera = None

            return fps_options if fps_options else [15, 24, 30, 60]
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            debug_print(f"⚠️ Error getting camera FPS: {e}")
            return [15, 24, 30, 60]
