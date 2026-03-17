# sysinfo.py
import platform
import psutil
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from design import print_narrative, print_error, EMOJI_LIGHTNING

console = Console()

def get_gpu_info():
    try:
        if platform.system() == "Windows":
            import subprocess
            output = subprocess.check_output("wmic path win32_VideoController get name", shell=True).decode()
            lines = output.strip().split('\n')
            gpu_names = [line.strip() for line in lines[1:] if line.strip()]
            return "\n".join(gpu_names) if gpu_names else "Unknown"
        elif platform.system() == "Linux":
            import subprocess
            try:
                output = subprocess.check_output("lspci | grep -E 'VGA|3D'", shell=True).decode()
                return output.strip().replace('\n', '\n') or "Unknown"
            except:
                return "Unknown (run lspci)"
        elif platform.system() == "Darwin":
            import subprocess
            try:
                output = subprocess.check_output("system_profiler SPDisplaysDataType | grep Chipset", shell=True).decode()
                return output.strip().replace('Chipset Model:', '').strip()
            except:
                return "Apple Graphics"
        else:
            return "Unknown"
    except Exception as e:
        return f"GPU info unavailable ({e})"

def _make_bar(percent, width=20):
    filled = int(percent * width)
    bar = "█" * filled + "░" * (width - filled)
    if percent < 0.5:
        color = "green"
    elif percent < 0.8:
        color = "yellow"
    else:
        color = "red"
    return f"[{color}]{bar}[/]"

def display_system_info():
    try:
        os_info = f"{platform.system()} {platform.release()}"
        hostname = platform.node()
        cpu_count = psutil.cpu_count(logical=True)
        cpu_percent = psutil.cpu_percent(interval=0.5) / 100.0
        mem = psutil.virtual_memory()
        mem_total = mem.total / (1024**3)
        mem_used = mem.used / (1024**3)
        mem_percent = mem.percent / 100.0
        gpu = get_gpu_info()

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Details", style="bright_white")

        table.add_row("🖥️  OS", os_info)
        table.add_row("🏷️  Hostname", hostname)
        cpu_bar = _make_bar(cpu_percent)
        table.add_row("🧠 CPU", f"{cpu_count} cores  {cpu_bar}  {cpu_percent*100:.1f}%")
        ram_bar = _make_bar(mem_percent)
        table.add_row("🧮 RAM", f"{mem_used:.1f}GB / {mem_total:.1f}GB  {ram_bar}  {mem_percent*100:.1f}%")
        table.add_row("🎮 GPU", gpu)

        panel = Panel(
            table,
            title=f"[bold bright_red]{EMOJI_LIGHTNING} SYSTEM AUTOPSY {EMOJI_LIGHTNING}[/]",
            border_style="bright_red",
            subtitle="[italic]The creature's anatomy[/]"
        )
        console.print(panel)

        if mem_percent > 0.9:
            print_narrative("The creature's memory is nearly full! It hungers for more...", style="bold red")
        elif cpu_percent > 0.9:
            print_narrative("The brain is working overtime! Sparks fly!", style="bold yellow")
        else:
            print_narrative("The machine hums quietly. All systems nominal.", style="bold green")
    except Exception as e:
        print_error(f"Cannot inspect system: {e}", "Some components may be hidden.")