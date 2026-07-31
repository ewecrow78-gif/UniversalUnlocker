"""
linux_engine.py

Движок локального обхода DPI для Linux.
Использует nftables для перенаправления трафика в NFQUEUE 
и запускает nfqws (из проекта zapret) для манипуляции пакетами.
"""

import os
import subprocess
import time
import sys

class LinuxDPIEngine:
    """
    Класс управления процессом nfqws и правилами nftables.
    Требует наличия бинарника nfqws и прав Root.
    """
    
    def __init__(self, bin_dir: str):
        self.bin_dir = bin_dir
        self.executable_path = os.path.join(self.bin_dir, "nfqws")
        self.process = None
        self.qnum = 200 # Номер очереди NFQUEUE

    def _kill_existing(self):
        """Убивает существующие процессы nfqws."""
        print("[DPI Engine] Завершение существующих процессов nfqws...")
        try:
            subprocess.run(
                ["killall", "nfqws"], 
                capture_output=True
            )
            time.sleep(0.5)
        except Exception:
            pass

    def _apply_nftables_rules(self):
        """Добавляет правила nftables для перенаправления TCP 80/443 в NFQUEUE."""
        print("[DPI Engine] Применение правил nftables...")
        # Убедимся, что цепочка существует, иначе создадим
        # Для простоты создаем свою таблицу и цепочку, перехватывающую OUTPUT
        rules = f"""
table inet zapret {{
    chain output {{
        type filter hook output priority 0; policy accept;
        tcp dport {{ 80, 443 }} queue num {self.qnum} bypass
    }}
}}
"""
        try:
            # Сначала пытаемся удалить таблицу, если она была
            subprocess.run(["nft", "delete", "table", "inet", "zapret"], capture_output=True)
            
            # Применяем новые правила
            proc = subprocess.run(["nft", "-f", "-"], input=rules.encode(), capture_output=True)
            if proc.returncode != 0:
                print(f"[DPI Engine] Ошибка nftables: {proc.stderr.decode()}")
                return False
            return True
        except Exception as e:
            print(f"[DPI Engine] Ошибка выполнения nft: {e}")
            return False

    def _remove_nftables_rules(self):
        """Удаляет таблицу zapret из nftables."""
        print("[DPI Engine] Очистка правил nftables...")
        try:
            subprocess.run(["nft", "delete", "table", "inet", "zapret"], capture_output=True)
        except Exception as e:
            print(f"[DPI Engine] Ошибка удаления правил nftables: {e}")

    def start(self):
        """Запускает nfqws и применяет правила."""
        if not os.path.exists(self.executable_path):
            print(f"[DPI Engine] ОШИБКА: Исполняемый файл не найден: {self.executable_path}")
            return False

        if os.geteuid() != 0:
            print("[DPI Engine] ОШИБКА: Для работы с nftables требуются права root!")
            return False

        self._kill_existing()
        
        if not self._apply_nftables_rules():
            return False

        # Параметры nfqws
        args = [
            self.executable_path,
            f"--qnum={self.qnum}",
            "--dpi-desync=fake,split2",
            "--dpi-desync-repeats=6",
            "--dpi-desync-any-protocol"
        ]

        print(f"[DPI Engine] Запуск nfqws: {' '.join(args)}")
        
        try:
            self.process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"[DPI Engine] nfqws успешно запущен (PID: {self.process.pid}).")
            return True
        except Exception as e:
            print(f"[DPI Engine] Ошибка при запуске nfqws: {e}")
            self._remove_nftables_rules()
            return False

    def stop(self):
        """Останавливает nfqws и удаляет правила nftables."""
        if self.process:
            print(f"[DPI Engine] Остановка nfqws (PID: {self.process.pid})...")
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
        
        self._kill_existing()
        self._remove_nftables_rules()
        print("[DPI Engine] Служба DPI Bypass остановлена.")
