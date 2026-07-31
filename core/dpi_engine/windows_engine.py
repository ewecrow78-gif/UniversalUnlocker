"""
windows_engine.py

Движок локального обхода DPI для Windows.
Запускает утилиту winws (из проекта zapret) в скрытом режиме и управляет её жизненным циклом.
"""

import os
import subprocess
import time

class WindowsDPIEngine:
    """
    Класс управления процессом winws.exe.
    Требует наличия winws.exe и WinDivert.dll в указанной директории, а также прав администратора.
    """
    
    def __init__(self, bin_dir: str):
        """
        Инициализация движка.
        :param bin_dir: Путь к папке, где лежат winws.exe и WinDivert.dll
        """
        self.bin_dir = bin_dir
        self.executable_path = os.path.join(self.bin_dir, "winws.exe")
        self.process = None

    def _kill_existing(self):
        """
        Завершает все существующие процессы winws.exe перед новым запуском
        во избежание конфликтов портов и утечек драйвера WinDivert.
        """
        print("[DPI Engine] Завершение существующих процессов winws.exe...")
        try:
            # taskkill /F /IM winws.exe
            subprocess.run(
                ["taskkill", "/F", "/IM", "winws.exe"], 
                capture_output=True, 
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(1) # Ждем освобождения ресурсов
        except Exception as e:
            print(f"[DPI Engine] Ошибка при остановке существующих процессов: {e}")

    def start(self):
        """
        Формирует аргументы обхода и запускает winws в фоновом режиме без окна.
        """
        if not os.path.exists(self.executable_path):
            print(f"[DPI Engine] ОШИБКА: Исполняемый файл не найден: {self.executable_path}")
            return False

        self._kill_existing()

        # Параметры обхода DPI (подбираются индивидуально или берутся из zapret-discord-youtube)
        args = [
            self.executable_path,
            "--wf-tcp=80,443",
            "--wf-udp=443,50000-65535", # UDP часто нужен для Discord/QUIC
            "--dpi-desync=fake,split2",
            "--dpi-desync-repeats=6",
            "--dpi-desync-autottl=2",
            "--dpi-desync-any-protocol"
        ]

        print(f"[DPI Engine] Запуск winws: {' '.join(args)}")
        
        try:
            # Запуск процесса без создания окна консоли (CREATE_NO_WINDOW)
            self.process = subprocess.Popen(
                args,
                cwd=self.bin_dir, # Рабочая директория важна для подхвата WinDivert.dll
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print(f"[DPI Engine] winws.exe успешно запущен (PID: {self.process.pid}).")
            return True
        except Exception as e:
            print(f"[DPI Engine] Ошибка при запуске winws: {e}")
            return False

    def stop(self):
        """
        Останавливает процесс winws.exe (graceful shutdown).
        """
        if self.process:
            print(f"[DPI Engine] Остановка процесса (PID: {self.process.pid})...")
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
        
        # Гарантированное убийство процесса в ОС
        self._kill_existing()
        print("[DPI Engine] Служба DPI Bypass остановлена.")
