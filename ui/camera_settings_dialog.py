import os
import platform
import subprocess
import threading

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QComboBox, QCheckBox, QPushButton,
                             QGroupBox, QFormLayout, QMessageBox, QInputDialog)

from core.utils import debug_print, get_icon_path, is_windows


class CameraSettingsDialog(QDialog):
    """Диалог настроек камеры"""

    settings_changed = pyqtSignal(dict)  # новые настройки камеры
    start_camera = pyqtSignal(dict)  # запуск камеры с настройками

    def __init__(self, device_id: str, current_settings: dict = None, parent=None, localization_manager=None):
        super().__init__(parent)
        self.device_id = device_id
        self.current_settings = current_settings or {}
        self.localization_manager = localization_manager

        self.setWindowTitle(f"{self.localization_manager.tr('camera_settings.title')} - {device_id}")
        self.setModal(True)
        self.resize(750, 600)

        # Устанавливаем иконку окна
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._create_ui()
        self.load_settings()

        # Изначально отключаем V4L2 поля
        self._update_v4l2_fields_state()

    def _create_ui(self):
        """Создает интерфейс"""
        layout = QVBoxLayout()

        # Заголовок
        title_text = self.localization_manager.tr("camera_settings.title")
        title_label = QLabel(title_text)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Основные настройки
        main_group_title = self.localization_manager.tr("camera_settings.main_settings")
        main_group = QGroupBox(main_group_title)
        main_layout = QFormLayout()

        # Кнопка обновления списка камер
        refresh_layout = QHBoxLayout()
        refresh_text = self.localization_manager.tr("camera_settings.refresh_cameras")
        refresh_tooltip = self.localization_manager.tr("camera_settings.refresh_cameras_tooltip")
        self.refresh_cameras_button = QPushButton(refresh_text)
        self.refresh_cameras_button.setToolTip(refresh_tooltip)
        self.refresh_cameras_button.clicked.connect(self._refresh_camera_list)
        refresh_layout.addWidget(self.refresh_cameras_button)
        refresh_layout.addStretch()
        main_layout.addRow("", refresh_layout)

        # ID камеры (выпадающий список)
        self.camera_id_combo = QComboBox()
        camera_placeholder = self.localization_manager.tr("camera_settings.select_camera")
        camera_tooltip = self.localization_manager.tr("camera_settings.camera_tooltip")
        camera_label = self.localization_manager.tr("camera_settings.camera")
        self.camera_id_combo.setPlaceholderText(camera_placeholder)
        self.camera_id_combo.setToolTip(camera_tooltip)
        self.camera_id_combo.currentTextChanged.connect(self._on_camera_id_changed)
        main_layout.addRow(camera_label, self.camera_id_combo)

        # Размер камеры (выпадающий список)
        self.camera_size_combo = QComboBox()
        size_placeholder = self.localization_manager.tr("camera_settings.select_size")
        size_tooltip = self.localization_manager.tr("camera_settings.camera_size_tooltip")
        size_label = self.localization_manager.tr("camera_settings.camera_size")
        self.camera_size_combo.setPlaceholderText(size_placeholder)
        self.camera_size_combo.setToolTip(size_tooltip)
        self.camera_size_combo.setEditable(True)
        self.camera_size_combo.setInsertPolicy(QComboBox.NoInsert)
        main_layout.addRow(size_label, self.camera_size_combo)

        # FPS камеры (выпадающий список)
        self.camera_fps_combo = QComboBox()
        fps_placeholder = self.localization_manager.tr("camera_settings.select_fps")
        fps_tooltip = self.localization_manager.tr("camera_settings.camera_fps_tooltip")
        fps_label = self.localization_manager.tr("camera_settings.camera_fps")
        self.camera_fps_combo.setPlaceholderText(fps_placeholder)
        self.camera_fps_combo.setToolTip(fps_tooltip)
        main_layout.addRow(fps_label, self.camera_fps_combo)

        main_group.setLayout(main_layout)
        layout.addWidget(main_group)

        # Дополнительные настройки камеры
        advanced_group_title = self.localization_manager.tr("camera_settings.advanced_settings")
        advanced_group = QGroupBox(advanced_group_title)
        advanced_layout = QFormLayout()

        # Соотношение сторон
        self.camera_ar_combo = QComboBox()
        self.camera_ar_combo.addItems(["", "sensor", "4:3", "16:9", "1:1"])
        auto_text = self.localization_manager.tr("camera_settings.automatically")
        ar_tooltip = self.localization_manager.tr("camera_settings.aspect_ratio_tooltip")
        ar_label = self.localization_manager.tr("camera_settings.aspect_ratio")
        self.camera_ar_combo.setItemText(0, auto_text)
        self.camera_ar_combo.setToolTip(ar_tooltip)
        advanced_layout.addRow(ar_label, self.camera_ar_combo)

        # Высокоскоростная съемка
        high_speed_text = self.localization_manager.tr("camera_settings.high_speed")
        high_speed_tooltip = self.localization_manager.tr("camera_settings.high_speed_tooltip")
        self.camera_high_speed_check = QCheckBox(high_speed_text)
        self.camera_high_speed_check.setToolTip(high_speed_tooltip)
        advanced_layout.addRow("", self.camera_high_speed_check)

        # Отключить звук камеры
        no_audio_text = self.localization_manager.tr("camera_settings.no_audio")
        no_audio_tooltip = self.localization_manager.tr("camera_settings.no_audio_tooltip")
        self.camera_no_audio_check = QCheckBox(no_audio_text)
        self.camera_no_audio_check.setToolTip(no_audio_tooltip)
        advanced_layout.addRow("", self.camera_no_audio_check)

        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)

        # Настройки отображения
        display_title = self.localization_manager.tr("camera_settings.display_settings")
        display_group = QGroupBox(display_title)
        display_layout = QFormLayout()

        # Поворот
        self.rotation_combo = QComboBox()
        self.rotation_combo.addItems(["0°", "90°", "180°", "270°"])
        self.rotation_combo.setToolTip(self.localization_manager.tr("camera_settings.rotation_tooltip"))
        rotation_label = self.localization_manager.tr("camera_settings.rotation")
        display_layout.addRow(rotation_label, self.rotation_combo)

        # Обрезка
        self.crop_edit = QLineEdit()
        self.crop_edit.setPlaceholderText(self.localization_manager.tr("camera_settings.crop_placeholder"))
        self.crop_edit.setToolTip(self.localization_manager.tr("camera_settings.crop_tooltip"))
        crop_label = self.localization_manager.tr("camera_settings.crop")
        display_layout.addRow(crop_label, self.crop_edit)

        # Зеркальное отображение
        self.flip_check = QCheckBox()
        self.flip_check.setToolTip(self.localization_manager.tr("camera_settings.flip_tooltip"))
        flip_label = self.localization_manager.tr("camera_settings.flip")
        display_layout.addRow(flip_label, self.flip_check)

        # Полноэкранный режим
        self.fullscreen_check = QCheckBox()
        self.fullscreen_check.setToolTip(self.localization_manager.tr("camera_settings.fullscreen_tooltip"))
        fullscreen_label = self.localization_manager.tr("camera_settings.fullscreen")
        display_layout.addRow(fullscreen_label, self.fullscreen_check)

        # Поверх всех окон
        self.always_on_top_check = QCheckBox()
        self.always_on_top_check.setToolTip(self.localization_manager.tr("camera_settings.always_on_top_tooltip"))
        always_on_top_label = self.localization_manager.tr("camera_settings.always_on_top")
        display_layout.addRow(always_on_top_label, self.always_on_top_check)

        display_group.setLayout(display_layout)
        layout.addWidget(display_group)

        # V4L2 настройки (только для Linux)
        self.v4l2_group = None
        current_system = platform.system().lower()
        debug_print(f"🔍 Detected OS: {current_system}")

        if not is_windows():
            v4l2_group_title = self.localization_manager.tr("camera_settings.v4l2_settings")
            info_text = self.localization_manager.tr("camera_settings.v4l2_info")
            v4l2_enabled_text = self.localization_manager.tr("camera_settings.v4l2_enabled")
            v4l2_enabled_tooltip = self.localization_manager.tr("camera_settings.v4l2_enabled_tooltip")
            self.v4l2_group = QGroupBox(v4l2_group_title)
            v4l2_layout = QFormLayout()

            # Информационное примечание
            info_label = QLabel(info_text)
            info_label.setWordWrap(True)
            info_label.setStyleSheet(
                "color: #666; font-size: 11px; padding: 5px; background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 3px;")
            v4l2_layout.addRow("", info_label)

            # Чекбокс для включения V4L2
            self.v4l2_enabled_check = QCheckBox(v4l2_enabled_text)
            self.v4l2_enabled_check.setToolTip(v4l2_enabled_tooltip)
            self.v4l2_enabled_check.toggled.connect(self._on_v4l2_enabled_changed)
            v4l2_layout.addRow("", self.v4l2_enabled_check)

            # V4L2 устройство
            self.v4l2_device_edit = QLineEdit()
            device_placeholder = self.localization_manager.tr("camera_settings.placeholder_device")
            device_tooltip = self.localization_manager.tr("camera_settings.v4l2_device_tooltip")
            device_label = self.localization_manager.tr("camera_settings.v4l2_device")
            self.v4l2_device_edit.setPlaceholderText(device_placeholder)
            self.v4l2_device_edit.setToolTip(device_tooltip)
            v4l2_layout.addRow(device_label, self.v4l2_device_edit)

            # V4L2 размер (информационное поле)
            size_info = self.localization_manager.tr("camera_settings.v4l2_size_info")
            size_label = self.localization_manager.tr("camera_settings.v4l2_size")
            self.v4l2_size_label = QLabel(size_info)
            self.v4l2_size_label.setStyleSheet("color: #666; font-style: italic;")
            v4l2_layout.addRow(size_label, self.v4l2_size_label)

            # V4L2 FPS (информационное поле)
            fps_info = self.localization_manager.tr("camera_settings.v4l2_fps_info")
            fps_label = self.localization_manager.tr("camera_settings.v4l2_fps")
            self.v4l2_fps_label = QLabel(fps_info)
            self.v4l2_fps_label.setStyleSheet("color: #666; font-style: italic;")
            v4l2_layout.addRow(fps_label, self.v4l2_fps_label)

            # V4L2 буфер
            self.v4l2_buffer_spin = QSpinBox()
            self.v4l2_buffer_spin.setRange(1, 10)
            self.v4l2_buffer_spin.setValue(3)
            buffer_tooltip = self.localization_manager.tr("camera_settings.v4l2_buffers_tooltip")
            buffer_label = self.localization_manager.tr("camera_settings.v4l2_buffers")
            self.v4l2_buffer_spin.setToolTip(buffer_tooltip)
            v4l2_layout.addRow(buffer_label, self.v4l2_buffer_spin)

            # Отключить воспроизведение видео
            no_playback_text = self.localization_manager.tr("camera_settings.v4l2_no_playback")
            no_playback_tooltip = self.localization_manager.tr("camera_settings.v4l2_no_playback_tooltip")
            self.v4l2_no_playback_check = QCheckBox(no_playback_text)
            self.v4l2_no_playback_check.setChecked(False)
            self.v4l2_no_playback_check.setToolTip(no_playback_tooltip)
            v4l2_layout.addRow("", self.v4l2_no_playback_check)

            # Кнопки V4L2
            v4l2_buttons_layout = QHBoxLayout()

            setup_text = self.localization_manager.tr("camera_settings.setup_v4l2")
            setup_tooltip = self.localization_manager.tr("camera_settings.setup_v4l2_tooltip")
            test_text = self.localization_manager.tr("camera_settings.test_v4l2")
            test_tooltip = self.localization_manager.tr("camera_settings.test_v4l2_tooltip")

            self.setup_v4l2_button = QPushButton(setup_text)
            self.setup_v4l2_button.clicked.connect(self._setup_v4l2)
            self.setup_v4l2_button.setToolTip(setup_tooltip)
            v4l2_buttons_layout.addWidget(self.setup_v4l2_button)

            self.test_v4l2_button = QPushButton(test_text)
            self.test_v4l2_button.clicked.connect(self._test_v4l2)
            self.test_v4l2_button.setToolTip(test_tooltip)
            v4l2_buttons_layout.addWidget(self.test_v4l2_button)

            v4l2_buttons_layout.addStretch()
            v4l2_layout.addRow("", v4l2_buttons_layout)

            self.v4l2_group.setLayout(v4l2_layout)
            layout.addWidget(self.v4l2_group)
        else:
            # На Windows создаем заглушки для совместимости
            self.v4l2_enabled_check = None
            self.v4l2_device_edit = None
            self.v4l2_size_label = None
            self.v4l2_fps_label = None
            self.v4l2_buffer_spin = None
            self.v4l2_no_playback_check = None
            self.setup_v4l2_button = None
            self.test_v4l2_button = None

        # Кнопки
        buttons_layout = QHBoxLayout()

        start_text = self.localization_manager.tr("camera_settings.start_camera")
        start_tooltip = self.localization_manager.tr("camera_settings.start_camera_tooltip")
        save_text = self.localization_manager.tr("camera_settings.save_settings")
        save_tooltip = self.localization_manager.tr("camera_settings.save_settings_tooltip")
        cancel_text = self.localization_manager.tr("camera_settings.cancel")
        cancel_tooltip = self.localization_manager.tr("camera_settings.cancel_tooltip")

        self.start_camera_button = QPushButton(start_text)
        self.start_camera_button.setToolTip(start_tooltip)
        self.start_camera_button.clicked.connect(self._start_camera)
        self.start_camera_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)

        self.save_button = QPushButton(save_text)
        self.save_button.setToolTip(save_tooltip)
        self.save_button.clicked.connect(self._save_settings)

        self.cancel_button = QPushButton(cancel_text)
        self.cancel_button.setToolTip(cancel_tooltip)
        self.cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(self.start_camera_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def _refresh_camera_list(self):
        """Обновляет список камер для текущего устройства"""
        if not self.device_id:
            title = self.localization_manager.tr("camera_messages.warning")
            message = self.localization_manager.tr("camera_messages.no_device_selected")

            QMessageBox.warning(self, title, message)
            return

        # Показываем индикатор загрузки
        loading_text = self.localization_manager.tr("camera_settings.loading")
        self.refresh_cameras_button.setText(loading_text)
        self.refresh_cameras_button.setEnabled(False)

        # Запускаем в отдельном потоке
        thread = threading.Thread(target=self._load_camera_data)
        thread.daemon = True
        thread.start()

    def _load_camera_data(self):
        """Загружает данные о камерах в отдельном потоке"""
        try:
            from core.adb_manager import AdbManager
            adb_manager = AdbManager()

            # Получаем список камер
            cameras = adb_manager.get_cameras(self.device_id)

            # Обновляем UI в главном потоке
            self.camera_id_combo.clear()
            not_selected_text = self.localization_manager.tr("camera_settings.not_selected")
            self.camera_id_combo.addItem(not_selected_text, "")

            for camera in cameras:
                self.camera_id_combo.addItem(camera['description'], camera['id'])

            # Применяем сохранённую камеру, если есть
            saved_camera = (
                self.current_settings.get('camera', {}) if isinstance(self.current_settings, dict) else {}).get(
                'camera_id', '')
            applied_saved = False
            if saved_camera:
                for i in range(self.camera_id_combo.count()):
                    if self.camera_id_combo.itemData(i) == saved_camera:
                        self.camera_id_combo.setCurrentIndex(i)
                        applied_saved = True
                        break

            # Если сохранённой нет, автоматически выбираем заднюю камеру
            if not applied_saved:
                back_camera_found = False
                for i in range(self.camera_id_combo.count()):
                    camera_data = self.camera_id_combo.itemData(i)
                    if camera_data:
                        # Находим камеру с типом "back"
                        for camera in cameras:
                            if camera['id'] == camera_data and camera.get('type') == 'back':
                                self.camera_id_combo.setCurrentIndex(i)
                                back_camera_found = True
                                break
                        if back_camera_found:
                            break
                # Если задняя камера не найдена, выбираем первую доступную
                if not back_camera_found and self.camera_id_combo.count() > 1:
                    self.camera_id_combo.setCurrentIndex(1)  # Пропускаем "Не выбрано"

            # Сбрасываем связанные поля
            self.camera_size_combo.clear()
            self.camera_fps_combo.clear()

            # Восстанавливаем кнопку
            refresh_text = self.localization_manager.tr("camera_settings.refresh_cameras")
            self.refresh_cameras_button.setText(refresh_text)
            self.refresh_cameras_button.setEnabled(True)

        except Exception as e:
            debug_print(f"⚠️ Error loading cameras: {e}")
            refresh_text = self.localization_manager.tr("camera_settings.refresh_cameras")
            self.refresh_cameras_button.setText(refresh_text)
            self.refresh_cameras_button.setEnabled(True)

    def _on_camera_id_changed(self, text):
        """Обработчик изменения ID камеры"""
        camera_id = self.camera_id_combo.currentData()
        if not camera_id or not self.device_id:
            self.camera_size_combo.clear()
            self.camera_fps_combo.clear()
            return

        # Загружаем размеры и FPS для выбранной камеры
        self._load_camera_details(camera_id)

        # Проверяем совместимость с V4L2 если V4L2 включен
        if self.v4l2_enabled_check and self.v4l2_enabled_check.isChecked():
            self._check_camera_v4l2_compatibility(camera_id)

    def _load_camera_details(self, camera_id):
        """Загружает детали камеры (размеры и FPS)"""
        try:
            from core.adb_manager import AdbManager
            adb_manager = AdbManager()

            # Получаем размеры камеры
            sizes = adb_manager.get_camera_sizes(self.device_id, camera_id)
            self.camera_size_combo.clear()
            auto_text = self.localization_manager.tr("camera_settings.automatically")
            default_text = self.localization_manager.tr("camera_settings.default")
            self.camera_size_combo.addItem(auto_text, "")
            for size in sizes:
                self.camera_size_combo.addItem(size, size)

            # Получаем FPS камеры
            fps_options = adb_manager.get_camera_fps_options(self.device_id, camera_id)
            self.camera_fps_combo.clear()
            self.camera_fps_combo.addItem(default_text, "0")
            for fps in fps_options:
                self.camera_fps_combo.addItem(f"{fps} fps", str(fps))

            # Применяем сохранённые размер и FPS (если есть), иначе выбираем максимум по FPS
            saved = (self.current_settings.get('camera', {}) if isinstance(self.current_settings, dict) else {})
            saved_size = saved.get('camera_size', '')
            saved_fps = saved.get('camera_fps', 0)

            if saved_size:
                # Пытаемся выставить сохранённый размер
                for i in range(self.camera_size_combo.count()):
                    if self.camera_size_combo.itemData(i) == saved_size or self.camera_size_combo.itemText(
                            i) == saved_size:
                        self.camera_size_combo.setCurrentIndex(i)
                        break

            if saved_fps and str(saved_fps) in [self.camera_fps_combo.itemData(i) for i in
                                                range(self.camera_fps_combo.count())]:
                for i in range(self.camera_fps_combo.count()):
                    if self.camera_fps_combo.itemData(i) == str(saved_fps):
                        self.camera_fps_combo.setCurrentIndex(i)
                        break
            else:
                # Автоматически выбираем максимальный FPS
                if fps_options:
                    max_fps = max(fps_options)
                    for i in range(self.camera_fps_combo.count()):
                        if self.camera_fps_combo.itemData(i) == str(max_fps):
                            self.camera_fps_combo.setCurrentIndex(i)
                            break

        except Exception as e:
            debug_print(f"⚠️ Error loading camera details: {e}")

    def load_settings(self):
        """Загружает текущие настройки"""
        camera = self.current_settings.get('camera', {})

        # Загружаем настройки камеры
        camera_id = camera.get('camera_id', '')
        if camera_id:
            # Ищем камеру в списке
            for i in range(self.camera_id_combo.count()):
                if self.camera_id_combo.itemData(i) == camera_id:
                    self.camera_id_combo.setCurrentIndex(i)
                    break

        camera_size = camera.get('camera_size', '')
        if camera_size:
            self.camera_size_combo.setCurrentText(camera_size)

        camera_fps = camera.get('camera_fps', 0)
        if camera_fps > 0:
            self.camera_fps_combo.setCurrentText(f"{camera_fps} fps")

        # Дополнительные настройки камеры
        self.camera_ar_combo.setCurrentText(camera.get('camera_ar', ''))
        self.camera_high_speed_check.setChecked(camera.get('camera_high_speed', False))
        self.camera_no_audio_check.setChecked(camera.get('camera_no_audio', False))  # По умолчанию False

        # Настройки отображения
        display = self.current_settings.get('display', {})
        rotation_map = {0: 0, 90: 1, 180: 2, 270: 3}
        self.rotation_combo.setCurrentIndex(rotation_map.get(display.get('rotation', 0), 0))
        self.crop_edit.setText(display.get('crop', ''))
        self.fullscreen_check.setChecked(display.get('fullscreen', False))
        self.always_on_top_check.setChecked(display.get('always_on_top', False))
        self.flip_check.setChecked(display.get('flip', False))

        # V4L2 настройки (только для Linux)
        if self.v4l2_enabled_check is not None:
            v4l2 = self.current_settings.get('v4l2', {})
            self.v4l2_enabled_check.setChecked(v4l2.get('enabled', False))
            self.v4l2_device_edit.setText(v4l2.get('device', '/dev/video0'))
            self.v4l2_buffer_spin.setValue(v4l2.get('buffers', 3))
            self.v4l2_no_playback_check.setChecked(v4l2.get('no_playback', True))

        # Автоматически загружаем камеры при открытии
        if self.device_id:
            self._refresh_camera_list()

    def get_settings(self) -> dict:
        """Получает текущие настройки из интерфейса"""
        rotation_map = {0: 0, 1: 90, 2: 180, 3: 270}
        settings = {
            'camera': {
                'camera_id': self.camera_id_combo.currentData() if self.camera_id_combo.currentData() else '',
                'camera_size': self.camera_size_combo.currentText() if self.camera_size_combo.currentText() and self.camera_size_combo.currentText() != 'Автоматически' else '',
                'camera_fps': int(self.camera_fps_combo.currentData()) if self.camera_fps_combo.currentData() else 0,
                'camera_ar': self.camera_ar_combo.currentText() if self.camera_ar_combo.currentText() and self.camera_ar_combo.currentText() != 'Автоматически' else '',
                'camera_high_speed': self.camera_high_speed_check.isChecked(),
                'camera_no_audio': self.camera_no_audio_check.isChecked()
            },
            'display': {
                'rotation': rotation_map[self.rotation_combo.currentIndex()],
                'crop': self.crop_edit.text(),
                'fullscreen': self.fullscreen_check.isChecked(),
                'always_on_top': self.always_on_top_check.isChecked(),
                'flip': self.flip_check.isChecked()
            },
            'v4l2': {
                'enabled': self.v4l2_enabled_check.isChecked() if self.v4l2_enabled_check else False,
                'device': self.v4l2_device_edit.text() or '/dev/video0' if self.v4l2_device_edit else '/dev/video0',
                'buffers': self.v4l2_buffer_spin.value() if self.v4l2_buffer_spin else 3,
                'no_playback': self.v4l2_no_playback_check.isChecked() if self.v4l2_no_playback_check else True
            }
        }
        debug_print(f"🔧 Camera settings: {settings}")
        return settings

    def _save_settings(self):
        """Сохраняет настройки"""
        settings = self.get_settings()
        self.settings_changed.emit(settings)
        title = self.localization_manager.tr("camera_messages.success")
        message = self.localization_manager.tr("camera_messages.settings_saved")
        QMessageBox.information(self, title, message)

    def _start_camera(self):
        """Запускает камеру с текущими настройками"""
        # Проверяем, что камера выбрана
        camera_id = self.camera_id_combo.currentData()
        if not camera_id:
            title = self.localization_manager.tr("camera_messages.error")
            message = self.localization_manager.tr("camera_messages.select_camera_first")
            QMessageBox.warning(self, title, message)
            return

        settings = self.get_settings()
        self.start_camera.emit(settings)
        self.accept()

    def _setup_v4l2(self):
        """Настраивает V4L2 устройство"""
        if self.v4l2_enabled_check is None:
            title = self.localization_manager.tr("camera_messages.error")
            message = self.localization_manager.tr("camera_messages.v4l2_unavailable_windows")
            QMessageBox.warning(self, title, message)
            return

        if not self.v4l2_enabled_check or not self.v4l2_enabled_check.isChecked():
            title = self.localization_manager.tr("camera_messages.error")
            message = self.localization_manager.tr("camera_messages.v4l2_not_enabled")
            QMessageBox.warning(self, title, message)
            return

        device = self.v4l2_device_edit.text().strip()
        if not device:
            device = "/dev/video0"

        # Запрашиваем пароль sudo
        title = self.localization_manager.tr("camera_messages.sudo_password")
        message = self.localization_manager.tr("camera_messages.enter_sudo_password")

        password, ok = QInputDialog.getText(
            self,
            title,
            message,
            QLineEdit.Password
        )

        if not ok or not password:
            return

        try:
            # Создаем V4L2 loopback устройство с параметрами для совместимости с OBS
            cmd = f"echo '{password}' | sudo -S modprobe v4l2loopback exclusive_caps=1"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                title = self.localization_manager.tr("camera_messages.error")
                message = self.localization_manager.tr("camera_messages.v4l2_module_error", error=result.stderr)
                QMessageBox.warning(self, title, message)
                return

            # Проверяем, что модуль загружен
            cmd = "lsmod | grep v4l2loopback"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if "v4l2loopback" not in result.stdout:
                title = self.localization_manager.tr("camera_messages.error")
                message = self.localization_manager.tr("camera_messages.v4l2_module_not_loaded")
                QMessageBox.warning(self, title, message)
                return

            # Проверяем доступные V4L2 устройства
            cmd = "ls /dev/video*"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                title = self.localization_manager.tr("camera_messages.error")
                message = self.localization_manager.tr("camera_messages.v4l2_devices_not_found")
                QMessageBox.warning(self, title, message)
                return

            # Показываем информацию о доступных устройствах
            devices = result.stdout.strip().split('\n')
            device_info = f"{self.localization_manager.tr('camera_messages.available_v4l2_devices')}:\n{chr(10).join(devices)}"

            title = self.localization_manager.tr("camera_messages.success")
            message = self.localization_manager.tr("camera_messages.v4l2_setup_success",
                                                   devices=device_info, device=device)
            QMessageBox.information(self, title, message)

        except Exception as e:
            title = self.localization_manager.tr("camera_messages.error")
            message = self.localization_manager.tr("camera_messages.v4l2_setup_error", error=str(e))
            QMessageBox.critical(self, title, message)

    def _test_v4l2(self):
        """Тестирует V4L2 устройство"""
        if self.v4l2_enabled_check is None:
            title = self.localization_manager.tr("camera_messages.error")
            message = self.localization_manager.tr("camera_messages.v4l2_unavailable_windows")
            QMessageBox.warning(self, title, message)
            return

        if not self.v4l2_enabled_check or not self.v4l2_enabled_check.isChecked():
            title = self.localization_manager.tr("camera_messages.error")
            message = self.localization_manager.tr("camera_messages.v4l2_not_enabled")
            QMessageBox.warning(self, title, message)
            return

        device = self.v4l2_device_edit.text().strip()
        if not device:
            device = "/dev/video0"

        if not os.path.exists(device):
            title = self.localization_manager.tr("camera_messages.error")
            message = self.localization_manager.tr("camera_messages.v4l2_device_not_found", device=device)
            QMessageBox.warning(self, title, message)
            return

        try:
            # Проверяем, доступно ли устройство
            cmd = f"v4l2-ctl --device={device} --list-formats-ext"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                title = self.localization_manager.tr("camera_messages.error")
                message = self.localization_manager.tr("camera_messages.v4l2_test_error", error=result.stderr)
                QMessageBox.warning(self, title, message)
                return

            # Показываем информацию об устройстве
            title = self.localization_manager.tr("camera_messages.v4l2_test_title")
            message = self.localization_manager.tr("camera_messages.v4l2_test_success",
                                                   device=device, formats=result.stdout)
            QMessageBox.information(self, title, message)

        except Exception as e:
            title = self.localization_manager.tr("camera_messages.error")
            message = self.localization_manager.tr("camera_messages.v4l2_test_error_general", error=str(e))
            QMessageBox.critical(self, title, message)

    def _check_v4l2_requirements(self):
        """Проверяет требования для V4L2"""
        try:
            # Проверяем наличие v4l2loopback
            result = subprocess.run("modinfo v4l2loopback", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                return False, self.localization_manager.tr("camera_messages.v4l2_module_not_found")

            # Проверяем наличие v4l2loopback-ctl
            result = subprocess.run("which v4l2loopback-ctl", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                return False, self.localization_manager.tr("camera_messages.v4l2_ctl_not_found")

            # Проверяем наличие v4l2-ctl
            result = subprocess.run("which v4l2-ctl", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                return False, self.localization_manager.tr("camera_messages.v4l2_utils_not_found")

            return True, self.localization_manager.tr("camera_messages.v4l2_requirements_met")

        except Exception as e:
            return False, self.localization_manager.tr("camera_messages.v4l2_check_error", error=str(e))

    def _on_v4l2_enabled_changed(self, enabled):
        """Обрабатывает изменение состояния чекбокса V4L2"""
        if self.v4l2_enabled_check is None:
            return  # V4L2 недоступен на Windows

        self._update_v4l2_fields_state()

        if enabled:
            # Проверяем требования при включении
            success, message = self._check_v4l2_requirements()
            if not success:
                QMessageBox.warning(self,
                                    self.localization_manager.tr("camera_messages.v4l2_unavailable_title"),
                                    self.localization_manager.tr("camera_messages.v4l2_enable_failed", message=message))
                if self.v4l2_enabled_check:
                    self.v4l2_enabled_check.setChecked(False)
                self._update_v4l2_fields_state()
            else:
                # Если V4L2 успешно включен, проверяем совместимость с текущей камерой
                camera_id = self.camera_id_combo.currentData()
                if camera_id:
                    self._check_camera_v4l2_compatibility(camera_id)

    def _update_v4l2_fields_state(self):
        """Обновляет состояние полей V4L2 в зависимости от чекбокса"""
        if self.v4l2_enabled_check is None:
            return  # V4L2 недоступен на Windows

        enabled = self.v4l2_enabled_check.isChecked() if self.v4l2_enabled_check else False

        # Управляем доступностью полей
        if self.v4l2_device_edit:
            self.v4l2_device_edit.setEnabled(enabled)
        if self.v4l2_buffer_spin:
            self.v4l2_buffer_spin.setEnabled(enabled)
        if self.v4l2_no_playback_check:
            self.v4l2_no_playback_check.setEnabled(enabled)
        if self.setup_v4l2_button:
            self.setup_v4l2_button.setEnabled(enabled)
        if self.test_v4l2_button:
            self.test_v4l2_button.setEnabled(enabled)

        # Визуальная индикация состояния
        if enabled:
            if self.v4l2_device_edit:
                self.v4l2_device_edit.setStyleSheet("")
            if self.v4l2_buffer_spin:
                self.v4l2_buffer_spin.setStyleSheet("")
        else:
            # Серый цвет для отключенных полей
            disabled_style = "background-color: #f0f0f0; color: #999999;"
            if self.v4l2_device_edit:
                self.v4l2_device_edit.setStyleSheet(disabled_style)
            if self.v4l2_buffer_spin:
                self.v4l2_buffer_spin.setStyleSheet(disabled_style)

    def _check_camera_v4l2_compatibility(self, camera_id):
        """Проверяет совместимость камеры с V4L2"""
        try:
            # Получаем информацию о камере
            from core.adb_manager import AdbManager
            adb_manager = AdbManager()
            cameras = adb_manager.get_cameras(self.device_id)

            camera_info = None
            for camera in cameras:
                if camera['id'] == camera_id:
                    camera_info = camera
                    break

            if not camera_info:
                return

            # Проверяем, является ли камера фронтальной
            camera_type = camera_info.get('type', '').lower()
            if 'front' in camera_type or 'selfie' in camera_type:
                QMessageBox.warning(
                    self,
                    self.localization_manager.tr("camera_messages.v4l2_front_camera_warning_title"),
                    self.localization_manager.tr("camera_messages.v4l2_front_camera_warning", camera_id=camera_id)
                )
                return

            # Проверяем разрешение камеры
            max_resolution = camera_info.get('max_resolution', '')
            if max_resolution:
                try:
                    width, height = map(int, max_resolution.split('x'))
                    # Если разрешение слишком маленькое, предупреждаем
                    if width < 1280 or height < 720:
                        QMessageBox.warning(
                            self,
                            self.localization_manager.tr("camera_messages.v4l2_low_resolution_warning_title"),
                            self.localization_manager.tr("camera_messages.v4l2_low_resolution_warning",
                                                         camera_id=camera_id, resolution=max_resolution)
                        )
                        return
                except (ValueError, IndexError):
                    pass

            # Если камера выглядит совместимой, показываем информационное сообщение
            title = self.localization_manager.tr("camera_messages.v4l2_compatibility_title")
            message = self.localization_manager.tr("camera_messages.v4l2_compatibility_success",
                                                   camera_id=camera_id,
                                                   type=camera_info.get('type', 'Неизвестно'),
                                                   resolution=camera_info.get('max_resolution', 'Неизвестно'))
            QMessageBox.information(self, title, message)

        except Exception as e:
            debug_print(f"⚠️ Error checking V4L2 compatibility: {e}")
            # Не показываем ошибку пользователю, так как это не критично
