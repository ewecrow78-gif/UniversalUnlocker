"""
hosts_manager.py

Модуль для модификации системного файла hosts с целью обхода Geo-блокировок.
Требует прав администратора для записи в файл.
"""

import os
import sys
import shutil
import urllib.request
import subprocess
from pathlib import Path

class HostsManager:
    """
    Класс управления системным файлом hosts.
    Обеспечивает резервное копирование, запись новых правил и очистку.
    """
    MARKER_START = "# --- UNIVERSAL UNLOCKER START ---"
    MARKER_END = "# --- UNIVERSAL UNLOCKER END ---"

    def __init__(self):
        if sys.platform == "win32":
            windir = os.environ.get("WINDIR", "C:\\Windows")
            self.hosts_path = Path(windir) / "System32" / "drivers" / "etc" / "hosts"
        else:
            self.hosts_path = Path("/etc/hosts")
            
        self.backup_path = self.hosts_path.with_suffix(".hosts.bak")

    def create_backup(self):
        """Создает резервную копию файла hosts, если её еще нет."""
        if not self.backup_path.exists():
            shutil.copy2(self.hosts_path, self.backup_path)
            print(f"[HostsManager] Резервная копия создана: {self.backup_path}")

    def fetch_unlock_rules(self, url: str) -> list[str]:
        """
        Скачивает список строк для hosts с указанного URL.
        Если скачивание не удалось, можно использовать захардкоженный список.
        """
        try:
            print(f"[HostsManager] Скачивание правил с {url}...")
            response = urllib.request.urlopen(url, timeout=5)
            data = response.read().decode('utf-8')
            return [line.strip() for line in data.splitlines() if line.strip() and not line.startswith('#')]
        except Exception as e:
            print(f"[HostsManager] Ошибка скачивания правил: {e}. Используем fallback.")
            # Захардкоженный словарь для AI сервисов (пример)
            return [
                "104.18.32.7 chatgpt.com",
                "104.18.32.7 openai.com"
            ]

    def apply_rules(self, rules: list[str]):
        """
        Записывает правила в файл hosts между маркерами. 
        Предварительно удаляет старые правила программы.
        """
        self.create_backup()
        self.remove_rules() # Очищаем старые записи перед добавлением новых

        try:
            with open(self.hosts_path, "a", encoding="utf-8") as f:
                f.write(f"\n{self.MARKER_START}\n")
                for rule in rules:
                    f.write(f"{rule}\n")
                f.write(f"{self.MARKER_END}\n")
            print("[HostsManager] Правила успешно добавлены в hosts.")
            self.flush_dns()
        except PermissionError:
            print("[HostsManager] ОШИБКА: Нет прав администратора для записи в hosts!")

    def remove_rules(self):
        """Удаляет блок правил Universal Unlocker из hosts (откат изменений)."""
        if not self.hosts_path.exists():
            return

        with open(self.hosts_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        in_block = False
        for line in lines:
            if self.MARKER_START in line:
                in_block = True
                continue
            if self.MARKER_END in line:
                in_block = False
                continue
            if not in_block:
                new_lines.append(line)

        try:
            with open(self.hosts_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            print("[HostsManager] Правила программы удалены из hosts.")
            self.flush_dns()
        except PermissionError:
            print("[HostsManager] ОШИБКА: Нет прав администратора для записи в hosts!")

    def flush_dns(self):
        """Сбрасывает DNS-кэш системы."""
        print("[HostsManager] Сброс DNS кэша...")
        try:
            if sys.platform == "win32":
                subprocess.run(["ipconfig", "/flushdns"], capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.run(["resolvectl", "flush-caches"], capture_output=True, text=True, check=True)
            print("[HostsManager] DNS кэш успешно сброшен.")
        except Exception as e:
            print(f"[HostsManager] Ошибка при сбросе DNS: {e}")
