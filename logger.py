# logger.py
import logging
from pathlib import Path
from design import print_narrative, print_error

LOG_FILE = Path.home() / "cypher-share.log"

# Configure logging
try:
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
except Exception as e:
    print_error(f"Cannot set up logging: {e}", "Transfers will not be logged to file.")

def log_transfer_event(event_type, device, details):
    """
    Log a transfer event.
    event_type: 'send_start', 'send_complete', 'send_interrupt',
                'receive_start', 'receive_complete', 'receive_interrupt',
                'file_sent', 'file_received', 'resume'
    device: device name or IP
    details: additional info (filename, size, etc.)
    """
    try:
        msg = f"{event_type.upper()} | Device: {device} | {details}"
        logging.info(msg)
        # Also print to UI logs
        print_narrative(msg, style="dim")
    except Exception as e:
        print_error(f"Failed to write log: {e}")

def log_file_transfer(file_path, size, status, device):
    """Log a single file transfer."""
    try:
        msg = f"FILE {status.upper()} | {file_path} ({size} bytes) | Device: {device}"
        logging.info(msg)
        print_narrative(msg, style="dim")
    except Exception as e:
        print_error(f"Failed to write file log: {e}")