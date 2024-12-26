import threading
import configparser
import os
import sys
import socket
import time

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception as e:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def check_network():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("8.8.8.8", 53))
        s.close()
        return True
    except OSError:
        return False

def broadcast_server(ip, port, multicast_group="224.0.0.1", interval=5):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    message = f"iperf3_server:{ip}:{port}".encode()
    while True:
        sock.sendto(message, (multicast_group, port))
        time.sleep(interval)

def get_default_interface_ip():
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

# Main Functionality
from iperf_server import IperfServer
from iperf_client import IperfClient

def load_config(config_file='config.ini'):
    config = configparser.ConfigParser()
    if not os.path.isfile(config_file):
        print(f"Config file {config_file} not found!")
        return None
    config.read(config_file)
    return config

def run_server(config):
    if check_network():
        server = IperfServer(config)
        multicast_group = config['settings']['multicast_group']
        multicast_interval = int(config['settings']['multicast_interval'])
        
        threading.Thread(target=broadcast_server, args=(server.server_ip, server.port, multicast_group, multicast_interval), daemon=True).start()
        server.run()
    else:
        print("Network check failed.")

def run_client(config):
    client = IperfClient()
    server_ip, server_port = listen_for_server(client.port)
    
    if server_ip:
        client.log(f"Found server via multicast: {server_ip}:{server_port}")
    else:
        client.log("No server found via multicast. Proceeding with manual input.")
        server_ip = input("Enter server IP manually: ")
        server_port = client.port

    client.run_test(server_ip)

if __name__ == "__main__":
    config = load_config()
    if config is None:
        sys.exit("Config file not found. Exiting.")
    
    mode = input("Enter mode (server/client): ").strip().lower()
    
    if mode == "server":
        run_server(config)
    elif mode == "client":
        run_client(config)
    else:
        print("Invalid mode. Please enter 'server' or 'client'.")