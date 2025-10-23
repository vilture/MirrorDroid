import os
import platform
import subprocess
from typing import Dict, Any, List

from PyQt5.QtCore import QObject, pyqtSignal, QProcess

from .path_manager import path_manager
from .utils import debug_print


class ScrcpyManager(QObject):
    """Менеджер для управления процессами scrcpy"""

    process_started = pyqtSignal(str, int)  # device_id, process_id
    process_finished = pyqtSignal(str, int)  # device_id, exit_code
    process_error = pyqtSignal(str, str)  # device_id, error_message
    stderr_output = pyqtSignal(str, str)  # device_id, error_output

    def __init__(self):
        super().__init__()
        self.active_processes = {}  # device_id -> QProcess
        # Используем PathManager для определения пути к scrcpy
        self.scrcpy_path = path_manager.get_scrcpy_path()

    def start_scrcpy(self, device_id: str, settings: Dict[str, Any]) -> bool:
        """Запускает scrcpy с заданными параметрами"""
        if device_id in self.active_processes:
            return False  # Уже запущен

        try:
            # Формируем команду scrcpy
            cmd = self._build_scrcpy_command(device_id, settings)
            # Повышаем подробность логов scrcpy в debug-режиме
            if os.environ.get('MIRRORDROID_DEBUG') == '1':
                cmd.extend(['-V', 'debug'])
            debug_print(f"🔧 Scrcpy command: {' '.join(cmd)}")

            # Гибридный подход: QProcess для debug, subprocess для обычного режима на Windows
            if platform.system().lower() == 'windows' and os.environ.get('MIRRORDROID_DEBUG') != '1':
                # Обычный режим на Windows - скрываем консоль
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    startupinfo=startupinfo
                )
                # Сохраняем subprocess как QProcess для совместимости
                self.active_processes[device_id] = process
                self.process_started.emit(device_id, process.pid)
                return True
            else:
                # Debug режим или Linux - используем QProcess
                process = QProcess()
                process.setProcessChannelMode(QProcess.SeparateChannels)  # Разделяем stdout и stderr

                # Подключаем сигналы
                process.finished.connect(
                    lambda exit_code, exit_status: self._on_process_finished(device_id, exit_code, exit_status)
                )
                process.errorOccurred.connect(
                    lambda error: self._on_process_error(device_id, error)
                )

                # Подключаем обработчик вывода
                process.readyReadStandardOutput.connect(
                    lambda: self._on_process_output(device_id, process.readAllStandardOutput().data().decode())
                )
                process.readyReadStandardError.connect(
                    lambda: self._on_process_error_output(device_id, process.readAllStandardError().data().decode())
                )
                
                # Запускаем процесс
                process.start(cmd[0], cmd[1:])

                if process.waitForStarted(5000):  # Ждем 5 секунд
                    self.active_processes[device_id] = process
                    self.process_started.emit(device_id, process.processId())
                    return True
                else:
                    error_msg = f"Не удалось запустить scrcpy. Код ошибки: {process.error()}"
                    self.process_error.emit(device_id, error_msg)
                    return False

        except Exception as e:
            error_msg = f"Ошибка запуска: {e}"
            self.process_error.emit(device_id, error_msg)
            return False

    def stop_scrcpy(self, device_id: str) -> bool:
        """Останавливает scrcpy для устройства"""
        if device_id in self.active_processes:
            process = self.active_processes[device_id]

            # Проверяем тип процесса
            if hasattr(process, 'terminate'):  # QProcess
                process.terminate()
                if not process.waitForFinished(3000):  # Ждем 3 секунды
                    process.kill()  # Принудительно завершаем
            else:  # subprocess.Popen
                process.terminate()
                try:
                    process.wait(timeout=3)  # Ждем 3 секунды
                except subprocess.TimeoutExpired:
                    process.kill()  # Принудительно завершаем

            # Безопасное удаление - проверяем еще раз
            if device_id in self.active_processes:
                del self.active_processes[device_id]
            return True
        return False

    def stop_all_scrcpy(self):
        """Останавливает все процессы scrcpy"""
        # Создаем копию списка ключей, чтобы избежать изменения словаря во время итерации
        device_ids = list(self.active_processes.keys())
        for device_id in device_ids:
            if device_id in self.active_processes:  # Проверяем, что процесс еще существует
                self.stop_scrcpy(device_id)

    def is_scrcpy_running(self, device_id: str) -> bool:
        """Проверяет, запущен ли scrcpy для устройства"""
        if device_id in self.active_processes:
            process = self.active_processes[device_id]
            # Проверяем тип процесса
            if hasattr(process, 'state'):  # QProcess
                return process.state() == QProcess.Running
            else:  # subprocess.Popen
                return process.poll() is None  # None означает, что процесс еще работает
        return False

    def get_active_devices(self) -> List[str]:
        """Получает список устройств с активными scrcpy"""
        active_devices = []
        for device_id, process in self.active_processes.items():
            if hasattr(process, 'state'):  # QProcess
                if process.state() == QProcess.Running:
                    active_devices.append(device_id)
            else:  # subprocess.Popen
                if process.poll() is None:  # None означает, что процесс еще работает
                    active_devices.append(device_id)
        return active_devices

    def is_camera_running(self, device_id: str) -> bool:
        """Проверяет, запущена ли камера для устройства"""
        return self.is_scrcpy_running(device_id)

    def _build_scrcpy_command(self, device_id: str, settings: Dict[str, Any]) -> List[str]:
        """Строит команду scrcpy на основе настроек"""
        cmd = [self.scrcpy_path, '-s', device_id]

        # Видео настройки
        video = settings.get('video', {})
        if video.get('max_size', 0) > 0:
            cmd.extend(['--max-size', str(video['max_size'])])
        if video.get('bit_rate', 0) > 0:
            cmd.extend(['--video-bit-rate', str(video['bit_rate'])])
        if video.get('max_fps', 0) > 0:
            cmd.extend(['--max-fps', str(video['max_fps'])])
        if video.get('codec'):
            cmd.extend(['--video-codec', video['codec']])
        if video.get('encoder'):
            cmd.extend(['--video-encoder', video['encoder']])

        # Аудио настройки
        audio = settings.get('audio', {})
        if audio.get('disable_audio', False):
            cmd.append('--no-audio')
        else:
            if audio.get('codec'):
                cmd.extend(['--audio-codec', audio['codec']])
            if audio.get('bit_rate', 0) > 0:
                cmd.extend(['--audio-bit-rate', str(audio['bit_rate'])])
            if audio.get('buffer_size', 0) > 0:
                cmd.extend(['--audio-buffer', str(audio['buffer_size'])])

        # Настройки отображения
        display = settings.get('display', {})
        if display.get('rotation', 0) != 0:
            cmd.extend(['--display-orientation', str(display['rotation'])])
        if display.get('crop'):
            cmd.extend(['--crop', display['crop']])
        if display.get('fullscreen', False):
            cmd.append('--fullscreen')
        if display.get('always_on_top', False):
            cmd.append('--always-on-top')
        if display.get('window_title'):
            cmd.extend(['--window-title', display['window_title']])

        # Настройки управления
        control = settings.get('control', {})
        if control.get('show_touches', False):
            cmd.append('--show-touches')
        if control.get('stay_awake', False):
            cmd.append('--stay-awake')
        if control.get('turn_screen_off', False):
            cmd.append('--turn-screen-off')

        # Настройки записи
        record = settings.get('record', {})
        if record.get('file'):
            cmd.extend(['--record', record['file']])
            if record.get('format'):
                cmd.extend(['--record-format', record['format']])
            if record.get('time_limit', 0) > 0:
                cmd.extend(['--time-limit', str(record['time_limit'])])

        # Настройки камеры
        camera = settings.get('camera', {})
        if camera.get('camera_id'):
            cmd.extend(['--camera-id', camera['camera_id']])
        # При high-speed scrcpy сам подберёт допустимое разрешение; не задаём --camera-size
        if camera.get('camera_size') and not camera.get('camera_high_speed', False):
            cmd.extend(['--camera-size', camera['camera_size']])
        if camera.get('camera_fps', 0) > 0:
            cmd.extend(['--camera-fps', str(camera['camera_fps'])])
        if camera.get('camera_ar') and camera['camera_ar'] not in ['', 'Автоматически']:
            cmd.extend(['--camera-ar', camera['camera_ar']])
        if camera.get('camera_high_speed', False):
            cmd.append('--camera-high-speed')

        # Настройки управления и устройств ввода
        control = settings.get('control', {})
        keyboard_mode = control.get('keyboard')
        if keyboard_mode in ('uhid', 'aoa', 'sdk'):
            cmd.append(f"--keyboard={keyboard_mode}")
        mouse_mode = control.get('mouse')
        if mouse_mode in ('uhid', 'aoa', 'sdk'):
            cmd.append(f"--mouse={mouse_mode}")
        # Настройки геймпада
        gamepad_mode = control.get('gamepad', 'disabled')
        if gamepad_mode == True:  # Совместимость со старыми настройками
            gamepad_mode = 'aoa'
        elif gamepad_mode == False:
            gamepad_mode = 'disabled'
        
        if gamepad_mode in ('aoa', 'uhid'):
            cmd.append(f"--gamepad={gamepad_mode}")
        # Для корректного ввода нелатиницы (кириллица и т.п.) предпочтительнее текстовый ввод
        # --prefer-text работает только с --keyboard=sdk
        if keyboard_mode == 'sdk' and control.get('prefer_text', False):
            cmd.append('--prefer-text')
            # Улучшает надёжность вставки текста в некоторые поля/IME
            if control.get('legacy_paste', False):
                cmd.append('--legacy-paste')
        elif control.get('raw_key_events', False):
            cmd.append('--raw-key-events')
        if control.get('no_key_repeat', False):
            cmd.append('--no-key-repeat')
        if control.get('forward_all_clicks', False):
            cmd.append('--forward-all-clicks')
        if control.get('legacy_paste', False):
            cmd.append('--legacy-paste')

        # Дополнительные настройки
        advanced = settings.get('advanced', {})
        if advanced.get('otg', False):
            cmd.append('--otg')
        if advanced.get('disable_screensaver', False):
            cmd.append('--disable-screensaver')
        if advanced.get('power_off_on_close', False):
            cmd.append('--power-off-on-close')
        if advanced.get('power_on', False):
            cmd.append('--power-on')
        if advanced.get('start_fps', 0) > 0:
            cmd.extend(['--start-fps', str(advanced['start_fps'])])
        if advanced.get('lock_video_orientation', -1) != -1:
            cmd.extend(['--lock-video-orientation', str(advanced['lock_video_orientation'])])
        if advanced.get('display_id', 0) > 0:
            cmd.extend(['--display-id', str(advanced['display_id'])])
        if advanced.get('tcpip'):
            cmd.extend(['--tcpip', advanced['tcpip']])
        if advanced.get('select_usb', False):
            cmd.append('--select-usb')
        if advanced.get('select_tcpip', False):
            cmd.append('--select-tcpip')
        if advanced.get('shortcut_mod'):
            cmd.extend(['--shortcut-mod', advanced['shortcut_mod']])

        # Дополнительные полезные параметры
        if display.get('always_on_top', False):
            cmd.append('--always-on-top')

        # Параметры для улучшения качества
        if video.get('buffer_size', 0) > 0:
            cmd.extend(['--video-buffer', str(video['buffer_size'])])

        return cmd

    def _on_process_finished(self, device_id: str, exit_code: int, exit_status):
        """Обработчик завершения процесса"""
        if device_id in self.active_processes:
            del self.active_processes[device_id]
        self.process_finished.emit(device_id, exit_code)

    def _on_process_output(self, device_id: str, output: str):
        """Обработчик вывода процесса"""
        if output.strip():
            debug_print(f"[scrcpy:{device_id}] {output.strip()}")

    def _on_process_error_output(self, device_id: str, error_output: str):
        """Обработчик вывода ошибок процесса"""
        if error_output.strip():
            debug_print(f"⚠️ [scrcpy:{device_id}:err] {error_output.strip()}")
            # Эмитируем сигнал для отображения в статусбаре
            self.stderr_output.emit(device_id, error_output.strip())

    def _on_process_error(self, device_id: str, error):
        """Обработчик ошибки процесса"""
        error_msg = f"Ошибка процесса: {error}"
        self.process_error.emit(device_id, error_msg)
        if device_id in self.active_processes:
            del self.active_processes[device_id]

    def start_camera(self, device_id: str, camera_settings: Dict[str, Any]) -> bool:
        """Запускает камеру для устройства с настройками"""
        try:
            # Формируем команду для камеры
            cmd = self._build_camera_command(device_id, camera_settings)
            # Повышаем подробность логов scrcpy в debug-режиме
            if os.environ.get('MIRRORDROID_DEBUG') == '1':
                cmd.extend(['-V', 'debug'])
            debug_print(f"🔧 Camera command: {' '.join(cmd)}")

            # Гибридный подход: QProcess для debug, subprocess для обычного режима на Windows
            if platform.system().lower() == 'windows' and os.environ.get('MIRRORDROID_DEBUG') != '1':
                # Обычный режим на Windows - скрываем консоль
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    startupinfo=startupinfo
                )
                # Сохраняем subprocess как QProcess для совместимости
                self.active_processes[device_id] = process
                self.process_started.emit(device_id, process.pid)
                return True
            else:
                # Debug режим или Linux - используем QProcess
                process = QProcess()

                # Подключаем сигналы
                process.finished.connect(
                    lambda exit_code, exit_status: self._on_process_finished(device_id, exit_code, exit_status))
                process.errorOccurred.connect(lambda error: self._on_process_error(device_id, error))
                process.readyReadStandardOutput.connect(
                    lambda: self._on_process_output(device_id, process.readAllStandardOutput().data().decode()))
                process.readyReadStandardError.connect(
                    lambda: self._on_process_error_output(device_id, process.readAllStandardError().data().decode()))

                # Запускаем процесс
                process.start(cmd[0], cmd[1:])

                if not process.waitForStarted(5000):
                    return False

                # Сохраняем процесс
                self.active_processes[device_id] = process

                # Эмитируем сигнал
                self.process_started.emit(device_id, process.processId())

                return True

        except Exception as e:
            debug_print(f"⚠️ Error starting camera: {e}")
            return False

    def _build_camera_command(self, device_id: str, camera_settings: Dict[str, Any]) -> List[str]:
        """Строит команду scrcpy для камеры на основе настроек"""
        cmd = [self.scrcpy_path, '-s', device_id]

        # Добавляем параметр для использования камеры
        cmd.append('--video-source=camera')

        # Настройки камеры
        camera = camera_settings.get('camera', {})

        # Отключаем аудио для камеры если включена соответствующая настройка
        if camera.get('camera_no_audio', False):  # По умолчанию False
            cmd.append('--no-audio')

        if camera.get('camera_id'):
            cmd.extend(['--camera-id', camera['camera_id']])
        if camera.get('camera_size'):
            cmd.extend(['--camera-size', camera['camera_size']])
        if camera.get('camera_fps', 0) > 0:
            cmd.extend(['--camera-fps', str(camera['camera_fps'])])
        if camera.get('camera_ar') and camera['camera_ar'] not in ['', 'Автоматически']:
            cmd.extend(['--camera-ar', camera['camera_ar']])
        if camera.get('camera_high_speed', False):
            cmd.append('--camera-high-speed')

        # Настройки отображения
        display = camera_settings.get('display', {})
        rotation = display.get('rotation', 0)
        flip = display.get('flip', False)
        
        # Комбинируем поворот и зеркальное отображение
        if rotation != 0 or flip:
            if flip:
                orientation = f"flip{rotation}"
            else:
                orientation = str(rotation)
            cmd.extend(['--display-orientation', orientation])
            
        if display.get('crop'):
            cmd.extend(['--crop', display['crop']])
        if display.get('fullscreen', False):
            cmd.append('--fullscreen')
        if display.get('always_on_top', False):
            cmd.append('--always-on-top')

        # V4L2 настройки (только если включен)
        v4l2 = camera_settings.get('v4l2', {})
        if v4l2.get('enabled', False) and v4l2.get('device'):
            cmd.extend(['--v4l2-sink', v4l2['device']])
            # Отключаем воспроизведение видео если включено
            if v4l2.get('no_playback', True):
                cmd.append('--no-video-playback')
            # V4L2 буфер (в миллисекундах)
            if v4l2.get('buffers', 0) > 0:
                # Конвертируем количество буферов в миллисекунды (примерно 33ms на буфер)
                buffer_ms = v4l2['buffers'] * 33
                cmd.extend(['--v4l2-buffer', str(buffer_ms)])

        return cmd
