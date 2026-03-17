# design.py
import time
import threading
from collections import deque
from datetime import timedelta
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
import shutil

console = Console(emoji=True)

# ========== Emoji & Theme Constants ==========
EMOJI_DOCTOR = "🧪"
EMOJI_CREATURE = "🧟"
EMOJI_ERROR = "💀"
EMOJI_WARNING = "⚠️"
EMOJI_SUCCESS = "✅"
EMOJI_INFO = "📡"
EMOJI_LAB = "🔬"
EMOJI_LIGHTNING = "⚡"
EMOJI_PIN = "🔑"
EMOJI_FILE = "📄"
EMOJI_FOLDER = "📁"
EMOJI_NETWORK = "🌐"
EMOJI_CLOCK = "⏳"

def rgb_cycle(step=0):
    """Generate an RGB hex color that cycles with step."""
    r = (step % 256)
    g = ((step + 85) % 256)
    b = ((step + 170) % 256)
    return f"#{r:02x}{g:02x}{b:02x}"

def get_terminal_size():
    """Return (width, height) of terminal."""
    return shutil.get_terminal_size((100, 30))

# ========== Banner (dynamic) ==========
def _make_banner(width):
    """Create a banner panel that fits the terminal width."""
    title = Text("⚡ CYPHER-SHARE ⚡", style="bold bright_red")
    subtitle = Text("Peer-to-Peer File Transfer with 6-digit PIN", style="dim white")
    banner = Panel(
        Align.center(Text.assemble(title, "\n", subtitle)),
        style="red",
        border_style="bright_red"
    )
    return banner

def show_banner():
    width, _ = get_terminal_size()
    console.print(_make_banner(width))

# ========== Live Display Class (Event-Driven) ==========
class LiveDisplay:
    def __init__(self):
        self.width, self.height = get_terminal_size()
        self.layout = Layout()
        # Define split proportions (relative sizes)
        self.layout.split_column(
            Layout(name="banner", ratio=1),
            Layout(name="doctor", ratio=1),
            Layout(name="panels", ratio=2),
            Layout(name="transfer", ratio=3),
            Layout(name="logs", ratio=2),
        )
        self.update_banner()
        self.layout["doctor"].update(Panel(f"{EMOJI_DOCTOR} Initializing...", style="bold yellow"))
        self.layout["panels"].update(Panel("Waiting for connection...", style="blue"))
        self.layout["transfer"].update(Panel("No transfer in progress", style="dim"))
        self.layout["logs"].update(Panel("Logs will appear here", style="dim"))

        self.logs = []               # store all logs (for history)
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
            'eta': timedelta(seconds=0),
            'pin': '',
            'local_ip': '',
            'remote_ip': ''
        }
        self.animation_step = 0
        self._running = True
        self._lock = threading.Lock()
        self._condition = threading.Condition()
        self._thread = None
        self._live = None

    def check_resize(self):
        """Check if terminal size changed, and update banner and bar lengths."""
        new_width, new_height = get_terminal_size()
        if new_width != self.width or new_height != self.height:
            self.width, self.height = new_width, new_height
            self.update_banner()
            self._update_logs()
            self._update_transfer_panel()
            self.refresh()

    def update_banner(self):
        self.layout["banner"].update(_make_banner(self.width))

    def add_log(self, message, style="yellow", prefix=f"[{EMOJI_DOCTOR} Doctor]"):
        timestamp = time.strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {prefix} {message}"
        with self._lock:
            self.logs.append(formatted)
        self._update_logs()
        self.refresh()

    def _get_log_panel_height(self):
        """Estimate how many lines can fit in the logs panel."""
        ratio_sum = 1+1+2+3+2  # 9
        panel_share = 2 / ratio_sum
        available_lines = int(self.height * panel_share) - 2  # subtract title & bottom border
        return max(1, available_lines)

    def _update_logs(self):
        """Update logs panel with as many recent logs as fit."""
        max_lines = self._get_log_panel_height()
        recent = self.logs[-max_lines:] if len(self.logs) > max_lines else self.logs
        log_text = "\n".join(recent)
        self.layout["logs"].update(Panel(log_text, title="📜 Laboratory Logs", style="bright_black"))

    def set_doctor_message(self, message):
        self.layout["doctor"].update(Panel(f"{EMOJI_DOCTOR} {message}", style="bold yellow"))
        self.refresh()

    def set_connection_panel(self, local_device, remote_device, local_ip, remote_ip):
        self.transfer_stats['connected'] = remote_device
        self.transfer_stats['local_ip'] = local_ip
        self.transfer_stats['remote_ip'] = remote_ip
        self._update_panels()
        self.refresh()

    def _update_panels(self):
        s = self.transfer_stats
        content = (
            f"{EMOJI_NETWORK} [bold green]Local:[/] {s['device']} ({s['local_ip']})\n"
            f"{EMOJI_NETWORK} [bold yellow]Remote:[/] {s['connected']} ({s['remote_ip']})\n"
            f"{EMOJI_PIN} [bold]PIN:[/] {s['pin']}"
        )
        self.layout["panels"].update(Panel(content, title="🔌 Neural Link", style="blue"))

    def update_transfer_stats(self, **kwargs):
        with self._lock:
            for k, v in kwargs.items():
                if k in self.transfer_stats:
                    self.transfer_stats[k] = v
        self._update_transfer_panel()
        self._update_panels()
        self.refresh()

    def _update_transfer_panel(self):
        s = self.transfer_stats
        if s['bytes_total'] > 0:
            overall_pct = s['bytes_done'] / s['bytes_total']
        else:
            overall_pct = 0
        if s['current_size'] > 0:
            file_pct = s['current_done'] / s['current_size']
        else:
            file_pct = 0

        bar_length = max(20, min(60, self.width - 30))
        self.animation_step += 1
        bar_chars = []
        for i in range(bar_length):
            color = rgb_cycle(self.animation_step + i * 5)
            bar_chars.append(f"[{color}]█[/]")

        filled = int(overall_pct * bar_length)
        overall_bar = "".join(bar_chars[:filled]) + "─" * (bar_length - filled)

        file_bar_length = max(15, min(40, self.width - 40))
        file_filled = int(file_pct * file_bar_length)
        file_bar_chars = bar_chars[:file_bar_length]
        file_bar = "".join(file_bar_chars[:file_filled]) + "─" * (file_bar_length - file_filled)

        def hr(num):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if num < 1024.0:
                    return f"{num:.1f}{unit}"
                num /= 1024.0
            return f"{num:.1f}PB"

        done_hr = hr(s['bytes_done'])
        total_hr = hr(s['bytes_total'])
        current_done_hr = hr(s['current_done'])
        current_total_hr = hr(s['current_size'])
        speed_hr = hr(s['speed']) + "/s"
        eta_str = str(s['eta']).split('.')[0]
        files_remaining = s['files_total'] - s['files_done']
        bytes_remaining = s['bytes_total'] - s['bytes_done']
        bytes_remaining_hr = hr(bytes_remaining)

        content = f"""
{EMOJI_CREATURE} Device      : {s['device']}
🔗 Connected   : {s['connected']}

📁 Files       : {s['files_done']} / {s['files_total']} ({files_remaining} remaining)
💾 Total       : {done_hr} / {total_hr} ({bytes_remaining_hr} remaining)

📄 Current     : {s['current_file']}
   Progress    : {file_bar} {int(file_pct*100)}%
   File bytes  : {current_done_hr} / {current_total_hr}
⚡ Speed       : {speed_hr}
⏳ ETA         : {eta_str}

   Overall     : {overall_bar} {int(overall_pct*100)}%
"""
        self.layout["transfer"].update(Panel(content, title="⚡ TRANSFER IN PROGRESS ⚡", style="bright_green"))

    def start(self):
        """Start the live display in a background thread (call once)."""
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        with Live(self.layout, refresh_per_second=10, screen=True) as live:
            self._live = live
            while self._running:
                with self._condition:
                    self._condition.wait()
                live.update(self.layout)

    def refresh(self):
        """Request a UI refresh (called from main thread after changes)."""
        if self._live:
            with self._condition:
                self._condition.notify()

    def stop(self):
        """Stop the live display and wait for thread to finish."""
        self._running = False
        self.refresh()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

# Global instance
_live_display = None

def get_live_display():
    global _live_display
    if _live_display is None:
        _live_display = LiveDisplay()
    return _live_display

# ========== Narrative print functions ==========
def print_narrative(message, style="bold yellow", prefix=f"[{EMOJI_DOCTOR} Doctor]"):
    if _live_display and _live_display._running:
        _live_display.add_log(message, style, prefix)
    else:
        console.print(f"{prefix} {message}", style=style)

def print_error(message, suggestion=""):
    console.print(f"[bold red]{EMOJI_ERROR} ERROR: {message}[/]")
    if suggestion:
        console.print(f"[bold yellow]{EMOJI_LIGHTNING} Suggestion: {suggestion}[/]")
    if _live_display and _live_display._running:
        _live_display.add_log(f"{EMOJI_ERROR} {message}", "bold red", "[💀]")

def print_success(message):
    console.print(f"[bold green]{EMOJI_SUCCESS} {message}[/]")
    if _live_display and _live_display._running:
        _live_display.add_log(f"{EMOJI_SUCCESS} {message}", "bold green", "[✅]")

def print_warning(message):
    console.print(f"[bold yellow]{EMOJI_WARNING} {message}[/]")
    if _live_display and _live_display._running:
        _live_display.add_log(f"{EMOJI_WARNING} {message}", "bold yellow", "[⚠️]")

def print_info(message):
    console.print(f"[bold cyan]{EMOJI_INFO} {message}[/]")
    if _live_display and _live_display._running:
        _live_display.add_log(f"{EMOJI_INFO} {message}", "cyan", "[📡]")

def animate_sparks(duration=2):
    with console.status(f"[bold red]Frankenstein's lab awakens... {EMOJI_LIGHTNING}", spinner="dots12") as status:
        time.sleep(duration)