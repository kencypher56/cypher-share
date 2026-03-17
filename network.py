import socket

def get_local_ip():
    """Get the local IP address that can reach the internet (or a fallback)."""
    try:
        # Connect to a public DNS server to determine the interface IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # Fallback: get all addresses and pick the first non‑loopback IPv4
        hostname = socket.gethostname()
        for addr in socket.gethostbyname_ex(hostname)[2]:
            if not addr.startswith("127."):
                return addr
        return "127.0.0.1"

def same_subnet(ip1, ip2, mask=24):
    """Check if two IPs are on the same /24 network (simple check)."""
    try:
        a1 = int(ip1.split('.')[3])  # last octet
        base1 = ip1.rsplit('.', 1)[0]
        base2 = ip2.rsplit('.', 1)[0]
        return base1 == base2
    except:
        return False