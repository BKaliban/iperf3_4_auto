import sys
from network_utils import listen_for_server
from iperf_client import IperfClient

if __name__ == "__main__":
    client = IperfClient()

    # Try to listen for a server using multicast
    server_ip, server_port = listen_for_server(client.port)
    if server_ip:
        client.log(f"Found server via multicast: {server_ip}:{server_port}")
    else:
        client.log("No server found via multicast. Proceeding with manual input.")
        server_ip = input("Enter server IP manually: ")
        server_port = client.port

    client.run_test(server_ip)