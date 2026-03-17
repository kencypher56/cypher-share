# design.py
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.table import Table
from rich import print as rprint
import time
import random
from datetime import timedelta
import threading
from collections import deque

console = Console(emoji=True)

# Emoji constants
EMOJI_DOCTOR = "🧪"
EMOJI_ERROR = "💀"
EMOJI_WARNING = "⚠️"
EMOJI_SUCCESS = "✅"
EMOJI_INFO = "📡"
EMOJI_LAB = "🔬"
EMOJI_LIGHTNING = "⚡"
EMOJI_CREATURE = "🧟"
EMOJI_PIN = "🔑"
EMOJI_FILE = "📄"
EMOJI_FOLDER = "📁"
EMOJI_NETWORK = "🌐"
EMOJI_CLOCK = "⏳"
EMOJI_SPARK = "✨"

# RGB color cycler for animated bar
def rgb_cycle(step=0):
    """Generate RGB colors in a smooth cycle."""
    r = (step % 256)
    g = ((step + 85) % 256)
    b = ((step + 170) % 256)
    return f"#{r:02x}{g:02x}{b:02x}"

def _make_static_banner():
    """Return a panel containing the static banner."""
    banner_text = Text("""
╔══════════════════════════════════════════════╗
║     ██████╗██╗   ██╗██████╗ ██╗  ██╗███████╗██████╗  ║
║    ██╔════╝╚██╗ ██╔╝██╔══██╗██║  ██║██╔════╝██╔══██╗ ║
║    ██║      ╚████╔╝ ██████╔╝███████║█████╗  ██████╔╝ ║
║    ██║       ╚██╔╝  ██╔═══╝ ██╔══██║██╔══╝  ██╔══██╗ ║
║    ╚██████╗   ██║   ██║     ██║  ██║███████╗██║  ██║ ║
║     ╚═════╝   ╚═╝   ╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ║
║                                                      ║
║           Peer-to-Peer File Transfer                ║
║           with a 6‑digit PIN handshake              ║
╚══════════════════════════════════════════════╝
    """, style="bold bright_red")
    return Panel(banner_text, style="red")

def show_banner():
    """Display the banner independently of the live display."""
    console.print(_make_static_banner())

class LiveDisplay:
    """Manages the live updating layout with animated progress."""
    def __init__(self):
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="banner", size=12),
            Layout(name="doctor", size=3),
            Layout(name="panels", size=8),
            Layout(name="transfer", size=6),
            Layout(name="logs", size=8),
        )
        self.layout["banner"].update(_make_static_banner())
        self.layout["doctor"].update(Panel("[🧪 Doctor] Initializing...", style="bold yellow"))
        self.layout["panels"].update(Panel("Waiting for connection...", style="blue"))
        self.layout["transfer"].update(Panel("No transfer in progress", style="dim"))
        self.layout["logs"].update(Panel("Logs will appear here", style="dim"))

        self.logs = deque(maxlen=10)
        self.transfer_stats = {
            'device': '?',
            'connected': '?',
            'files_done': 0,
            'files_total': 0,
            'bytes_done': 0,
            'bytes_total': 0,
            'current_file': '',
            'current_size': 0,
            'current_done': 0,
            'speed': 0,
            'eta': timedelta(seconds=0)
        }
        self.animation_step = 0
        self._running = True
        self._lock = threading.Lock()

    def add_log(self, message, style="yellow", prefix="[🧪 Doctor]"):
        """Add a log message to the scrolling log panel."""
        timestamp = time.strftime("%H:%M:%S")
        with self._lock:
            self.logs.append(f"[{timestamp}] {prefix} {message}")
        self._update_logs()

    def _update_logs(self):
        """Refresh the log panel with current logs."""
        log_text = "\n".join(self.logs)
        self.layout["logs"].update(Panel(log_text, title="📜 Laboratory Logs", style="bright_black"))

    def set_doctor_message(self, message):
        """Update the doctor dialogue panel."""
        self.layout["doctor"].update(Panel(f"{EMOJI_DOCTOR} {message}", style="bold yellow"))

    def set_connection_panel(self, local_device, remote_device, local_ip, remote_ip):
        """Update the connection info panel."""
        content = (
            f"{EMOJI_NETWORK} [bold green]Local:[/] {local_device} ({local_ip})\n"
            f"{EMOJI_NETWORK} [bold yellow]Remote:[/] {remote_device} ({remote_ip})"
        )
        self.layout["panels"].update(Panel(content, title="🔌 Neural Link", style="blue"))

    def update_transfer_stats(self, **kwargs):
        """Update transfer statistics."""
        with self._lock:
            for k, v in kwargs.items():
                if k in self.transfer_stats:
                    self.transfer_stats[k] = v
        self._update_transfer_panel()

    def _update_transfer_panel(self):
        """Render the animated transfer panel."""
        s = self.transfer_stats
        # Build the animated bar
        if s['bytes_total'] > 0:
            overall_pct = s['bytes_done'] / s['bytes_total']
        else:
            overall_pct = 0
        if s['current_size'] > 0:
            file_pct = s['current_done'] / s['current_size']
        else:
            file_pct = 0

        # Create RGB‑shifting bar characters
        bar_length = 40
        self.animation_step += 1
        bar_chars = []
        for i in range(bar_length):
            # each character gets a different colour based on position + animation step
            color = rgb_cycle(self.animation_step + i * 5)
            bar_chars.append(f"[{color}]█[/]")

        # Build the overall bar
        filled = int(overall_pct * bar_length)
        overall_bar = "".join(bar_chars[:filled]) + "─" * (bar_length - filled)

        # Build the current file bar (shorter)
        file_bar_length = 30
        file_filled = int(file_pct * file_bar_length)
        file_bar_chars = bar_chars[:file_bar_length]  # reuse same colors
        file_bar = "".join(file_bar_chars[:file_filled]) + "─" * (file_bar_length - file_filled)

        # Human readable sizes
        done_hr = self._hr(s['bytes_done'])
        total_hr = self._hr(s['bytes_total'])
        current_done_hr = self._hr(s['current_done'])
        current_total_hr = self._hr(s['current_size'])
        speed_hr = self._hr(s['speed']) + "/s"
        eta_str = str(s['eta']).split('.')[0]  # remove microseconds

        content = f"""
{EMOJI_CREATURE} Device      : {s['device']}
🔗 Connected   : {s['connected']}

📁 Files       : {s['files_done']} / {s['files_total']} ({(s['files_total'] - s['files_done'])} remaining)
💾 Total       : {done_hr} / {total_hr}

📄 Current     : {s['current_file']}
   Progress    : {file_bar} {int(file_pct*100)}%
   File bytes  : {current_done_hr} / {current_total_hr}
⚡ Speed       : {speed_hr}
⏳ ETA         : {eta_str}

   Overall     : {overall_bar} {int(overall_pct*100)}%
"""
        self.layout["transfer"].update(Panel(content, title="⚡ TRANSFER IN PROGRESS ⚡", style="bright_green"))

    def _hr(self, num):
        """Convert bytes to human readable."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if num < 1024.0:
                return f"{num:.1f}{unit}"
            num /= 1024.0
        return f"{num:.1f}PB"

    def start_live(self):
        """Start the live display (call in main thread)."""
        with Live(self.layout, refresh_per_second=10, screen=True) as live:
            while self._running:
                # Periodically refresh to animate bar
                self._update_transfer_panel()
                live.update(self.layout)
                time.sleep(0.1)

    def stop(self):
        """Stop the live display."""
        self._running = False

# Global instance (singleton)
_live_display = None

def get_live_display():
    global _live_display
    if _live_display is None:
        _live_display = LiveDisplay()
    return _live_display

def print_narrative(message, style="bold yellow", prefix="[🧪 Doctor]"):
    """Add a log line to the live display (if active) or print normally."""
    if _live_display:
        _live_display.add_log(message, style, prefix)
    else:
        console.print(f"{prefix} {message}", style=style)

def print_error(message, suggestion=""):
    """Print error with emoji."""
    console.print(f"[bold red]{EMOJI_ERROR} ERROR: {message}[/]")
    if suggestion:
        console.print(f"[bold yellow]{EMOJI_LIGHTNING} Suggestion: {suggestion}[/]")
    if _live_display:
        _live_display.add_log(f"{EMOJI_ERROR} {message}", "bold red", "[💀]")

def print_success(message):
    console.print(f"[bold green]{EMOJI_SUCCESS} {message}[/]")
    if _live_display:
        _live_display.add_log(f"{EMOJI_SUCCESS} {message}", "bold green", "[✅]")

def print_warning(message):
    console.print(f"[bold yellow]{EMOJI_WARNING} {message}[/]")
    if _live_display:
        _live_display.add_log(f"{EMOJI_WARNING} {message}", "bold yellow", "[⚠️]")

def print_info(message):
    console.print(f"[bold cyan]{EMOJI_INFO} {message}[/]")
    if _live_display:
        _live_display.add_log(f"{EMOJI_INFO} {message}", "cyan", "[📡]")

def animate_sparks(duration=2):
    with console.status(f"[bold red]Frankenstein's lab awakens... {EMOJI_LIGHTNING}", spinner="dots12") as status:
        time.sleep(duration)

def display_transfer_panel(device_name, pin, total_files, total_size_human, role="Sender"):
    """Used before live display starts, prints a panel."""
    panel = Panel(
        f"{EMOJI_LAB} [bold cyan]Device:[/] {device_name}\n"
        f"{EMOJI_PIN} [bold yellow]PIN:[/] {pin}\n"
        f"{EMOJI_FILE} [bold]Files:[/] {total_files}\n"
        f"{EMOJI_FOLDER} [bold]Total:[/] {total_size_human}",
        title=f"[bold red]{EMOJI_LIGHTNING} {role} Experiment {EMOJI_LIGHTNING}[/]",
        border_style="bright_red",
        padding=(1, 2)
    )
    console.print(panel)

def display_connection_panel(local_device, remote_device, local_ip, remote_ip):
    """Update the live connection panel if live display active."""
    if _live_display:
        _live_display.set_connection_panel(local_device, remote_device, local_ip, remote_ip)