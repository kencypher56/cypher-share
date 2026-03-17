import logging
from pathlib import Path
from design import print_narrative, print_error

LOG_FILE = Path.home() / "cypher-share.log"

try:
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
except Exception as e:
    print_error(f"Cannot set up logging: {e}", "Transfers will not be logged.")

def log_transfer(sender, receiver, files, status="success", details=""):
    """Log transfer event to file and optionally console."""
    try:
        msg = f"Sender: {sender} | Receiver: {receiver} | Files: {files} | Status: {status}"
        if details:
            msg += f" | Details: {details}"
        logging.info(msg)
        # Also print narrative if status is not success
        if status != "success":
            print_narrative(f"[LOG] {msg}", style="dim")
    except Exception as e:
        print_error(f"Failed to write log: {e}")