# protocol.py
import json
import socket

def send_json(sock, obj):
    """Send a JSON object with a 4‑byte length prefix."""
    data = json.dumps(obj).encode('utf-8')
    length = len(data).to_bytes(4, 'big')
    sock.sendall(length + data)

def recv_exact(sock, n):
    """Receive exactly n bytes from the socket."""
    buffer = b''
    while len(buffer) < n:
        chunk = sock.recv(n - len(buffer))
        if not chunk:
            return None  # connection closed
        buffer += chunk
    return buffer

def recv_json(sock):
    """Receive a JSON object that was sent with send_json."""
    length_bytes = recv_exact(sock, 4)
    if length_bytes is None:
        return None
    length = int.from_bytes(length_bytes, 'big')
    data = recv_exact(sock, length)
    if data is None:
        return None
    return json.loads(data.decode('utf-8'))