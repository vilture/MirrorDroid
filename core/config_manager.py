import json
import os
from typing import Dict, Any, List

from .utils import debug_print


class ConfigManager:
    """Менеджер для сохранения и загрузки настроек приложения"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию из файла"""
        if os.path.exists(self.config_file):
            try:
                debug_print(f"📁 Loading configuration from {self.config_file}")
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                debug_print("✅ Configuration loaded successfully")
                return config
            except (json.JSONDecodeError, IOError) as e:
                debug_print(f"⚠️ Error loading configuration: {e}, using default settings")
                pass

        # Возвращаем конфигурацию по умолчанию
        return {
            "app_settings": {
                "always_on_top": True,
                "auto_scan_network": True,
                "scan_timeout": 5
            },
            "devices": [],
            "scrcpy_defaults": {
                "video": {
                    "max_size": 0,
                    "bit_rate": 8000000,
                    "max_fps": 0,
                    "codec": "h264",
                    "encoder": "",
                    "buffer_size": 0
                },
                "audio": {
                    "codec": "opus",
                    "bit_rate": 128000,
                    "buffer_size": 0,
                    "disable_audio": False
                },
                "display": {
                    "rotation": 0,
                    "crop": "",
                    "fullscreen": False,
                    "always_on_top": False,
                    "window_title": ""
                },
                "control": {
                    "show_touches": False,
                    "stay_awake": False,
                    "turn_screen_off": False
                },
                "record": {
                    "file": "",
                    "format": "mp4",
                    "time_limit": 0
                },
                "advanced": {
                    "keyboard": "disabled",
                    "mouse": "disabled",
                    "gamepad": False,
                    "otg": False,
                    "prefer_text": True,
                    "raw_key_events": False,
                    "no_key_repeat": False,
                    "disable_screensaver": False,
                    "forward_all_clicks": False,
                    "legacy_paste": False,
                    "power_off_on_close": False,
                    "power_on": False,
                    "start_fps": 0,
                    "lock_video_orientation": -1,
                    "display_id": 0,
                    "serial": "",
                    "tcpip": "",
                    "select_usb": False,
                    "select_tcpip": False,
                    "shortcut_mod": "lctrl,lalt,lsuper"
                }
            }
        }

    def save_config(self):
        """Сохраняет конфигурацию в файл"""
        try:
            debug_print(f"💾 Saving configuration to {self.config_file}")
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            debug_print("✅ Configuration saved successfully")
        except IOError as e:
            debug_print(f"❌ Error saving configuration: {e}")

    def get_app_setting(self, key: str, default=None):
        """Получает настройку приложения"""
        return self.config.get("app_settings", {}).get(key, default)

    def set_app_setting(self, key: str, value: Any):
        """Устанавливает настройку приложения"""
        debug_print(f"⚙️ Setting app setting: {key} = {value}")
        if "app_settings" not in self.config:
            self.config["app_settings"] = {}
        self.config["app_settings"][key] = value
        self.save_config()

    def get_devices(self) -> List[Dict[str, Any]]:
        """Получает список сохраненных устройств"""
        return self.config.get("devices", [])

    def add_device(self, device_info: Dict[str, Any]):
        """Добавляет устройство в список"""
        debug_print(f"📱 Adding device: {device_info.get('id', 'unknown')}")
        devices = self.get_devices()
        # Проверяем, не существует ли уже устройство с таким ID
        for i, device in enumerate(devices):
            if device.get("id") == device_info.get("id"):
                debug_print(f"🔄 Updating existing device: {device_info.get('id')}")
                devices[i] = device_info
                break
        else:
            debug_print(f"➕ Adding new device: {device_info.get('id')}")
            devices.append(device_info)

        self.config["devices"] = devices
        self.save_config()

    def remove_device(self, device_id: str):
        """Удаляет устройство из списка"""
        debug_print(f"🗑️ Removing device: {device_id}")
        devices = self.get_devices()
        self.config["devices"] = [d for d in devices if d.get("id") != device_id]
        self.save_config()

    def get_device_settings(self, device_id: str) -> Dict[str, Any]:
        """Получает настройки scrcpy для конкретного устройства"""
        devices = self.get_devices()
        for device in devices:
            if device.get("id") == device_id:
                return device.get("scrcpy_settings", self.get_default_scrcpy_settings())
        return self.get_default_scrcpy_settings()

    def set_device_settings(self, device_id: str, settings: Dict[str, Any]):
        """Устанавливает настройки scrcpy для конкретного устройства"""
        debug_print(f"⚙️ Saving scrcpy settings for device: {device_id}")
        devices = self.get_devices()
        for device in devices:
            if device.get("id") == device_id:
                device["scrcpy_settings"] = settings
                debug_print(f"🔄 Updating settings for existing device: {device_id}")
                break
        else:
            # Если устройство не найдено, создаем новую запись
            debug_print(f"➕ Creating new settings record for device: {device_id}")
            devices.append({
                "id": device_id,
                "scrcpy_settings": settings
            })

        self.config["devices"] = devices
        self.save_config()

    def get_default_scrcpy_settings(self) -> Dict[str, Any]:
        """Получает настройки scrcpy по умолчанию"""
        return self.config.get("scrcpy_defaults", {})

    def set_default_scrcpy_settings(self, settings: Dict[str, Any]):
        """Устанавливает настройки scrcpy по умолчанию"""
        debug_print("⚙️ Saving default scrcpy settings")
        self.config["scrcpy_defaults"] = settings
        self.save_config()

    def get_camera_settings(self, device_id: str) -> Dict[str, Any]:
        """Получает настройки камеры для устройства"""
        devices = self.config.get("devices", [])
        for device in devices:
            if device["id"] == device_id:
                return device.get("camera_settings", self.get_default_camera_settings())

        # Если устройство не найдено, возвращаем настройки по умолчанию
        return self.get_default_camera_settings()

    def set_camera_settings(self, device_id: str, settings: Dict[str, Any]):
        """Устанавливает настройки камеры для устройства"""
        debug_print(f"📷 Saving camera settings for device: {device_id}")
        devices = self.config.get("devices", [])

        # Ищем устройство в списке
        device_found = False
        for device in devices:
            if device["id"] == device_id:
                device["camera_settings"] = settings
                debug_print(f"🔄 Updating camera settings for existing device: {device_id}")
                device_found = True
                break

        if not device_found:
            # Если устройство не найдено, создаем новую запись
            debug_print(f"➕ Creating new camera settings record for device: {device_id}")
            devices.append({
                "id": device_id,
                "camera_settings": settings
            })

        self.config["devices"] = devices
        self.save_config()

    def get_default_camera_settings(self) -> Dict[str, Any]:
        """Получает настройки камеры по умолчанию"""
        return {
            "camera_id": "",  # Будет установлена автоматически при загрузке списка камер
            "camera_size": "",  # Будет установлен автоматически при загрузке размеров
            "camera_fps": 30,  # Максимальный FPS по умолчанию
            "camera_facing": "back",  # Задняя камера по умолчанию
            "camera_ar": "",
            "camera_high_speed": False,
            "camera_no_audio": False  # По умолчанию включаем аудио
        }
