import socket

def get_local_ip():
    """Get the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception as e:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def broadcast_server(ip, port, multicast_group="224.0.0.1", interval=5):
    """Broadcast server information to clients in a multicast group."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    message = f"iperf3_server:{ip}:{port}".encode()

    while True:
        sock.sendto(message, (multicast_group, port))
        time.sleep(interval)