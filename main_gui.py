"""
main_gui.py

Главный файл графического интерфейса пользователя (GUI) для Universal Unlocker.
Использует CustomTkinter для современного дизайна. Запускается без прав администратора.
"""

import os
import sys
import ctypes
import subprocess
import threading
import customtkinter as ctk

# Настройка внешнего вида CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class UniversalUnlockerApp(ctk.CTk):
    """
    Главное окно приложения.
    """
    def __init__(self):
        super().__init__()

        self.title("Universal Unlocker")
        self.geometry("550x450")
        self.resizable(False, False)

        # Состояние переключателей
        self.hosts_var = ctk.BooleanVar(value=False)
        self.dpi_var = ctk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self):
        """Создает элементы интерфейса."""
        # Заголовок
        self.header = ctk.CTkLabel(self, text="Universal Unlocker", font=ctk.CTkFont(size=24, weight="bold"))
        self.header.pack(pady=(20, 10))

        # Переключатель: Hosts (ИИ)
        self.switch_hosts = ctk.CTkSwitch(
            self, 
            text="Разблокировать ИИ (ChatGPT, Claude) [Hosts]", 
            variable=self.hosts_var,
            font=ctk.CTkFont(size=14)
        )
        self.switch_hosts.pack(pady=10, padx=20, anchor="w")

        # Переключатель: DPI Bypass (YouTube/Discord)
        self.switch_dpi = ctk.CTkSwitch(
            self, 
            text="Разблокировать YouTube/Discord [DPI Bypass]", 
            variable=self.dpi_var,
            font=ctk.CTkFont(size=14)
        )
        self.switch_dpi.pack(pady=10, padx=20, anchor="w")

        # Кнопки управления
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=20, fill="x", padx=20)

        self.btn_apply = ctk.CTkButton(
            self.btn_frame, 
            text="ПРИМЕНИТЬ", 
            fg_color="green", 
            hover_color="darkgreen",
            command=self.apply_changes
        )
        self.btn_apply.pack(side="left", expand=True, padx=10)

        self.btn_stop = ctk.CTkButton(
            self.btn_frame, 
            text="ОСТАНОВИТЬ ВСЁ", 
            fg_color="red", 
            hover_color="darkred",
            command=self.stop_all
        )
        self.btn_stop.pack(side="right", expand=True, padx=10)

        # Консоль логов
        self.log_console = ctk.CTkTextbox(self, state="disabled", font=ctk.CTkFont(family="Consolas", size=12))
        self.log_console.pack(pady=(10, 20), padx=20, fill="both", expand=True)

        self.log("Приложение запущено. Ожидание действий...")

    def log(self, message: str):
        """Добавляет строку лога в текстовое поле."""
        self.log_console.configure(state="normal")
        self.log_console.insert("end", message + "\n")
        self.log_console.see("end")
        self.log_console.configure(state="disabled")

    def _run_worker_elevated(self, action: str):
        """
        Запускает воркер с запросом прав Администратора/Root на лету.
        """
        worker_script = os.path.join(os.path.dirname(__file__), "worker.py")
        hosts_flag = "1" if self.hosts_var.get() else "0"
        dpi_flag = "1" if self.dpi_var.get() else "0"
        
        args = f"{action} {hosts_flag} {dpi_flag}"
        
        try:
            if sys.platform == "win32":
                # Элевация на Windows (запрашивает UAC)
                self.log("Запрос прав Администратора (Windows)...")
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{worker_script}" {args}', None, 1)
            else:
                # Элевация на Linux (запрашивает пароль через pkexec)
                self.log("Запрос прав Root (Linux)...")
                subprocess.Popen(["pkexec", sys.executable, worker_script, action, hosts_flag, dpi_flag])
            
            self.log(f"Команда '{action}' отправлена воркеру.")
        except Exception as e:
            self.log(f"Ошибка элевации: {e}")

    def apply_changes(self):
        """Обработчик кнопки ПРИМЕНИТЬ."""
        self.log("Применение настроек...")
        self._run_worker_elevated("apply")

    def stop_all(self):
        """Обработчик кнопки ОСТАНОВИТЬ ВСЁ."""
        self.log("Остановка всех процессов и откат изменений...")
        self._run_worker_elevated("stop")

if __name__ == "__main__":
    app = UniversalUnlockerApp()
    app.mainloop()
