# receive.py
import socket
import time
import json
from zeroconf import Zeroconf, ServiceBrowser
import operations
import resume
import logger
import network
import name_generator
import protocol
from design import (get_live_display, print_narrative, print_error, print_success,
                    print_warning, print_info, display_transfer_panel, display_connection_panel)

TCP_PORT = 5556
SERVICE_TYPE = "_cypher-share._tcp.local."

class ReceiverListener:
    def __init__(self, target_pin):
        self.target_pin = target_pin
        self.found_service = None
        self.metadata = None

    def add_service(self, zeroconf, type, name):
        try:
            info = zeroconf.get_service_info(type, name)
            if info:
                properties = info.properties
                pin = properties.get(b'pin', b'').decode()
                if pin == self.target_pin:
                    device = properties.get(b'device', b'unknown').decode()
                    if info.addresses:
                        ip = socket.inet_ntoa(info.addresses[0])
                    else:
                        ip = "unknown"
                    print_narrative(f"Found sender: {device} at {ip}")
                    self.found_service = (ip, info.port)
                    self.metadata = {
                        "total_files": properties.get(b'total_files', b'0').decode(),
                        "total_size": properties.get(b'total_size', b'0').decode(),
                    }
        except Exception as e:
            print_error(f"Error while browsing: {e}")

    def update_service(self, *args):
        pass

def start_receiver(pin):
    live = get_live_display()
    import threading
    live_thread = threading.Thread(target=live.start_live, daemon=True)
    live_thread.start()

    print_narrative(f"Scanning for sender with PIN {pin}...")
    zeroconf = Zeroconf()
    listener = ReceiverListener(pin)
    browser = ServiceBrowser(zeroconf, SERVICE_TYPE, listener)

    timeout = time.time() + 30
    try:
        while not listener.found_service and time.time() < timeout:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print_narrative("Scan interrupted.", style="bold red")
        zeroconf.close()
        live.stop()
        return
    except Exception as e:
        print_error(f"Discovery error: {e}")
        zeroconf.close()
        live.stop()
        return

    zeroconf.close()

    if not listener.found_service:
        print_narrative("No sender found with that PIN. The creature sleeps.", style="bold red")
        live.stop()
        return

    sender_ip, port = listener.found_service
    print_narrative(f"Connecting to sender at {sender_ip}:{port}...", style="bold blue")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((sender_ip, port))
    except Exception as e:
        print_error(f"Cannot connect to sender: {e}", "Is the sender still alive?")
        live.stop()
        return

    # Receive metadata
    try:
        metadata = protocol.recv_json(sock)
        if metadata is None:
            print_error("Sender closed connection during handshake.")
            sock.close()
            live.stop()
            return
    except Exception as e:
        print_error(f"Failed to receive manifest: {e}")
        sock.close()
        live.stop()
        return

    total_files = metadata["total_files"]
    total_size = metadata["total_size"]
    files = metadata["files"]
    sender_device = metadata["device"]

    display_transfer_panel(sender_device, pin, total_files, operations.human_readable_size(total_size), role="Receiver")

    # Prepare resume info
    resume_info = {}
    out_dir = operations.ensure_output_dir()
    for f in files:
        rel = f["rel_path"]
        target = out_dir / rel
        if target.exists():
            existing = target.stat().st_size
            if existing < f["size"]:
                resume_info[rel] = {"transferred": existing}
            elif existing == f["size"]:
                resume_info[rel] = {"transferred": f["size"]}
        else:
            resume_info[rel] = {"transferred": 0}

    resume_info["device"] = name_generator.generate_name()

    try:
        protocol.send_json(sock, resume_info)
    except Exception as e:
        print_error(f"Failed to send resume info: {e}")
        sock.close()
        live.stop()
        return

    # Update connection panel
    live.set_connection_panel(resume_info["device"], sender_device, network.get_local_ip(), sender_ip)

    # Initialize transfer stats
    live.update_transfer_stats(
        device=resume_info["device"],
        connected=sender_device,
        files_done=0,
        files_total=total_files,
        bytes_done=0,
        bytes_total=total_size,
        current_file='',
        current_size=0,
        current_done=0,
        speed=0,
        eta=timedelta(seconds=0)
    )

    bytes_received_total = 0
    files_done = 0
    start_time = time.time()

    for f in files:
        rel = f["rel_path"]
        size = f["size"]
        target = out_dir / rel
        offset = resume_info.get(rel, {}).get("transferred", 0)

        if offset >= size:
            bytes_received_total += size
            files_done += 1
            live.update_transfer_stats(
                files_done=files_done,
                bytes_done=bytes_received_total
            )
            continue

        live.update_transfer_stats(
            current_file=rel,
            current_size=size,
            current_done=offset
        )

        target.parent.mkdir(parents=True, exist_ok=True)
        mode = 'ab' if offset > 0 else 'wb'

        try:
            with open(target, mode) as fp:
                received = offset
                while received < size:
                    chunk = sock.recv(min(8192, size - received))
                    if not chunk:
                        break
                    fp.write(chunk)
                    received += len(chunk)
                    bytes_received_total += len(chunk)
                    elapsed = time.time() - start_time
                    speed = bytes_received_total / elapsed if elapsed > 0 else 0
                    remaining = total_size - bytes_received_total
                    eta_seconds = remaining / speed if speed > 0 else 0
                    live.update_transfer_stats(
                        bytes_done=bytes_received_total,
                        current_done=received,
                        speed=speed,
                        eta=timedelta(seconds=eta_seconds)
                    )
        except (ConnectionResetError, BrokenPipeError) as e:
            print_error(f"Connection lost while receiving {rel}.", "The sender may have disconnected.")
            resume.update_progress(rel, received, size)
            break
        except Exception as e:
            print_error(f"File {rel} reception failed: {e}")
            resume.update_progress(rel, received, size)
            break

        if received == size:
            files_done += 1
            live.update_transfer_stats(files_done=files_done)
            resume.update_progress(rel, size, size)

    elapsed = time.time() - start_time
    avg_speed = bytes_received_total / elapsed if elapsed > 0 else 0
    if bytes_received_total == total_size:
        print_success(f"All files received and saved to {out_dir} in {elapsed:.1f}s ({operations.human_readable_size(avg_speed)}/s).")
        logger.log_transfer(sender_device, resume_info["device"], [f["rel_path"] for f in files], "success")
    else:
        print_warning(f"Transfer incomplete: {operations.human_readable_size(bytes_received_total)} / {operations.human_readable_size(total_size)} received.")
        logger.log_transfer(sender_device, resume_info["device"], [f["rel_path"] for f in files], f"interrupted at {bytes_received_total} bytes")

    sock.close()
    live.stop()