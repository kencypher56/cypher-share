# send.py
import socket
import time
from zeroconf import Zeroconf, ServiceInfo
import name_generator
import pin_generator
import operations
import resume
import logger
import network
import protocol
from datetime import timedelta
from design import get_live_display, print_narrative, print_error, print_success, print_warning

TCP_PORT = 5556
SERVICE_TYPE = "_cypher-share._tcp.local."

def start_sender(file_paths):
    if not file_paths:
        print_narrative("No files to send. The experiment lacks a subject.", style="yellow")
        return

    live = get_live_display()
    live.start()  # <-- FIXED: was start_live_thread

    try:
        device_name = name_generator.generate_name()
        pin = pin_generator.generate_pin()
        session_id = f"{int(time.time())}"
        local_ip = network.get_local_ip()

        file_list, total_size = operations.get_files_and_size(file_paths)
        if not file_list:
            print_error("No valid files selected.", "Check paths and permissions.")
            live.stop()
            return

        total_files = len(file_list)
        manifest = [{"rel_path": rel, "size": size} for rel, _, size in file_list]
        file_map = {rel: full for rel, full, size in file_list}

        print_narrative(f"I am [bold bright_cyan]{device_name}[/]. My PIN is [bold yellow]{pin}[/]")
        print_narrative(f"My local IP is {local_ip}", style="dim")
        live.set_doctor_message(f"I am {device_name}. PIN is {pin}. Broadcasting...")
        live.update_transfer_stats(device=device_name, pin=pin, local_ip=local_ip,
                                   files_total=total_files, bytes_total=total_size)

        logger.log_transfer_event('send_start', device_name, f"Total files: {total_files}, total size: {total_size}")

        # Zeroconf
        try:
            info = ServiceInfo(
                SERVICE_TYPE,
                f"{device_name}.{SERVICE_TYPE}",
                addresses=[socket.inet_aton(local_ip)],
                port=TCP_PORT,
                properties={
                    'pin': pin,
                    'device': device_name,
                    'session': session_id,
                    'total_size': str(total_size),
                    'total_files': str(total_files)
                },
                server=f"{device_name}.local."
            )
            zeroconf = Zeroconf()
            zeroconf.register_service(info)
        except Exception as e:
            print_error(f"Failed to announce the experiment: {e}", "Is another instance running?")
            live.stop()
            return

        # TCP server
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind(('', TCP_PORT))
            server.listen(1)
            server.settimeout(60)
        except Exception as e:
            print_error(f"Cannot open communication channel: {e}", "Port 5556 may be in use.")
            zeroconf.unregister_service(info)
            zeroconf.close()
            live.stop()
            return

        print_narrative("Waiting for a receiver to answer the call...", style="bold yellow")
        live.set_doctor_message("Waiting for receiver...")
        try:
            conn, addr = server.accept()
            print_narrative(f"Receiver connected from {addr}", style="bold blue")
            live.add_log(f"Receiver connected from {addr}", "bold blue")
        except socket.timeout:
            print_narrative("No receiver connected within 60 seconds. Aborting.", style="bold red")
            server.close()
            zeroconf.unregister_service(info)
            zeroconf.close()
            live.stop()
            return
        except Exception as e:
            print_error(f"Connection failed: {e}")
            server.close()
            zeroconf.unregister_service(info)
            zeroconf.close()
            live.stop()
            return

        # Send metadata
        metadata = {
            "total_files": total_files,
            "total_size": total_size,
            "files": manifest,
            "device": device_name,
            "pin": pin
        }
        try:
            protocol.send_json(conn, metadata)
        except Exception as e:
            print_error(f"Failed to send metadata: {e}")
            conn.close()
            server.close()
            zeroconf.unregister_service(info)
            zeroconf.close()
            live.stop()
            return

        # Receive resume info
        try:
            resume_data = protocol.recv_json(conn)
            if resume_data is None:
                print_error("Receiver closed connection during handshake.")
                conn.close()
                server.close()
                zeroconf.unregister_service(info)
                zeroconf.close()
                live.stop()
                return
            receiver_device = resume_data.get("device", "unknown")
        except Exception as e:
            print_error(f"Failed to receive resume info: {e}")
            conn.close()
            server.close()
            zeroconf.unregister_service(info)
            zeroconf.close()
            live.stop()
            return

        # Update connection panel
        live.set_connection_panel(device_name, receiver_device, local_ip, addr[0])
        live.set_doctor_message(f"Connected to {receiver_device}")
        live.update_transfer_stats(connected=receiver_device, remote_ip=addr[0])

        logger.log_transfer_event('send_connected', device_name, f"Connected to {receiver_device} at {addr[0]}")

        bytes_sent_total = 0
        files_done = 0
        start_time = time.time()

        for file_info in manifest:
            rel = file_info["rel_path"]
            size = file_info["size"]
            full_path = file_map[rel]

            offset = 0
            if resume_data and isinstance(resume_data, dict):
                offset = resume_data.get(rel, {}).get("transferred", 0)
            if offset > 0:
                print_narrative(f"Resuming {rel} from byte {offset}", style="yellow")
                logger.log_transfer_event('resume', device_name, f"Resuming {rel} from byte {offset}")

            live.update_transfer_stats(
                current_file=rel,
                current_size=size,
                current_done=offset
            )

            try:
                with open(full_path, 'rb') as f:
                    f.seek(offset)
                    sent = offset
                    while sent < size:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        conn.sendall(chunk)
                        sent += len(chunk)
                        bytes_sent_total += len(chunk)

                        elapsed = time.time() - start_time
                        speed = bytes_sent_total / elapsed if elapsed > 0 else 0
                        live.update_transfer_stats(
                            bytes_done=bytes_sent_total,
                            current_done=sent,
                            speed=speed,
                            eta=timedelta(seconds=(total_size - bytes_sent_total) / speed if speed > 0 else 0)
                        )
            except (BrokenPipeError, ConnectionResetError) as e:
                print_error(f"Connection lost while sending {rel}.", "The receiver may have disconnected.")
                resume.update_progress(rel, sent, size)
                logger.log_transfer_event('send_interrupt', device_name, f"Connection lost while sending {rel}")
                break
            except Exception as e:
                print_error(f"File {rel} transmission failed: {e}")
                resume.update_progress(rel, sent, size)
                logger.log_transfer_event('send_interrupt', device_name, f"File {rel} failed: {e}")
                break

            # File fully sent
            files_done += 1
            live.update_transfer_stats(
                files_done=files_done,
                current_done=size
            )
            resume.update_progress(rel, size, size)
            logger.log_file_transfer(rel, size, 'sent', receiver_device)

        elapsed = time.time() - start_time
        avg_speed = bytes_sent_total / elapsed if elapsed > 0 else 0
        if bytes_sent_total == total_size:
            print_success(f"All files sent. Creature delivered in {elapsed:.1f}s ({operations.human_readable_size(avg_speed)}/s).")
            logger.log_transfer_event('send_complete', device_name,
                                      f"All files sent in {elapsed:.1f}s, avg speed {operations.human_readable_size(avg_speed)}/s")
        else:
            print_warning(f"Transfer incomplete: {operations.human_readable_size(bytes_sent_total)} / {operations.human_readable_size(total_size)} sent.")
            logger.log_transfer_event('send_interrupt', device_name,
                                      f"Transfer incomplete: {bytes_sent_total}/{total_size} bytes")

        conn.close()
        server.close()
        zeroconf.unregister_service(info)
        zeroconf.close()
    except Exception as e:
        print_error(f"Unexpected catastrophe in sender: {e}", "The experiment has failed. Check logs.")
        logger.log_transfer_event('send_error', 'unknown', str(e))
    finally:
        live.stop()