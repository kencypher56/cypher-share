import qrcode
from rich.console import Console
from rich.text import Text

console = Console()

def generate_qr_ascii(data):
    qr = qrcode.QRCode()
    qr.add_data(data)
    qr.make()
    ascii_str = ""
    for row in qr.get_matrix():
        line = "".join(["██" if cell else "  " for cell in row])
        ascii_str += line + "\n"
    return ascii_str

def display_qr(pin, device_name=""):
    data = f"PIN:{pin}" + (f" NAME:{device_name}" if device_name else "")
    ascii_qr = generate_qr_ascii(data)
    console.print(Text(ascii_qr, style="bold bright_green"))