import threading
import configparser
import os
import sys
from iperf_server import IperfServer
from iperf_client import IperfClient
from network_utils import broadcast_server, listen_for_server, check_network

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