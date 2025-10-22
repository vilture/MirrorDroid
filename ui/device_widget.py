from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                             QPushButton, QMenu, QAction, QMessageBox)

from core.localization import LocalizationManager


class DeviceWidget(QWidget):
    """Виджет для отображения устройства в списке"""

    start_scrcpy = pyqtSignal(str)
    stop_scrcpy = pyqtSignal(str)
    disconnect_device = pyqtSignal(str)
    remove_device = pyqtSignal(str)
    configure_device = pyqtSignal(str)
    start_camera = pyqtSignal(str)

    def __init__(self, device_info: dict, scrcpy_running: bool = False,
                 localization_manager: LocalizationManager = None):
        super().__init__()
        self.device_info = device_info
        self.scrcpy_running = scrcpy_running
        self.localization_manager = localization_manager
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        # Основная информация об устройстве
        info_layout = QVBoxLayout()

        # ID устройства
        self.id_label = QLabel(self.device_info.get('id', 'Unknown'))
        self.id_label.setFont(QFont("Arial", 10, QFont.Bold))
        info_layout.addWidget(self.id_label)

        # Дополнительная информация
        details_layout = QHBoxLayout()

        # Имя устройства
        name = self.device_info.get('name', 'Unknown')
        name_text = f"{self.localization_manager.tr('device_widget.name')} {name}"
        self.name_label = QLabel(name_text)
        self.name_label.setStyleSheet("color: #666; font-size: 9px;")
        details_layout.addWidget(self.name_label)

        # Модель устройства
        model = self.device_info.get('model', 'Unknown')
        model_text = f"{self.localization_manager.tr('device_widget.model')} {model}"
        self.model_label = QLabel(model_text)
        self.model_label.setStyleSheet("color: #666; font-size: 9px;")
        details_layout.addWidget(self.model_label)

        # Тип подключения
        connection_type = self.device_info.get('connection_type', 'Unknown')
        type_text = f"{self.localization_manager.tr('device_widget.type')} {connection_type}"
        self.connection_label = QLabel(type_text)
        self.connection_label.setStyleSheet("color: #666; font-size: 9px;")
        details_layout.addWidget(self.connection_label)

        info_layout.addLayout(details_layout)

        # Статус подключения
        status = self.device_info.get('status', 'Unknown')
        status_text = f"{self.localization_manager.tr('device_widget.status')} {status}"
        self.status_label = QLabel(status_text)
        if status == 'device':
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        info_layout.addWidget(self.status_label)

        layout.addLayout(info_layout)

        # Кнопки управления
        buttons_layout = QVBoxLayout()

        # Кнопка запуска/остановки scrcpy
        if self.scrcpy_running:
            button_text = self.localization_manager.tr("device_widget.stop")
            self.scrcpy_button = QPushButton(button_text)
            self.scrcpy_button.setStyleSheet("""
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
            self.scrcpy_button.clicked.connect(self._on_stop_scrcpy)
        else:
            button_text = self.localization_manager.tr("device_widget.start")
            self.scrcpy_button = QPushButton(button_text)
            self.scrcpy_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            self.scrcpy_button.clicked.connect(self._on_start_scrcpy)

        buttons_layout.addWidget(self.scrcpy_button)

        # Кнопка камеры
        camera_text = self.localization_manager.tr("device_widget.camera")
        self.camera_button = QPushButton(camera_text)
        self.camera_button.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        self.camera_button.clicked.connect(self._on_start_camera)
        buttons_layout.addWidget(self.camera_button)

        # Кнопка меню
        self.menu_button = QPushButton("⋮")
        self.menu_button.setFixedSize(30, 30)
        self.menu_button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        self.menu_button.clicked.connect(self._show_context_menu)
        buttons_layout.addWidget(self.menu_button)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        # Стиль виджета
        self.setStyleSheet("""
            DeviceWidget {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background-color: white;
                margin: 2px;
            }
            DeviceWidget:hover {
                border-color: #007bff;
                background-color: #f8f9fa;
            }
        """)

    def _on_start_scrcpy(self):
        """Обработчик запуска scrcpy"""
        self.start_scrcpy.emit(self.device_info['id'])

    def _on_stop_scrcpy(self):
        """Обработчик остановки scrcpy"""
        self.stop_scrcpy.emit(self.device_info['id'])

    def _on_start_camera(self):
        """Обработчик запуска камеры"""
        self.start_camera.emit(self.device_info['id'])

    def _on_configure_device(self):
        """Обработчик настройки устройства"""
        self.configure_device.emit(self.device_info['id'])

    def _show_context_menu(self):
        """Показывает контекстное меню"""
        menu = QMenu(self)

        # Действие отключения
        disconnect_text = self.localization_manager.tr("device_widget.disconnect")
        disconnect_action = QAction(disconnect_text, self)
        disconnect_action.triggered.connect(
            lambda: self.disconnect_device.emit(self.device_info['id'])
        )
        menu.addAction(disconnect_action)

        # Действие удаления
        remove_text = self.localization_manager.tr("device_widget.remove")
        remove_action = QAction(remove_text, self)
        remove_action.triggered.connect(
            lambda: self._confirm_remove_device()
        )
        menu.addAction(remove_action)

        menu.exec_(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))

    def _confirm_remove_device(self):
        """Подтверждение удаления устройства"""
        title = self.localization_manager.tr("device_widget.confirm_remove")
        message = self.localization_manager.tr("device_widget.confirm_remove_message", device_id=self.device_info['id'])
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.remove_device.emit(self.device_info['id'])

    def update_scrcpy_status(self, running: bool):
        """Обновляет статус scrcpy"""
        self.scrcpy_running = running

        if running:
            button_text = self.localization_manager.tr("device_widget.stop")
            self.scrcpy_button.setText(button_text)
            self.scrcpy_button.setStyleSheet("""
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
            self.scrcpy_button.clicked.disconnect()
            self.scrcpy_button.clicked.connect(self._on_stop_scrcpy)
        else:
            button_text = self.localization_manager.tr("device_widget.start")
            self.scrcpy_button.setText(button_text)
            self.scrcpy_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            self.scrcpy_button.clicked.disconnect()
            self.scrcpy_button.clicked.connect(self._on_start_scrcpy)

    def update_device_info(self, device_info: dict):
        """Обновляет информацию об устройстве"""
        self.device_info = device_info

        # Обновляем отображаемую информацию
        self.id_label.setText(device_info.get('id', 'Unknown'))

        # Имя устройства
        name = device_info.get('name', 'Unknown')
        name_text = f"{self.localization_manager.tr('device_widget.name')} {name}"
        self.name_label.setText(name_text)

        # Модель устройства
        model = device_info.get('model', 'Unknown')
        model_text = f"{self.localization_manager.tr('device_widget.model')} {model}"
        self.model_label.setText(model_text)

        # Тип подключения
        connection_type = device_info.get('connection_type', 'Unknown')
        type_text = f"{self.localization_manager.tr('device_widget.type')} {connection_type}"
        self.connection_label.setText(type_text)

        # Обновляем статус
        status = device_info.get('status', 'Unknown')
        status_text = f"{self.localization_manager.tr('device_widget.status')} {status}"
        self.status_label.setText(status_text)
        if status == 'device':
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
