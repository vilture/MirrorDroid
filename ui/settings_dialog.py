import os

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QLabel, QLineEdit, QSpinBox, QComboBox,
                             QCheckBox, QPushButton, QGroupBox, QFormLayout,
                             QFileDialog, QRadioButton, QButtonGroup)

from core.utils import get_icon_path


class SettingsDialog(QDialog):
    """Диалог настроек scrcpy"""

    settings_changed = pyqtSignal(dict)  # новые настройки
    language_changed = pyqtSignal(str)  # изменение языка

    def __init__(self, current_settings: dict = None, parent=None, localization_manager=None):
        super().__init__(parent)
        self.current_settings = current_settings or {}
        self.localization_manager = localization_manager
        self.init_ui()
        self.load_settings()

        # Подключаем сигнал смены языка (для будущего использования)
        self.localization_manager.language_changed.connect(self.on_language_changed)

    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle(self.localization_manager.tr("settings"))
        self.setModal(True)
        self.resize(600, 500)

        # Устанавливаем иконку окна
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout()

        # Создаем табы для разных категорий настроек
        self.tab_widget = QTabWidget()

        # Видео настройки
        self.video_tab = self._create_video_tab()
        video_title = self.localization_manager.tr("settings_tabs.video")
        self.tab_widget.addTab(self.video_tab, video_title)

        # Аудио настройки
        self.audio_tab = self._create_audio_tab()
        audio_title = self.localization_manager.tr("settings_tabs.audio")
        self.tab_widget.addTab(self.audio_tab, audio_title)

        # Настройки отображения
        self.display_tab = self._create_display_tab()
        display_title = self.localization_manager.tr("settings_tabs.display")
        self.tab_widget.addTab(self.display_tab, display_title)

        # Настройки управления
        self.control_tab = self._create_control_tab()
        control_title = self.localization_manager.tr("settings_tabs.control")
        self.tab_widget.addTab(self.control_tab, control_title)

        # Настройки записи
        self.record_tab = self._create_record_tab()
        record_title = self.localization_manager.tr("settings_tabs.record")
        self.tab_widget.addTab(self.record_tab, record_title)

        # Дополнительные настройки
        self.advanced_tab = self._create_advanced_tab()
        advanced_title = self.localization_manager.tr("settings_tabs.advanced")
        self.tab_widget.addTab(self.advanced_tab, advanced_title)

        # Памятка по горячим клавишам
        self.shortcuts_tab = self._create_shortcuts_tab()
        shortcuts_title = self.localization_manager.tr("settings_tabs.shortcuts")
        self.tab_widget.addTab(self.shortcuts_tab, shortcuts_title)

        # Настройки языка
        self.language_tab = self._create_language_tab()
        language_title = self.localization_manager.tr("settings_tabs.language")
        self.tab_widget.addTab(self.language_tab, language_title)

        layout.addWidget(self.tab_widget)

        # Кнопки
        buttons_layout = QHBoxLayout()

        reset_text = self.localization_manager.tr("buttons.reset")
        self.reset_button = QPushButton(reset_text)
        self.reset_button.clicked.connect(self.reset_settings)
        buttons_layout.addWidget(self.reset_button)

        buttons_layout.addStretch()

        cancel_text = self.localization_manager.tr("buttons.cancel")
        self.cancel_button = QPushButton(cancel_text)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        ok_text = self.localization_manager.tr("buttons.ok")
        self.ok_button = QPushButton(ok_text)
        self.ok_button.clicked.connect(self.accept_settings)
        buttons_layout.addWidget(self.ok_button)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def _create_video_tab(self) -> QWidget:
        """Создает таб с настройками видео"""
        widget = QWidget()
        layout = QFormLayout()

        # Максимальный размер
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(0, 4096)
        self.max_size_spin.setSuffix(self.localization_manager.tr("units.px"))
        self.max_size_spin.setSpecialValueText(self.localization_manager.tr("main_settings.video.unlimited"))
        self.max_size_spin.setToolTip(self.localization_manager.tr("main_settings.video.max_size_tooltip"))
        max_size_label = self.localization_manager.tr("main_settings.video.max_size")
        layout.addRow(max_size_label, self.max_size_spin)

        # Битрейт
        self.bit_rate_spin = QSpinBox()
        self.bit_rate_spin.setRange(0, 100000000)
        self.bit_rate_spin.setSuffix(self.localization_manager.tr("units.bps"))
        self.bit_rate_spin.setToolTip(self.localization_manager.tr("main_settings.video.bit_rate_tooltip"))
        bit_rate_label = self.localization_manager.tr("main_settings.video.bit_rate")
        layout.addRow(bit_rate_label, self.bit_rate_spin)

        # Максимальный FPS
        self.max_fps_spin = QSpinBox()
        self.max_fps_spin.setRange(0, 120)
        self.max_fps_spin.setSuffix(self.localization_manager.tr("units.fps"))
        self.max_fps_spin.setSpecialValueText(self.localization_manager.tr("main_settings.video.unlimited"))
        self.max_fps_spin.setToolTip(self.localization_manager.tr("main_settings.video.max_fps_tooltip"))
        max_fps_label = self.localization_manager.tr("main_settings.video.max_fps")
        layout.addRow(max_fps_label, self.max_fps_spin)

        # Кодек
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["h264", "h265", "av1"])
        self.codec_combo.setToolTip(self.localization_manager.tr("main_settings.video.codec_tooltip"))
        codec_label = self.localization_manager.tr("main_settings.video.codec")
        layout.addRow(codec_label, self.codec_combo)

        # Энкодер
        self.encoder_edit = QLineEdit()
        self.encoder_edit.setPlaceholderText(self.localization_manager.tr("main_settings.video.encoder_placeholder"))
        self.encoder_edit.setToolTip(self.localization_manager.tr("main_settings.video.encoder_tooltip"))
        encoder_label = self.localization_manager.tr("main_settings.video.encoder")
        layout.addRow(encoder_label, self.encoder_edit)

        widget.setLayout(layout)
        return widget

    def _create_audio_tab(self) -> QWidget:
        """Создает таб с настройками аудио"""
        widget = QWidget()
        layout = QFormLayout()

        # Кодек аудио
        self.audio_codec_combo = QComboBox()
        self.audio_codec_combo.addItems(["opus", "aac", "raw"])
        self.audio_codec_combo.setToolTip(self.localization_manager.tr("main_settings.audio.codec_tooltip"))
        codec_label = self.localization_manager.tr("main_settings.audio.codec")
        layout.addRow(codec_label, self.audio_codec_combo)

        # Битрейт аудио
        self.audio_bit_rate_spin = QSpinBox()
        self.audio_bit_rate_spin.setRange(0, 1000000)
        self.audio_bit_rate_spin.setSuffix(self.localization_manager.tr("units.bps"))
        self.audio_bit_rate_spin.setToolTip(self.localization_manager.tr("main_settings.audio.bit_rate_tooltip"))
        bit_rate_label = self.localization_manager.tr("main_settings.audio.bit_rate")
        layout.addRow(bit_rate_label, self.audio_bit_rate_spin)

        # Размер буфера
        self.audio_buffer_spin = QSpinBox()
        self.audio_buffer_spin.setRange(0, 10000)
        self.audio_buffer_spin.setSuffix(self.localization_manager.tr("units.ms"))
        self.audio_buffer_spin.setToolTip(self.localization_manager.tr("main_settings.audio.buffer_size_tooltip"))
        self.audio_buffer_spin.setSpecialValueText(self.localization_manager.tr("main_settings.audio.default"))
        buffer_label = self.localization_manager.tr("main_settings.audio.buffer_size")
        layout.addRow(buffer_label, self.audio_buffer_spin)

        # Отключение звука
        self.audio_disable_check = QCheckBox()
        self.audio_disable_check.setToolTip(self.localization_manager.tr("main_settings.audio.disable_audio_tooltip"))
        disable_audio_label = self.localization_manager.tr("main_settings.audio.disable_audio")
        layout.addRow(disable_audio_label, self.audio_disable_check)

        widget.setLayout(layout)
        return widget

    def _create_display_tab(self) -> QWidget:
        """Создает таб с настройками отображения"""
        widget = QWidget()
        layout = QFormLayout()

        # Поворот
        self.rotation_combo = QComboBox()
        self.rotation_combo.addItems(["0°", "90°", "180°", "270°"])
        self.rotation_combo.setToolTip(self.localization_manager.tr("main_settings.display.rotation_tooltip"))
        rotation_label = self.localization_manager.tr("main_settings.display.rotation")
        layout.addRow(rotation_label, self.rotation_combo)

        # Обрезка
        self.crop_edit = QLineEdit()
        self.crop_edit.setPlaceholderText(self.localization_manager.tr("main_settings.display.crop_placeholder"))
        self.crop_edit.setToolTip(self.localization_manager.tr("main_settings.display.crop_tooltip"))
        crop_label = self.localization_manager.tr("main_settings.display.crop")
        layout.addRow(crop_label, self.crop_edit)

        # Полноэкранный режим
        self.fullscreen_check = QCheckBox()
        self.fullscreen_check.setToolTip(self.localization_manager.tr("main_settings.display.fullscreen_tooltip"))
        fullscreen_label = self.localization_manager.tr("main_settings.display.fullscreen")
        layout.addRow(fullscreen_label, self.fullscreen_check)

        # Поверх всех окон
        self.always_on_top_check = QCheckBox()
        self.always_on_top_check.setToolTip(self.localization_manager.tr("main_settings.display.always_on_top_tooltip"))
        always_on_top_label = self.localization_manager.tr("main_settings.display.always_on_top")
        layout.addRow(always_on_top_label, self.always_on_top_check)

        # Заголовок окна
        self.window_title_edit = QLineEdit()
        self.window_title_edit.setPlaceholderText(
            self.localization_manager.tr("main_settings.display.window_title_placeholder"))
        self.window_title_edit.setToolTip(self.localization_manager.tr("main_settings.display.window_title_tooltip"))
        window_title_label = self.localization_manager.tr("main_settings.display.window_title")
        layout.addRow(window_title_label, self.window_title_edit)

        widget.setLayout(layout)
        return widget

    def _create_control_tab(self) -> QWidget:
        """Создает таб с настройками управления"""
        widget = QWidget()
        layout = QFormLayout()

        # Показывать касания
        self.show_touches_check = QCheckBox()
        self.show_touches_check.setToolTip(self.localization_manager.tr("main_settings.control.show_touches_tooltip"))
        show_touches_label = self.localization_manager.tr("main_settings.control.show_touches")
        layout.addRow(show_touches_label, self.show_touches_check)

        # Не выключать экран
        self.stay_awake_check = QCheckBox()
        self.stay_awake_check.setToolTip(self.localization_manager.tr("main_settings.control.stay_awake_tooltip"))
        stay_awake_label = self.localization_manager.tr("main_settings.control.stay_awake")
        layout.addRow(stay_awake_label, self.stay_awake_check)

        # Выключить экран при запуске
        self.turn_screen_off_check = QCheckBox()
        self.turn_screen_off_check.setToolTip(
            self.localization_manager.tr("main_settings.control.turn_screen_off_tooltip"))
        turn_screen_off_label = self.localization_manager.tr("main_settings.control.turn_screen_off")
        layout.addRow(turn_screen_off_label, self.turn_screen_off_check)

        # Разделитель
        separator = QLabel("─" * 50)
        separator.setStyleSheet("color: #ccc; margin: 10px 0;")
        layout.addRow(separator)

        # Заголовок для устройств ввода
        input_title_text = self.localization_manager.tr("main_settings.control.input_devices")
        input_title = QLabel(input_title_text)
        input_title.setStyleSheet("font-weight: bold; color: #333; margin: 5px 0;")
        layout.addRow(input_title)

        # Клавиатура
        self.keyboard_combo = QComboBox()
        self.keyboard_combo.addItem(self.localization_manager.tr("main_settings.control.keyboard_disabled"), "disabled")
        self.keyboard_combo.addItem(self.localization_manager.tr("main_settings.control.keyboard_aoa"), "aoa")
        self.keyboard_combo.addItem(self.localization_manager.tr("main_settings.control.keyboard_hid"), "uhid")
        self.keyboard_combo.addItem(self.localization_manager.tr("main_settings.control.keyboard_sdk"), "sdk")
        self.keyboard_combo.setToolTip(self.localization_manager.tr("main_settings.control.keyboard_tooltip"))
        keyboard_label = self.localization_manager.tr("main_settings.control.keyboard")
        layout.addRow(keyboard_label, self.keyboard_combo)

        # Мышь
        self.mouse_combo = QComboBox()
        self.mouse_combo.addItem(self.localization_manager.tr("main_settings.control.mouse_disabled"), "disabled")
        self.mouse_combo.addItem(self.localization_manager.tr("main_settings.control.mouse_aoa"), "aoa")
        self.mouse_combo.addItem(self.localization_manager.tr("main_settings.control.mouse_hid"), "uhid")
        self.mouse_combo.addItem(self.localization_manager.tr("main_settings.control.mouse_sdk"), "sdk")
        self.mouse_combo.setToolTip(self.localization_manager.tr("main_settings.control.mouse_tooltip"))
        mouse_label = self.localization_manager.tr("main_settings.control.mouse")
        layout.addRow(mouse_label, self.mouse_combo)

        # Геймпад
        self.gamepad_check = QCheckBox()
        self.gamepad_check.setToolTip(self.localization_manager.tr("main_settings.control.gamepad_tooltip"))
        gamepad_label = self.localization_manager.tr("main_settings.control.gamepad")
        layout.addRow(gamepad_label, self.gamepad_check)

        # Предпочитать текст
        self.prefer_text_check = QCheckBox()
        self.prefer_text_check.setToolTip(self.localization_manager.tr("main_settings.control.prefer_text_tooltip"))
        prefer_text_label = self.localization_manager.tr("main_settings.control.prefer_text")
        layout.addRow(prefer_text_label, self.prefer_text_check)

        # Сырые события клавиатуры
        self.raw_key_events_check = QCheckBox()
        self.raw_key_events_check.setToolTip(
            self.localization_manager.tr("main_settings.control.raw_key_events_tooltip"))
        raw_key_events_label = self.localization_manager.tr("main_settings.control.raw_key_events")
        layout.addRow(raw_key_events_label, self.raw_key_events_check)

        # Отключить повторение клавиш
        self.no_key_repeat_check = QCheckBox()
        self.no_key_repeat_check.setToolTip(self.localization_manager.tr("main_settings.control.no_key_repeat_tooltip"))
        no_key_repeat_label = self.localization_manager.tr("main_settings.control.no_key_repeat")
        layout.addRow(no_key_repeat_label, self.no_key_repeat_check)

        # Пересылать все клики
        self.forward_all_clicks_check = QCheckBox()
        self.forward_all_clicks_check.setToolTip(
            self.localization_manager.tr("main_settings.control.forward_all_clicks_tooltip"))
        forward_all_clicks_label = self.localization_manager.tr("main_settings.control.forward_all_clicks")
        layout.addRow(forward_all_clicks_label, self.forward_all_clicks_check)

        # Устаревшая вставка
        self.legacy_paste_check = QCheckBox()
        self.legacy_paste_check.setToolTip(self.localization_manager.tr("main_settings.control.legacy_paste_tooltip"))
        legacy_paste_label = self.localization_manager.tr("main_settings.control.legacy_paste")
        layout.addRow(legacy_paste_label, self.legacy_paste_check)

        widget.setLayout(layout)
        return widget

    def _create_record_tab(self) -> QWidget:
        """Создает таб с настройками записи"""
        widget = QWidget()
        layout = QFormLayout()

        # Чекбокс для включения записи
        enable_record_text = self.localization_manager.tr("main_settings.record.enable")
        enable_record_tooltip = self.localization_manager.tr("main_settings.record.enable_tooltip")
        self.enable_record_check = QCheckBox(enable_record_text)
        self.enable_record_check.setToolTip(enable_record_tooltip)
        self.enable_record_check.toggled.connect(self._on_record_enabled_changed)
        layout.addRow(self.enable_record_check)

        # Файл записи
        record_layout = QHBoxLayout()
        self.record_file_edit = QLineEdit()
        self.record_file_edit.setPlaceholderText(self.localization_manager.tr("main_settings.record.file_placeholder"))
        self.record_file_edit.setToolTip(self.localization_manager.tr("main_settings.record.file_tooltip"))
        file_label = self.localization_manager.tr("main_settings.record.file")
        browse_text = self.localization_manager.tr("main_settings.record.browse")
        record_layout.addWidget(self.record_file_edit)

        self.record_file_button = QPushButton(browse_text)
        self.record_file_button.clicked.connect(self._select_record_file)
        record_layout.addWidget(self.record_file_button)

        layout.addRow(file_label, record_layout)

        # Формат записи
        self.record_format_combo = QComboBox()
        self.record_format_combo.addItems(["mp4", "mkv"])
        self.record_format_combo.setToolTip(self.localization_manager.tr("main_settings.record.format_tooltip"))
        format_label = self.localization_manager.tr("main_settings.record.format")
        layout.addRow(format_label, self.record_format_combo)

        # Ограничение времени
        self.time_limit_spin = QSpinBox()
        self.time_limit_spin.setRange(0, 3600)
        self.time_limit_spin.setSuffix(self.localization_manager.tr("units.sec"))
        self.time_limit_spin.setSpecialValueText(self.localization_manager.tr("main_settings.record.unlimited"))
        self.time_limit_spin.setToolTip(self.localization_manager.tr("main_settings.record.time_limit_tooltip"))
        time_limit_label = self.localization_manager.tr("main_settings.record.time_limit")
        layout.addRow(time_limit_label, self.time_limit_spin)

        # Изначально отключаем поля записи
        self._update_record_fields_state()

        widget.setLayout(layout)
        return widget

    def _create_advanced_tab(self) -> QWidget:
        """Создает таб с дополнительными настройками"""
        widget = QWidget()
        layout = QFormLayout()

        # OTG
        self.otg_check = QCheckBox()
        self.otg_check.setToolTip(self.localization_manager.tr("main_settings.advanced.otg_tooltip"))
        otg_label = self.localization_manager.tr("main_settings.advanced.otg")
        layout.addRow(otg_label, self.otg_check)

        # Отключить хранитель экрана
        self.disable_screensaver_check = QCheckBox()
        self.disable_screensaver_check.setToolTip(
            self.localization_manager.tr("main_settings.advanced.disable_screensaver_tooltip"))
        disable_screensaver_label = self.localization_manager.tr("main_settings.advanced.disable_screensaver")
        layout.addRow(disable_screensaver_label, self.disable_screensaver_check)

        # Выключить при закрытии
        self.power_off_on_close_check = QCheckBox()
        self.power_off_on_close_check.setToolTip(
            self.localization_manager.tr("main_settings.advanced.power_off_on_close_tooltip"))
        power_off_on_close_label = self.localization_manager.tr("main_settings.advanced.power_off_on_close")
        layout.addRow(power_off_on_close_label, self.power_off_on_close_check)

        # Включить при запуске
        self.power_on_check = QCheckBox()
        self.power_on_check.setToolTip(self.localization_manager.tr("main_settings.advanced.power_on_tooltip"))
        power_on_label = self.localization_manager.tr("main_settings.advanced.power_on")
        layout.addRow(power_on_label, self.power_on_check)

        # Начальный FPS
        self.start_fps_spin = QSpinBox()
        self.start_fps_spin.setRange(0, 120)
        self.start_fps_spin.setSuffix(self.localization_manager.tr("units.fps"))
        self.start_fps_spin.setSpecialValueText(self.localization_manager.tr("main_settings.advanced.default"))
        self.start_fps_spin.setToolTip(self.localization_manager.tr("main_settings.advanced.start_fps_tooltip"))
        start_fps_label = self.localization_manager.tr("main_settings.advanced.start_fps")
        layout.addRow(start_fps_label, self.start_fps_spin)

        # Блокировка ориентации
        self.lock_orientation_spin = QSpinBox()
        self.lock_orientation_spin.setRange(-1, 3)
        self.lock_orientation_spin.setSpecialValueText(
            self.localization_manager.tr("main_settings.advanced.not_locked"))
        self.lock_orientation_spin.setToolTip(
            self.localization_manager.tr("main_settings.advanced.lock_orientation_tooltip"))
        lock_orientation_label = self.localization_manager.tr("main_settings.advanced.lock_orientation")
        layout.addRow(lock_orientation_label, self.lock_orientation_spin)

        # ID дисплея
        self.display_id_spin = QSpinBox()
        self.display_id_spin.setRange(0, 10)
        self.display_id_spin.setToolTip(self.localization_manager.tr("main_settings.advanced.display_id_tooltip"))
        display_id_label = self.localization_manager.tr("main_settings.advanced.display_id")
        layout.addRow(display_id_label, self.display_id_spin)

        # TCP/IP
        self.tcpip_edit = QLineEdit()
        self.tcpip_edit.setPlaceholderText(self.localization_manager.tr("main_settings.advanced.tcpip_placeholder"))
        self.tcpip_edit.setToolTip(self.localization_manager.tr("main_settings.advanced.tcpip_tooltip"))
        tcpip_label = self.localization_manager.tr("main_settings.advanced.tcpip")
        layout.addRow(tcpip_label, self.tcpip_edit)

        # Выбрать USB
        self.select_usb_check = QCheckBox()
        self.select_usb_check.setToolTip(self.localization_manager.tr("main_settings.advanced.select_usb_tooltip"))
        select_usb_label = self.localization_manager.tr("main_settings.advanced.select_usb")
        layout.addRow(select_usb_label, self.select_usb_check)

        # Выбрать TCP/IP
        self.select_tcpip_check = QCheckBox()
        self.select_tcpip_check.setToolTip(self.localization_manager.tr("main_settings.advanced.select_tcpip_tooltip"))
        select_tcpip_label = self.localization_manager.tr("main_settings.advanced.select_tcpip")
        layout.addRow(select_tcpip_label, self.select_tcpip_check)

        # Модификаторы горячих клавиш
        self.shortcut_mod_edit = QLineEdit()
        self.shortcut_mod_edit.setPlaceholderText(
            self.localization_manager.tr("main_settings.advanced.shortcut_mod_placeholder"))
        self.shortcut_mod_edit.setToolTip(self.localization_manager.tr("main_settings.advanced.shortcut_mod_tooltip"))
        shortcut_mod_label = self.localization_manager.tr("main_settings.advanced.shortcut_mod")
        layout.addRow(shortcut_mod_label, self.shortcut_mod_edit)

        widget.setLayout(layout)
        return widget

    def _on_record_enabled_changed(self, enabled):
        """Обработчик изменения состояния чекбокса записи"""
        self._update_record_fields_state()

    def _update_record_fields_state(self):
        """Обновляет состояние полей записи в зависимости от чекбокса"""
        enabled = self.enable_record_check.isChecked()
        self.record_file_edit.setEnabled(enabled)
        self.record_file_button.setEnabled(enabled)
        self.record_format_combo.setEnabled(enabled)
        self.time_limit_spin.setEnabled(enabled)

    def _select_record_file(self):
        """Выбор файла для записи"""
        title = self.localization_manager.tr("main_settings.record.file")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            title,
            "",
            "MP4 файлы (*.mp4);;MKV файлы (*.mkv);;Все файлы (*)"
        )
        if file_path:
            self.record_file_edit.setText(file_path)

    def load_settings(self):
        """Загружает текущие настройки"""
        video = self.current_settings.get('video', {})
        self.max_size_spin.setValue(video.get('max_size', 0))
        self.bit_rate_spin.setValue(video.get('bit_rate', 8000000))
        self.max_fps_spin.setValue(video.get('max_fps', 0))
        self.codec_combo.setCurrentText(video.get('codec', 'h264'))
        self.encoder_edit.setText(video.get('encoder', ''))

        audio = self.current_settings.get('audio', {})
        self.audio_codec_combo.setCurrentText(audio.get('codec', 'opus'))
        self.audio_bit_rate_spin.setValue(audio.get('bit_rate', 128000))
        self.audio_buffer_spin.setValue(audio.get('buffer_size', 0))
        self.audio_disable_check.setChecked(audio.get('disable_audio', False))

        display = self.current_settings.get('display', {})
        rotation_map = {0: 0, 90: 1, 180: 2, 270: 3}
        self.rotation_combo.setCurrentIndex(rotation_map.get(display.get('rotation', 0), 0))
        self.crop_edit.setText(display.get('crop', ''))
        self.fullscreen_check.setChecked(display.get('fullscreen', False))
        self.always_on_top_check.setChecked(display.get('always_on_top', False))
        self.window_title_edit.setText(display.get('window_title', ''))

        control = self.current_settings.get('control', {})
        self.show_touches_check.setChecked(control.get('show_touches', False))
        self.stay_awake_check.setChecked(control.get('stay_awake', False))
        self.turn_screen_off_check.setChecked(control.get('turn_screen_off', False))

        # Настройки устройств ввода (из control, а не advanced)
        control_input = self.current_settings.get('control', {})
        # Маппинг старых значений (enabled/hack) к валидным (aoa/uhid)
        kb = control_input.get('keyboard', 'disabled')
        if kb == 'enabled':
            kb = 'aoa'
        elif kb == 'hack':
            kb = 'uhid'
        elif kb == 'aosp':  # Маппинг старого aosp на aoa
            kb = 'aoa'
        ms = control_input.get('mouse', 'disabled')
        if ms == 'enabled':
            ms = 'aoa'
        elif ms == 'hack':
            ms = 'uhid'
        elif ms == 'aosp':  # Маппинг старого aosp на aoa
            ms = 'aoa'

        # Устанавливаем по userData
        def set_combo_by_data(combo: QComboBox, value: str, allowed: list):
            target = value if value in allowed else 'disabled'
            for i in range(combo.count()):
                if combo.itemData(i) == target:
                    combo.setCurrentIndex(i)
                    return
            combo.setCurrentIndex(0)

        set_combo_by_data(self.keyboard_combo, kb, ['disabled', 'aoa', 'uhid', 'sdk'])
        set_combo_by_data(self.mouse_combo, ms, ['disabled', 'aoa', 'uhid', 'sdk'])
        self.gamepad_check.setChecked(control_input.get('gamepad', False))
        self.prefer_text_check.setChecked(control_input.get('prefer_text', False))
        self.raw_key_events_check.setChecked(control_input.get('raw_key_events', False))
        self.no_key_repeat_check.setChecked(control_input.get('no_key_repeat', False))
        self.forward_all_clicks_check.setChecked(control_input.get('forward_all_clicks', False))
        self.legacy_paste_check.setChecked(control_input.get('legacy_paste', False))

        record = self.current_settings.get('record', {})
        # Загружаем состояние чекбокса записи
        self.enable_record_check.setChecked(bool(record.get('file', '')))
        self.record_file_edit.setText(record.get('file', ''))
        self.record_format_combo.setCurrentText(record.get('format', 'mp4'))
        self.time_limit_spin.setValue(record.get('time_limit', 0))
        # Обновляем состояние полей
        self._update_record_fields_state()

        advanced = self.current_settings.get('advanced', {})
        self.otg_check.setChecked(advanced.get('otg', False))
        self.disable_screensaver_check.setChecked(advanced.get('disable_screensaver', False))
        self.power_off_on_close_check.setChecked(advanced.get('power_off_on_close', False))
        self.power_on_check.setChecked(advanced.get('power_on', False))
        self.start_fps_spin.setValue(advanced.get('start_fps', 0))
        self.lock_orientation_spin.setValue(advanced.get('lock_video_orientation', -1))
        self.display_id_spin.setValue(advanced.get('display_id', 0))
        self.tcpip_edit.setText(advanced.get('tcpip', ''))
        self.select_usb_check.setChecked(advanced.get('select_usb', False))
        self.select_tcpip_check.setChecked(advanced.get('select_tcpip', False))
        self.shortcut_mod_edit.setText(advanced.get('shortcut_mod', 'lctrl,lalt,lmeta'))

        # Загружаем настройки языка
        current_language = self.localization_manager.get_language()
        if current_language == "en":
            self.english_radio.setChecked(True)

    def get_settings(self) -> dict:
        """Получает текущие настройки из интерфейса"""
        rotation_map = {0: 0, 1: 90, 2: 180, 3: 270}

        return {
            'video': {
                'max_size': self.max_size_spin.value(),
                'bit_rate': self.bit_rate_spin.value(),
                'max_fps': self.max_fps_spin.value(),
                'codec': self.codec_combo.currentText(),
                'encoder': self.encoder_edit.text()
            },
            'audio': {
                'codec': self.audio_codec_combo.currentText(),
                'bit_rate': self.audio_bit_rate_spin.value(),
                'buffer_size': self.audio_buffer_spin.value(),
                'disable_audio': self.audio_disable_check.isChecked()
            },
            'display': {
                'rotation': rotation_map[self.rotation_combo.currentIndex()],
                'crop': self.crop_edit.text(),
                'fullscreen': self.fullscreen_check.isChecked(),
                'always_on_top': self.always_on_top_check.isChecked(),
                'window_title': self.window_title_edit.text()
            },
            'control': {
                'show_touches': self.show_touches_check.isChecked(),
                'stay_awake': self.stay_awake_check.isChecked(),
                'turn_screen_off': self.turn_screen_off_check.isChecked(),
                # Настройки устройств ввода
                'keyboard': self.keyboard_combo.currentData() or 'disabled',
                'mouse': self.mouse_combo.currentData() or 'disabled',
                'gamepad': self.gamepad_check.isChecked(),
                'prefer_text': self.prefer_text_check.isChecked(),
                'raw_key_events': self.raw_key_events_check.isChecked(),
                'no_key_repeat': self.no_key_repeat_check.isChecked(),
                'forward_all_clicks': self.forward_all_clicks_check.isChecked(),
                'legacy_paste': self.legacy_paste_check.isChecked()
            },
            'record': {
                'file': self.record_file_edit.text() if self.enable_record_check.isChecked() else '',
                'format': self.record_format_combo.currentText(),
                'time_limit': self.time_limit_spin.value()
            },
            'advanced': {
                'otg': self.otg_check.isChecked(),
                'disable_screensaver': self.disable_screensaver_check.isChecked(),
                'power_off_on_close': self.power_off_on_close_check.isChecked(),
                'power_on': self.power_on_check.isChecked(),
                'start_fps': self.start_fps_spin.value(),
                'lock_video_orientation': self.lock_orientation_spin.value(),
                'display_id': self.display_id_spin.value(),
                'tcpip': self.tcpip_edit.text(),
                'select_usb': self.select_usb_check.isChecked(),
                'select_tcpip': self.select_tcpip_check.isChecked(),
                'shortcut_mod': self.shortcut_mod_edit.text()
            }
        }

    def _create_shortcuts_tab(self) -> QWidget:
        """Создает вкладку с памяткой по горячим клавишам"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Заголовок
        title_text = self.localization_manager.tr("main_settings.shortcuts.title")
        title_label = QLabel(title_text)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Информация о модификаторе
        mod_info_text = self.localization_manager.tr("main_settings.shortcuts.mod_info")
        mod_info = QLabel(mod_info_text)
        mod_info.setStyleSheet("color: #666; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(mod_info)

        # Создаем прокручиваемую область для таблицы
        from PyQt5.QtWidgets import QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(400)

        # Таблица с горячими клавишами
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels([
            self.localization_manager.tr("main_settings.shortcuts.action"),
            self.localization_manager.tr("main_settings.shortcuts.shortcut")
        ])
        shortcuts_data = [
            (self.localization_manager.tr("main_settings.shortcuts.fullscreen"), "MOD + f"),
            (self.localization_manager.tr("main_settings.shortcuts.rotate_left"), "MOD + ←"),
            (self.localization_manager.tr("main_settings.shortcuts.rotate_right"), "MOD + →"),
            (self.localization_manager.tr("main_settings.shortcuts.pixel_perfect"), "MOD + g"),
            (self.localization_manager.tr("main_settings.shortcuts.remove_black_bars"), "MOD + w"),
            (self.localization_manager.tr("main_settings.shortcuts.home"), "MOD + h"),
            (self.localization_manager.tr("main_settings.shortcuts.back"), "MOD + b"),
            (self.localization_manager.tr("main_settings.shortcuts.app_switch"), "MOD + s"),
            (self.localization_manager.tr("main_settings.shortcuts.menu"), "MOD + m"),
            (self.localization_manager.tr("main_settings.shortcuts.volume_up"), "MOD + ↑"),
            (self.localization_manager.tr("main_settings.shortcuts.volume_down"), "MOD + ↓"),
            (self.localization_manager.tr("main_settings.shortcuts.power"), "MOD + p"),
            (self.localization_manager.tr("main_settings.shortcuts.screen_off"), "MOD + o"),
            (self.localization_manager.tr("main_settings.shortcuts.screen_on"), "MOD + Shift + o"),
            (self.localization_manager.tr("main_settings.shortcuts.rotate_device"), "MOD + r"),
            (self.localization_manager.tr("main_settings.shortcuts.expand_notifications"), "MOD + n"),
            (self.localization_manager.tr("main_settings.shortcuts.expand_settings"), "MOD + n + n"),
            (self.localization_manager.tr("main_settings.shortcuts.collapse_panels"), "MOD + Shift + n"),
            (self.localization_manager.tr("main_settings.shortcuts.copy"), "MOD + c"),
            (self.localization_manager.tr("main_settings.shortcuts.cut"), "MOD + x"),
            (self.localization_manager.tr("main_settings.shortcuts.paste"), "MOD + v"),
            (self.localization_manager.tr("main_settings.shortcuts.paste_text"), "MOD + Shift + v"),
            (self.localization_manager.tr("main_settings.shortcuts.fps_counter"), "MOD + i"),
            (self.localization_manager.tr("main_settings.shortcuts.zoom"),
             self.localization_manager.tr("main_settings.shortcuts.zoom_shortcut")),
            (self.localization_manager.tr("main_settings.shortcuts.install_apk"),
             self.localization_manager.tr("main_settings.shortcuts.install_apk_shortcut")),
            (self.localization_manager.tr("main_settings.shortcuts.send_file"),
             self.localization_manager.tr("main_settings.shortcuts.send_file_shortcut"))
        ]
        table.setRowCount(len(shortcuts_data))

        for i, (action, shortcut) in enumerate(shortcuts_data):
            table.setItem(i, 0, QTableWidgetItem(action))
            table.setItem(i, 1, QTableWidgetItem(shortcut))

        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)

        scroll_area.setWidget(table)
        layout.addWidget(scroll_area)

        # Дополнительная информация
        info_text = f"<b>{self.localization_manager.tr('main_settings.shortcuts.mouse_actions')}</b><br>"
        info_text += f"{self.localization_manager.tr('main_settings.shortcuts.mouse_info')}<br><br>"
        info_text += f"<b>{self.localization_manager.tr('main_settings.shortcuts.notes')}</b><br>"
        info_text += f"{self.localization_manager.tr('main_settings.shortcuts.notes_info')}"
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-top: 10px;")
        layout.addWidget(info_label)

        widget.setLayout(layout)
        return widget

    def _create_language_tab(self) -> QWidget:
        """Создает таб с настройками языка"""
        widget = QWidget()
        layout = QFormLayout()

        # Группа для выбора языка
        group_title = self.localization_manager.tr("language_settings.title")
        russian_text = self.localization_manager.tr("language_settings.russian")
        english_text = self.localization_manager.tr("language_settings.english")
        info_text = self.localization_manager.tr("language_settings.restart_info")
        language_group = QGroupBox(group_title)
        language_layout = QVBoxLayout()

        # Радиокнопки для выбора языка
        self.language_button_group = QButtonGroup()

        self.russian_radio = QRadioButton(russian_text)
        self.russian_radio.setChecked(True)  # По умолчанию русский
        self.language_button_group.addButton(self.russian_radio, 0)
        language_layout.addWidget(self.russian_radio)

        self.english_radio = QRadioButton(english_text)
        self.language_button_group.addButton(self.english_radio, 1)
        language_layout.addWidget(self.english_radio)

        # Подключаем сигнал только к группе кнопок, чтобы избежать двойного срабатывания
        self.language_button_group.buttonClicked.connect(self._on_language_changed)

        language_group.setLayout(language_layout)
        layout.addRow(language_group)

        # Информация о перезапуске
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #666; font-style: italic; margin-top: 10px;")
        info_label.setWordWrap(True)
        layout.addRow(info_label)

        widget.setLayout(layout)
        return widget

    def _on_language_changed(self, button):
        """Обработчик изменения языка"""
        if button == self.russian_radio:
            self.language_changed.emit("ru")
        elif button == self.english_radio:
            self.language_changed.emit("en")

    def on_language_changed(self, language):
        """Обработчик смены языка от LocalizationManager"""
        # При смене языка приложение будет закрыто, поэтому здесь ничего не делаем
        pass

    def reset_settings(self):
        """Сбрасывает настройки к значениям по умолчанию"""
        self.current_settings = {}
        self.load_settings()

    def accept_settings(self):
        """Принимает настройки"""
        settings = self.get_settings()
        self.settings_changed.emit(settings)
        self.accept()
