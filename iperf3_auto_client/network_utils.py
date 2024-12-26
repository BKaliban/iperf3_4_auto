import socket
import configparser

def get_default_interface_ip():
    """
    Returns the IP address of the default network interface (the first non-localhost IP address).
    """
    try:
        host_name = socket.gethostname()
        ip_list = socket.gethostbyname_ex(host_name)[2]
        for ip in ip_list:
            if not ip.startswith("127."):
                return ip
        return ip_list[0]
    except Exception as e:
        print(f"Error getting default interface IP: {str(e)}")
        return None

def listen_for_server(port=5201, timeout=10):
    multicast_group = "224.0.0.1"
    local_ip = get_default_interface_ip()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", port))
    
    group = socket.inet_aton(multicast_group) + socket.inet_aton(local_ip)
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, group)
        print(f"Joined multicast group {multicast_group} on {local_ip}")
    except OSError as e:
        print(f"Failed to join multicast group: {e}")
        return None, None
    
    sock.settimeout(timeout)
    try:
        while True:
            data, address = sock.recvfrom(1024)
            print(f"Received message from {address}: {data.decode()}")
            if data.startswith(b"iperf3_server:"):
                _, ip, server_port = data.decode().split(":")
                return ip, int(server_port)
    except socket.timeout:
        print("Timeout while listening for server")
        return None, None