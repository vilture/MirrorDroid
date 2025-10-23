import os
import tempfile

from PyQt5.QtCore import QObject, pyqtSignal, QThread

try:
    from lyto import cli
    import qrcode
    from io import BytesIO
except ImportError:
    cli = None
    qrcode = None


class QRConnectionWorker(QThread):
    """Поток для работы с QR подключением"""

    qr_generated = pyqtSignal(str)  # Путь к файлу QR кода
    connection_success = pyqtSignal(str)  # IP адрес подключенного устройства
    connection_error = pyqtSignal(str)  # Сообщение об ошибке
    status_update = pyqtSignal(str)  # Обновление статуса

    def __init__(self, adb_path: str = None, tcpip_port: int = 5555):
        super().__init__()
        self.adb_path = adb_path or "adb"
        self.tcpip_port = tcpip_port
        self.should_stop = False

    def run(self):
        """Запускает процесс QR подключения"""
        if not cli or not qrcode:
            self.connection_error.emit("Библиотека lyto не установлена")
            return

        try:
            self.status_update.emit("Инициализация QR подключения...")

            # Создаем временный файл для QR кода
            temp_dir = tempfile.gettempdir()
            qr_file = os.path.join(temp_dir, "mirrordroid_qr.png")

            self.status_update.emit("Генерация QR кода...")

            # Генерируем QR код используя lyto
            # Генерируем случайные имя и пароль для подключения
            import random
            import string
            name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            password = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

            qr_code_data = cli.generate_code(name, password)
            if qr_code_data:
                # Создаем QR код изображение
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_code_data)
                qr.make(fit=True)

                # Создаем изображение
                img = qr.make_image(fill_color="black", back_color="white")
                img.save(qr_file)

                self.qr_generated.emit(qr_file)
                self.status_update.emit("QR код готов! Отсканируйте его на устройстве...")

                # Ждем подключения
                self.status_update.emit("Ожидание подключения устройства...")

                # Проверяем подключение через ADB
                import subprocess
                connected = False
                initial_device_count = 0

                # Считаем изначальное количество устройств
                try:
                    result = subprocess.run([self.adb_path, 'devices'],
                                            capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        for line in lines[1:]:
                            if '\tdevice' in line or '\tunauthorized' in line:
                                initial_device_count += 1
                except:
                    pass

                for i in range(30):  # Ждем до 30 секунд
                    if self.should_stop:
                        return

                    # Проверяем подключение через ADB
                    try:
                        result = subprocess.run([self.adb_path, 'devices'],
                                                capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            # Ищем устройства в выводе
                            lines = result.stdout.strip().split('\n')
                            device_count = 0
                            authorized_devices = 0

                            for line in lines[1:]:  # Пропускаем заголовок
                                if '\tdevice' in line:
                                    device_count += 1
                                    authorized_devices += 1
                                elif '\tunauthorized' in line:
                                    device_count += 1

                            # Проверяем, появилось ли новое устройство
                            if device_count > initial_device_count:
                                if authorized_devices > 0:
                                    connected = True
                                    self.connection_success.emit(f"Новое устройство подключено! Всего: {device_count}")
                                    return
                                else:
                                    self.status_update.emit(
                                        "Новое устройство обнаружено, но не авторизовано. Разрешите отладку на устройстве.")
                            elif device_count > 0:
                                self.status_update.emit(f"Ожидание нового устройства... (найдено: {device_count})")
                    except Exception as e:
                        self.status_update.emit(f"Ошибка проверки ADB: {str(e)}")

                    self.msleep(1000)

                    if i % 5 == 0:
                        self.status_update.emit(f"Ожидание подключения... ({i}/30)")

                # Если не подключилось за время ожидания
                if not connected:
                    self.connection_error.emit("Время ожидания истекло. Устройство не подключилось.")
            else:
                self.connection_error.emit("Не удалось сгенерировать QR код")

        except Exception as e:
            self.connection_error.emit(f"Ошибка QR подключения: {str(e)}")

    def stop(self):
        """Останавливает процесс"""
        self.should_stop = True


class QRConnectionManager(QObject):
    """Менеджер для QR подключения"""

    qr_ready = pyqtSignal(str)  # Путь к QR коду
    device_connected = pyqtSignal(str)  # IP подключенного устройства
    error_occurred = pyqtSignal(str)  # Ошибка
    status_changed = pyqtSignal(str)  # Статус

    def __init__(self, adb_path: str = None):
        super().__init__()
        self.adb_path = adb_path or "adb"
        self.worker = None
        self.qr_file_path = None

    def start_qr_connection(self, tcpip_port: int = 5555):
        """Запускает процесс QR подключения"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

        self.worker = QRConnectionWorker(self.adb_path, tcpip_port)
        self.worker.qr_generated.connect(self.qr_ready)
        self.worker.connection_success.connect(self.device_connected)
        self.worker.connection_error.connect(self.error_occurred)
        self.worker.status_update.connect(self.status_changed)

        self.worker.start()

    def stop_qr_connection(self):
        """Останавливает процесс QR подключения"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

    def cleanup(self):
        """Очищает временные файлы"""
        if self.qr_file_path and os.path.exists(self.qr_file_path):
            try:
                os.remove(self.qr_file_path)
            except:
                pass
