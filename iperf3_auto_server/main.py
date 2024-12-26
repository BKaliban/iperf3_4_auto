import threading
from iperf_server import IperfServer
from network_utils import broadcast_server

if __name__ == "__main__":
    server = IperfServer()
    
    multicast_group = server.config['settings']['multicast_group']
    multicast_interval = int(server.config['settings']['multicast_interval'])
    
    threading.Thread(target=broadcast_server, args=(server.server_ip, server.port, multicast_group, multicast_interval), daemon=True).start()
    
    server.run()