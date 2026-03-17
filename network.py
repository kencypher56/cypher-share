# network.py
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        hostname = socket.gethostname()
        for addr in socket.gethostbyname_ex(hostname)[2]:
            if not addr.startswith("127."):
                return addr
        return "127.0.0.1"

def same_subnet(ip1, ip2, mask=24):
    try:
        base1 = ip1.rsplit('.', 1)[0]
        base2 = ip2.rsplit('.', 1)[0]
        return base1 == base2
    except:
        return False