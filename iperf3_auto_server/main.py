import threading
import configparser
import os
import sys
from iperf_server import IperfServer
from network_utils import broadcast_server, check_network

def load_config(config_file='config.ini'):
    config = configparser.ConfigParser()
    if not os.path.isfile(config_file):
        print(f"Config file {config_file} not found!")
        return None
    config.read(config_file)
    return config

if __name__ == "__main__":
    config = load_config()
    if config is None:
        sys.exit("Config file not found. Exiting.")
    
    print(config.sections())
    print(config['settings'])

    if check_network():
        server = IperfServer(config)
        
        multicast_group = config['settings']['multicast_group']
        multicast_interval = int(config['settings']['multicast_interval'])
        
        threading.Thread(target=broadcast_server, args=(server.server_ip, server.port, multicast_group, multicast_interval), daemon=True).start()
        
        server.run()
    else:
        print("Network check failed.")