import os

from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QDateTime
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QFrame, QProgressBar)

from core.qr_connection import QRConnectionManager
from core.utils import get_icon_path


class QRConnectionDialog(QDialog):
    """Диалог для QR подключения к устройству"""

    device_connected = pyqtSignal(str)  # IP подключенного устройства

    def __init__(self, adb_path: str = None, parent=None, localization_manager=None):
        super().__init__(parent)
        self.localization_manager = localization_manager
        self.adb_path = adb_path or "adb"
        self.qr_manager = None

        self.setWindowTitle(self.localization_manager.tr("qr_connection.title"))
        self.setModal(True)
        self.resize(500, 600)

        # Устанавливаем иконку окна
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._create_ui()
        self._setup_connections()

    def _create_ui(self):
        """Создает интерфейс диалога"""
        layout = QVBoxLayout()

        # Инструкции
        instructions = QLabel(self.localization_manager.tr("qr_connection.instructions"))
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; margin: 10px;")
        layout.addWidget(instructions)

        # Область для QR кода
        qr_frame = QFrame()
        qr_frame.setFrameStyle(QFrame.StyledPanel)
        qr_frame.setMinimumHeight(300)
        qr_layout = QVBoxLayout()

        # QR код изображение
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setStyleSheet("border: 2px dashed #ccc; padding: 20px;")
        self.qr_label.setText(self.localization_manager.tr("qr_connection.qr_placeholder"))
        self.qr_label.setMinimumHeight(250)
        qr_layout.addWidget(self.qr_label)

        qr_frame.setLayout(qr_layout)
        layout.addWidget(qr_frame)

        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Статус
        self.status_label = QLabel(self.localization_manager.tr("qr_connection.ready"))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)

        # Лог
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setPlaceholderText(self.localization_manager.tr("qr_connection.log_placeholder"))
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        # Кнопки
        buttons_layout = QHBoxLayout()

        self.start_button = QPushButton(self.localization_manager.tr("qr_connection.start"))
        self.start_button.clicked.connect(self._start_qr_connection)
        self.start_button.setStyleSheet("""
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

        self.stop_button = QPushButton(self.localization_manager.tr("qr_connection.stop"))
        self.stop_button.clicked.connect(self._stop_qr_connection)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)

        self.close_button = QPushButton(self.localization_manager.tr("qr_connection.close"))
        self.close_button.clicked.connect(self.reject)

        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def _setup_connections(self):
        """Настраивает соединения"""
        pass

    def _start_qr_connection(self):
        """Запускает QR подключение"""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Неопределенный прогресс

        # Создаем менеджер QR подключения
        self.qr_manager = QRConnectionManager(self.adb_path)
        self.qr_manager.qr_ready.connect(self._on_qr_ready)
        self.qr_manager.device_connected.connect(self._on_device_connected)
        self.qr_manager.error_occurred.connect(self._on_error)
        self.qr_manager.status_changed.connect(self._on_status_changed)

        # Запускаем процесс
        self.qr_manager.start_qr_connection()

    def _stop_qr_connection(self):
        """Останавливает QR подключение"""
        if self.qr_manager:
            self.qr_manager.stop_qr_connection()

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText(self.localization_manager.tr("qr_connection.stopped"))

    def _on_qr_ready(self, qr_file_path: str):
        """Обработчик готовности QR кода"""
        try:
            pixmap = QPixmap(qr_file_path)
            if not pixmap.isNull():
                # Масштабируем QR код для отображения
                scaled_pixmap = pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.qr_label.setPixmap(scaled_pixmap)
                self._log_message(f"QR код сгенерирован: {qr_file_path}")
            else:
                self._log_message("Ошибка загрузки QR кода")
        except Exception as e:
            self._log_message(f"Ошибка отображения QR кода: {e}")

    def _on_device_connected(self, device_info: str):
        """Обработчик подключения устройства"""
        self._log_message(f"Устройство подключено: {device_info}")
        self.status_label.setText(self.localization_manager.tr("qr_connection.connected"))
        self.progress_bar.setVisible(False)

        # Эмитируем сигнал о подключении
        self.device_connected.emit(device_info)

        # Закрываем диалог через 2 секунды
        QTimer.singleShot(2000, self.accept)

    def _on_error(self, error_message: str):
        """Обработчик ошибки"""
        self._log_message(f"Ошибка: {error_message}")

        # Определяем тип ошибки для более точного сообщения
        if "Время ожидания истекло" in error_message:
            self.status_label.setText(self.localization_manager.tr("qr_connection.timeout"))
        elif "не авторизовано" in error_message:
            self.status_label.setText(self.localization_manager.tr("qr_connection.unauthorized"))
        else:
            self.status_label.setText(self.localization_manager.tr("qr_connection.error"))

        self.progress_bar.setVisible(False)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def _on_status_changed(self, status: str):
        """Обработчик изменения статуса"""
        self.status_label.setText(status)
        self._log_message(status)

    def _log_message(self, message: str):
        """Добавляет сообщение в лог"""
        self.log_text.append(f"[{QDateTime.currentDateTime().toString('hh:mm:ss')}] {message}")
        # Прокручиваем вниз
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)

    def closeEvent(self, event):
        """Обработчик закрытия диалога"""
        if self.qr_manager:
            self.qr_manager.stop_qr_connection()
            self.qr_manager.cleanup()
        event.accept()
