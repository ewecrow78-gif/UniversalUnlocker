import sys
import os

# Добавляем родительскую директорию в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.hosts_manager import HostsManager
from core.dpi_engine.windows_engine import WindowsDPIEngine

def main():
    if len(sys.argv) < 4:
        print("Usage: worker.py <action> <hosts_flag> <dpi_flag>")
        return

    action = sys.argv[1]
    hosts_enabled = sys.argv[2] == "1"
    dpi_enabled = sys.argv[3] == "1"

    if action == "apply":
        if hosts_enabled:
            hm = HostsManager()
            # Для примера используем дефолтные правила
            rules = hm.fetch_unlock_rules("https://example.com/hosts.txt")
            hm.apply_rules(rules)
        if dpi_enabled:
            bin_dir = os.path.join(os.path.dirname(__file__), "bin", "win")
            engine = WindowsDPIEngine(bin_dir)
            engine.start()

    elif action == "stop":
        hm = HostsManager()
        hm.remove_rules()
        bin_dir = os.path.join(os.path.dirname(__file__), "bin", "win")
        engine = WindowsDPIEngine(bin_dir)
        engine.stop()

if __name__ == "__main__":
    main()
