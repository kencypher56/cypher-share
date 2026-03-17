# protocol.py
import json
import socket

def send_json(sock, obj):
    data = json.dumps(obj).encode('utf-8')
    length = len(data).to_bytes(4, 'big')
    sock.sendall(length + data)

def recv_exact(sock, n):
    buffer = b''
    while len(buffer) < n:
        chunk = sock.recv(n - len(buffer))
        if not chunk:
            return None
        buffer += chunk
    return buffer

def recv_json(sock):
    length_bytes = recv_exact(sock, 4)
    if length_bytes is None:
        return None
    length = int.from_bytes(length_bytes, 'big')
    data = recv_exact(sock, length)
    if data is None:
        return None
    return json.loads(data.decode('utf-8'))