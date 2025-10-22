import os
import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QScrollArea,
                             QMessageBox, QStatusBar, QFrame, QCheckBox)

from core.adb_manager import AdbManager
from core.config_manager import ConfigManager
from core.localization import LocalizationManager
from core.scrcpy_manager import ScrcpyManager
from core.utils import debug_print, get_icon_path
from ui.device_widget import DeviceWidget
from ui.settings_dialog import SettingsDialog

# Версия приложения
APP_VERSION = "1.0.0"


class MainWindow(QMainWindow):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()
        self.init_managers()
        self.init_ui()
        self.setup_connections()
        self.load_settings()
        self.refresh_devices()

    def init_managers(self):
        """Инициализация менеджеров"""
        # Определяем путь к config.json рядом с исполняемым файлом
        if getattr(sys, 'frozen', False):
            # Приложение упаковано PyInstaller
            config_path = os.path.join(os.path.dirname(sys.executable), 'config.json')
        else:
            # Приложение запущено из исходного кода
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')

        debug_print(f"📁 Path to config.json: {config_path}")
        self.config_manager = ConfigManager(config_path)
        self.localization_manager = LocalizationManager(self.config_manager)
        self.adb_manager = AdbManager()
        self.scrcpy_manager = ScrcpyManager()

        # Таймер для автообновления
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_devices)
        self.refresh_timer.start(5000)  # Обновляем каждые 5 секунд

    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle(self.localization_manager.tr("app_title"))
        self.setGeometry(100, 100, 1000, 700)

        # Устанавливаем иконку окна
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Устанавливаем опцию "поверх всех окон"
        if self.config_manager.get_app_setting("always_on_top", True):
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Создаем меню
        self.create_menu_bar()

        # Панель инструментов
        self.create_toolbar(main_layout)

        # Область устройств
        self.create_devices_area(main_layout)

        # Статус бар
        self.create_status_bar()

    def create_menu_bar(self):
        """Создает меню - убираем все меню"""
        pass

    def create_toolbar(self, parent_layout):
        """Создает панель инструментов"""
        toolbar_frame = QFrame()
        toolbar_frame.setFrameStyle(QFrame.StyledPanel)
        toolbar_layout = QHBoxLayout()
        toolbar_frame.setLayout(toolbar_layout)

        # Кнопка обновления
        self.refresh_button = QPushButton(self.localization_manager.tr("refresh"))
        self.refresh_button.clicked.connect(self.refresh_devices)
        toolbar_layout.addWidget(self.refresh_button)

        # Поле ввода IP
        toolbar_layout.addWidget(QLabel(self.localization_manager.tr("ip_label")))
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText(self.localization_manager.tr("ip_placeholder"))
        self.ip_input.setMaximumWidth(150)
        toolbar_layout.addWidget(self.ip_input)

        # Кнопка подключения
        self.connect_button = QPushButton(self.localization_manager.tr("connect"))
        self.connect_button.clicked.connect(self.connect_device)
        toolbar_layout.addWidget(self.connect_button)

        # Кнопка автообновления
        self.auto_refresh_check = QCheckBox(self.localization_manager.tr("auto_refresh"))
        self.auto_refresh_check.setChecked(True)
        self.auto_refresh_check.toggled.connect(self.toggle_auto_refresh)
        toolbar_layout.addWidget(self.auto_refresh_check)

        # Кнопка настроек
        self.settings_button = QPushButton(self.localization_manager.tr("settings"))
        self.settings_button.clicked.connect(self.show_scrcpy_settings)
        toolbar_layout.addWidget(self.settings_button)

        # Кнопка остановки всех scrcpy
        self.stop_all_button = QPushButton(self.localization_manager.tr("stop_all"))
        self.stop_all_button.clicked.connect(self.stop_all_scrcpy)
        self.stop_all_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        toolbar_layout.addWidget(self.stop_all_button)

        toolbar_layout.addStretch()

        parent_layout.addWidget(toolbar_frame)

    def create_devices_area(self, parent_layout):
        """Создает область для отображения устройств"""
        # Создаем скроллируемую область
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Контейнер для устройств
        self.devices_widget = QWidget()
        self.devices_layout = QVBoxLayout()
        self.devices_widget.setLayout(self.devices_layout)

        # Заголовок
        title_label = QLabel(self.localization_manager.tr("devices_title"))
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("color: #333; margin: 10px;")
        self.devices_layout.addWidget(title_label)

        # Область для виджетов устройств
        self.devices_container = QWidget()
        self.devices_container_layout = QVBoxLayout()
        self.devices_container.setLayout(self.devices_container_layout)
        self.devices_layout.addWidget(self.devices_container)

        self.devices_layout.addStretch()
        self.scroll_area.setWidget(self.devices_widget)
        parent_layout.addWidget(self.scroll_area)

        # Убираем прогресс бар для сканирования

    def create_status_bar(self):
        """Создает статус бар"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Статус подключенных устройств
        self.devices_status = QLabel(self.localization_manager.tr("devices_status", count=0))
        self.status_bar.addWidget(self.devices_status)

        # Статус активных scrcpy
        self.scrcpy_status = QLabel(self.localization_manager.tr("scrcpy_status", count=0))
        self.status_bar.addWidget(self.scrcpy_status)

        # Статус подключения
        self.connection_status = QLabel("")
        self.status_bar.addPermanentWidget(self.connection_status)

        # Версия приложения (в правом углу)
        self.version_label = QLabel(self.localization_manager.tr("version", version=APP_VERSION))
        self.version_label.setStyleSheet("color: #666; font-size: 11px;")
        self.status_bar.addPermanentWidget(self.version_label)

    def setup_connections(self):
        """Настраивает соединения сигналов"""
        # ADB Manager
        self.adb_manager.device_list_changed.connect(self.on_devices_changed)

        # Scrcpy Manager
        self.scrcpy_manager.process_started.connect(self.on_scrcpy_started)
        self.scrcpy_manager.process_finished.connect(self.on_scrcpy_finished)
        self.scrcpy_manager.process_error.connect(self.on_scrcpy_error)

        # Убираем соединения с Network Scanner

    def load_settings(self):
        """Загружает настройки приложения"""
        # Загружаем сохраненные устройства
        saved_devices = self.config_manager.get_devices()
        for device in saved_devices:
            # Добавляем устройства в список, если они подключены
            pass

    def refresh_devices(self):
        """Обновляет список устройств"""
        devices = self.adb_manager.get_devices()
        self.update_devices_display(devices)
        self.update_status()

    def update_devices_display(self, devices):
        """Обновляет отображение устройств"""
        # Очищаем текущие виджеты
        for i in reversed(range(self.devices_container_layout.count())):
            child = self.devices_container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # Добавляем новые виджеты
        for device in devices:
            device_widget = DeviceWidget(device, self.scrcpy_manager.is_scrcpy_running(device['id']),
                                         self.localization_manager)

            # Подключаем сигналы
            device_widget.start_scrcpy.connect(self.start_scrcpy)
            device_widget.stop_scrcpy.connect(self.stop_scrcpy)
            device_widget.disconnect_device.connect(self.disconnect_device)
            device_widget.remove_device.connect(self.remove_device)
            device_widget.configure_device.connect(self.configure_device)
            device_widget.start_camera.connect(self.start_camera)

            self.devices_container_layout.addWidget(device_widget)

        # Если устройств нет, показываем сообщение
        if not devices:
            no_devices_label = QLabel(self.localization_manager.tr("no_devices"))
            no_devices_label.setAlignment(Qt.AlignCenter)
            no_devices_label.setStyleSheet("color: #666; font-size: 14px; padding: 20px;")
            self.devices_container_layout.addWidget(no_devices_label)

        # Принудительно обновляем интерфейс
        self.devices_container.update()
        self.scroll_area.update()

    def start_scrcpy(self, device_id):
        """Запускает scrcpy для устройства"""
        # Получаем настройки для устройства
        settings = self.config_manager.get_device_settings(device_id)

        # Запускаем scrcpy
        success = self.scrcpy_manager.start_scrcpy(device_id, settings)

        if not success:
            QMessageBox.warning(self, self.localization_manager.tr("messages.error"),
                                self.localization_manager.tr("messages.scrcpy_start_failed", device_id=device_id))
        else:
            self.status_bar.showMessage(self.localization_manager.tr("messages.scrcpy_started", device_id=device_id),
                                        3000)

    def stop_scrcpy(self, device_id):
        """Останавливает scrcpy для устройства"""
        success = self.scrcpy_manager.stop_scrcpy(device_id)
        if success:
            self.status_bar.showMessage(self.localization_manager.tr("messages.scrcpy_stopped", device_id=device_id),
                                        3000)

    def stop_all_scrcpy(self):
        """Останавливает все процессы scrcpy"""
        self.scrcpy_manager.stop_all_scrcpy()
        self.status_bar.showMessage(self.localization_manager.tr("messages.all_scrcpy_stopped"), 3000)

    def connect_device(self):
        """Подключается к устройству по IP"""
        ip = self.ip_input.text().strip()
        if not ip:
            QMessageBox.warning(self, self.localization_manager.tr("messages.error"),
                                self.localization_manager.tr("messages.enter_ip"))
            return

        self.status_bar.showMessage(self.localization_manager.tr("messages.connecting", ip=ip), 0)
        success, message = self.adb_manager.connect_device(ip)

        if success:
            self.status_bar.showMessage(self.localization_manager.tr("messages.device_connected", ip=ip), 3000)
            self.refresh_devices()
        else:
            QMessageBox.warning(self, self.localization_manager.tr("messages.connection_error"), message)
            self.status_bar.showMessage("", 0)

    def disconnect_device(self, device_id):
        """Отключает устройство"""
        success, message = self.adb_manager.disconnect_device(device_id)
        if success:
            self.status_bar.showMessage(
                self.localization_manager.tr("messages.device_disconnected", device_id=device_id), 3000)
            self.refresh_devices()
        else:
            QMessageBox.warning(self, self.localization_manager.tr("messages.disconnection_error"), message)

    def remove_device(self, device_id):
        """Удаляет устройство из списка"""
        self.config_manager.remove_device(device_id)
        self.status_bar.showMessage(self.localization_manager.tr("messages.device_removed", device_id=device_id), 3000)

    def configure_device(self, device_id):
        """Настраивает устройство"""
        current_settings = self.config_manager.get_device_settings(device_id)

        dialog = SettingsDialog(current_settings, self, self.localization_manager)
        dialog.set_current_device(device_id)  # Передаем ID устройства для загрузки камер
        dialog.settings_changed.connect(
            lambda settings: self.save_device_settings(device_id, settings)
        )
        dialog.language_changed.connect(self.on_language_changed)
        dialog.exec_()

    def save_device_settings(self, device_id, settings):
        """Сохраняет настройки устройства"""
        self.config_manager.set_device_settings(device_id, settings)
        self.status_bar.showMessage(self.localization_manager.tr("messages.settings_saved", device_id=device_id), 3000)

    def start_camera(self, device_id: str):
        """Запускает камеру для устройства"""
        from ui.camera_settings_dialog import CameraSettingsDialog

        # Получаем текущие настройки камеры
        camera_settings = self.config_manager.get_camera_settings(device_id)

        # Создаем диалог настроек камеры
        dialog = CameraSettingsDialog(device_id, camera_settings, self, self.localization_manager)
        dialog.settings_changed.connect(lambda settings: self.save_camera_settings(device_id, settings))
        dialog.start_camera.connect(lambda settings: self.launch_camera(device_id, settings))
        dialog.exec_()

    def save_camera_settings(self, device_id: str, settings):
        """Сохраняет настройки камеры"""
        self.config_manager.set_camera_settings(device_id, settings)
        self.status_bar.showMessage(self.localization_manager.tr("messages.camera_settings_saved", device_id=device_id),
                                    3000)

    def launch_camera(self, device_id: str, settings):
        """Запускает камеру с настройками"""
        # Проверяем, не запущена ли уже камера для этого устройства
        if self.scrcpy_manager.is_camera_running(device_id):
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, self.localization_manager.tr("messages.error"),
                                self.localization_manager.tr("messages.camera_already_running", device_id=device_id))
            return

        # Валидация high-speed: требует высокого FPS (обычно >= 120)
        camera = settings.get('camera', {}) if isinstance(settings, dict) else {}
        if camera.get('camera_high_speed'):
            fps = int(camera.get('camera_fps') or 0)
            if fps < 120:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, self.localization_manager.tr("messages.error"),
                                    self.localization_manager.tr("messages.high_speed_fps_warning"))
                return

        success = self.scrcpy_manager.start_camera(device_id, settings)
        if success:
            self.status_bar.showMessage(self.localization_manager.tr("messages.camera_started", device_id=device_id),
                                        3000)
            self.update_devices_display(self.adb_manager.devices)  # Обновляем отображение
        else:
            self.status_bar.showMessage(
                self.localization_manager.tr("messages.camera_start_failed", device_id=device_id), 3000)

    def toggle_auto_refresh(self, enabled):
        """Переключает автообновление"""
        if enabled:
            self.refresh_timer.start(5000)  # Обновляем каждые 5 секунд
            self.status_bar.showMessage(self.localization_manager.tr("messages.auto_refresh_enabled"), 2000)
        else:
            self.refresh_timer.stop()
            self.status_bar.showMessage(self.localization_manager.tr("messages.auto_refresh_disabled"), 2000)

    def show_scrcpy_settings(self, device_id: str = None):
        """Показывает настройки scrcpy"""
        if device_id:
            # Настройки для конкретного устройства
            device_settings = self.config_manager.get_device_settings(device_id)
            dialog = SettingsDialog(device_settings, self, self.localization_manager)
            dialog.set_current_device(device_id)
            dialog.settings_changed.connect(lambda settings: self.save_device_settings(device_id, settings))
            dialog.language_changed.connect(self.on_language_changed)
        else:
            # Глобальные настройки
            default_settings = self.config_manager.get_default_scrcpy_settings()
            dialog = SettingsDialog(default_settings, self, self.localization_manager)
            dialog.settings_changed.connect(self.save_default_settings)
            dialog.language_changed.connect(self.on_language_changed)

        dialog.exec_()

    def save_default_settings(self, settings):
        """Сохраняет настройки по умолчанию"""
        self.config_manager.set_default_scrcpy_settings(settings)
        self.status_bar.showMessage(self.localization_manager.tr("messages.default_settings_saved"), 3000)

    def save_device_settings(self, device_id: str, settings):
        """Сохраняет настройки для конкретного устройства"""
        self.config_manager.set_device_settings(device_id, settings)
        self.status_bar.showMessage(self.localization_manager.tr("messages.settings_saved", device_id=device_id), 3000)

    def update_status(self):
        """Обновляет статус бар"""
        devices_count = len(self.adb_manager.devices)
        scrcpy_count = len(self.scrcpy_manager.get_active_devices())

        self.devices_status.setText(self.localization_manager.tr("devices_status", count=devices_count))
        self.scrcpy_status.setText(self.localization_manager.tr("scrcpy_status", count=scrcpy_count))

    # Обработчики сигналов
    def on_devices_changed(self, devices):
        """Обработчик изменения списка устройств"""
        self.update_devices_display(devices)
        self.update_status()

    def on_scrcpy_started(self, device_id, process_id):
        """Обработчик запуска scrcpy"""
        self.status_bar.showMessage(self.localization_manager.tr("messages.scrcpy_started", device_id=device_id), 3000)
        self.update_status()
        self.refresh_devices()  # Обновляем отображение

    def on_scrcpy_finished(self, device_id, exit_code):
        """Обработчик завершения scrcpy"""
        self.status_bar.showMessage(self.localization_manager.tr("messages.scrcpy_finished", device_id=device_id), 3000)
        self.update_status()
        self.refresh_devices()  # Обновляем отображение

    def on_scrcpy_error(self, device_id, error_message):
        """Обработчик ошибки scrcpy"""
        QMessageBox.warning(self, self.localization_manager.tr("messages.scrcpy_error"),
                            f"{self.localization_manager.tr('messages.error')} для {device_id}:\n{error_message}")
        self.update_status()
        self.refresh_devices()

    def on_language_changed(self, language):
        """Обработчик изменения языка"""
        self.localization_manager.set_language(language)

        # Показываем предупреждение о закрытии приложения
        reply = QMessageBox.question(
            self,
            self.localization_manager.tr("messages.info"),
            self.localization_manager.tr("messages.language_changed", language=language) +
            "\n" + self.localization_manager.tr("messages.restart_required") +
            "\n\n" + self.localization_manager.tr("messages.app_will_close"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            # Закрываем приложение (настройки уже сохранены в LocalizationManager)
            self.close()

    # Убираем методы сканирования сети

    def closeEvent(self, event):
        """Обработчик закрытия приложения"""
        # Останавливаем все процессы scrcpy
        self.scrcpy_manager.stop_all_scrcpy()

        # Сохраняем настройки
        self.config_manager.save_config()

        event.accept()
