import os
import sys
import shutil
import subprocess
import socket
from datetime import datetime
import threading
import time
import ipaddress
from concurrent.futures import ThreadPoolExecutor

def ensure_tools_exist():
    tools_dir = os.path.join(os.environ['TEMP'], "tools")
    exe_path = os.path.join(tools_dir, "iperf3.exe")
    dll_path = os.path.join(tools_dir, "cygwin1.dll")

    if not os.path.exists(tools_dir):
        os.makedirs(tools_dir)

    if not os.path.exists(exe_path):
        src_exe = os.path.join(sys._MEIPASS, "tools", "iperf3.exe")
        print(f"[INFO] Extracting iperf3.exe to {exe_path}")
        shutil.copy(src_exe, exe_path)

    if not os.path.exists(dll_path):
        src_dll = os.path.join(sys._MEIPASS, "tools", "cygwin1.dll")
        print(f"[INFO] Extracting cygwin1.dll to {dll_path}")
        shutil.copy(src_dll, dll_path)

    if os.path.exists(exe_path) and os.path.exists(dll_path):
        print(f"[INFO] Tools extracted successfully to {tools_dir}")
    else:
        print(f"[ERROR] Tools extraction failed. Check permissions or source files.")

    return exe_path

def ensure_firewall_rule_exists():
    rule_name = "iperf3"
    rule_command_check = f'netsh advfirewall firewall show rule name="{rule_name}"'
    rule_command_add_tcp = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=allow protocol=TCP localport=5201'
    rule_command_add_udp = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=allow protocol=UDP localport=5201'
    rule_command_add_broadcast = f'netsh advfirewall firewall add rule name="{rule_name}_broadcast" dir=in action=allow protocol=UDP localport=50000'

    try:
        result = subprocess.run(rule_command_check, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "No rules match the specified criteria" in result.stdout:
            print("[INFO] Adding firewall rule for TCP port 5201")
            subprocess.run(rule_command_add_tcp, shell=True)
            print("[INFO] Adding firewall rule for UDP port 5201")
            subprocess.run(rule_command_add_udp, shell=True)
            print("[INFO] Adding firewall rule for UDP broadcast port 50000")
            subprocess.run(rule_command_add_broadcast, shell=True)
        else:
            print("[INFO] Firewall rule already exists.")
    except Exception as e:
        print(f"[ERROR] Could not ensure firewall rule: {e}")

def log(message, log_file):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] {message}"
    print(msg)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def start_broadcast(server_ip, port, log_file):
    addr = '<broadcast>'
    udp_port = 50000
    msg = f"{server_ip}:{port}".encode('utf-8')

    def broadcast():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            while True:
                try:
                    sock.sendto(msg, (addr, udp_port))
                    log(f"Broadcasting server info: {msg.decode()}", log_file)
                    time.sleep(1)  # Reduced delay to increase broadcast frequency
                except Exception as e:
                    log(f"Broadcast error: {e}", log_file)
                    break

    threading.Thread(target=broadcast, daemon=True).start()

def scan_ip(ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            result = sock.connect_ex((str(ip), port))
            if result == 0:
                return str(ip)
    except Exception:
        pass
    return None

def scan_subnet_for_server(subnet, port, log_file):
    log(f"Scanning subnet {subnet} for server...", log_file)
    found_ip = None
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ip = {executor.submit(scan_ip, ip, port): ip for ip in ipaddress.IPv4Network(subnet, strict=False)}
        for future in future_to_ip:
            ip = future_to_ip[future]
            try:
                result = future.result()
                if result:
                    found_ip = result
                    break
            except Exception as e:
                log(f"Error scanning IP {ip}: {e}", log_file)
    if found_ip:
        log(f"Found server at {found_ip}:{port}", log_file)
        return found_ip, port
    log(f"No server found in subnet {subnet}", log_file)
    return None, None

def listen_for_broadcast(log_file, timeout=30):
    udp_port = 50000
    log("Listening for server broadcasts...", log_file)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('', udp_port))
        sock.settimeout(timeout)
        try:
            while True:
                data, addr = sock.recvfrom(1024)
                info = data.decode('utf-8')
                log(f"Received broadcast from {addr}: {info}", log_file)
                server_ip, server_port = info.split(":")
                return server_ip, int(server_port)
        except socket.timeout:
            log("Broadcast listening timed out.", log_file)
            return None, None

def animated_indicator(message, stop_event):
    symbols = ['/', '\\']
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{message} {symbols[idx]} ")
        sys.stdout.flush()
        idx = (idx + 1) % len(symbols)
        time.sleep(0.5)
    sys.stdout.write(f"\r{message} Done ✅\n")
    sys.stdout.flush()

def perform_network_diagnostics(target_ip, log_file):
    def log_diagnostic(message):
        log(message, log_file)

    ping_result = subprocess.run(['ping', '-n', '4', target_ip], capture_output=True, text=True)
    log_diagnostic(f"Ping results:\n{ping_result.stdout}")

    tracert_result = subprocess.run(['tracert', '-d', '-h', '15', target_ip], capture_output=True, text=True)
    log_diagnostic(f"Route trace:\n{tracert_result.stdout}")

    mtus = [1500, 1492, 1472, 1452, 1442]
    for mtu in mtus:
        ping_mtu = subprocess.run(['ping', '-n', '1', '-f', '-l', str(mtu), target_ip], capture_output=True, text=True)
        if "Packet needs to be fragmented" not in ping_mtu.stderr:
            log_diagnostic(f"Max MTU: {mtu}")
            break

def start_server():
    log_file = os.path.join(os.environ['TEMP'], "iperf3_server_log.txt")
    ensure_firewall_rule_exists()
    log("Starting iPerf3 server...", log_file)
    tools_dir = os.path.join(os.environ['TEMP'], "tools")
    exe_path = os.path.join(tools_dir, "iperf3.exe")

    if not os.path.exists(exe_path):
        log("iperf3.exe not found. Ensure tools are correctly extracted.", log_file)
        return

    server_ip = get_local_ip()
    port = 5201
    start_broadcast(server_ip, port, log_file)

    log(f"Starting iPerf3 server on {server_ip}:{port}", log_file)
    try:
        proc = subprocess.Popen(
            [exe_path, "-s", "-p", str(port), "-i", "1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        with open(log_file, "a", encoding="utf-8") as log_output:
            while True:
                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break
                if line:
                    log_output.write(line)
    except KeyboardInterrupt:
        log("Server stopping due to KeyboardInterrupt...", log_file)
    except Exception as e:
        log(f"Error running server: {e}", log_file)

def start_client():
    log_file = os.path.join(os.environ['TEMP'], "iperf3_client_log.txt")
    ensure_firewall_rule_exists()
    log("Starting iPerf3 client...", log_file)
    tools_dir = os.path.join(os.environ['TEMP'], "tools")
    exe_path = os.path.join(tools_dir, "iperf3.exe")

    if not os.path.exists(exe_path):
        log("iperf3.exe not found. Ensure tools are correctly extracted.", log_file)
        return

    test_count = 1
    while True:
        try:
            test_count = int(input("Enter the number of test cycles: "))
            if test_count > 0:
                break
            else:
                print("Please enter a number greater than 0.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

    server_ip, server_port = listen_for_broadcast(log_file)
    if not server_ip:
        subnet = '.'.join(get_local_ip().split('.')[:3]) + '.0/24'
        server_ip, server_port = scan_subnet_for_server(subnet, 5201, log_file)

    if not server_ip:
        server_ip = input("Server not found via broadcast. Enter the server IP address: ")
        server_port = 5201

    log(f"Attempting to connect to server at {server_ip}:{server_port}", log_file)
    perform_network_diagnostics(server_ip, log_file)

    try:
        for i in range(test_count):
            stop_event = threading.Event()
            message = f"Running iperf3 to the server in normal mode"
            indicator_thread = threading.Thread(target=animated_indicator, args=(message, stop_event), daemon=True)
            indicator_thread.start()

            proc = subprocess.Popen(
                [exe_path, "-c", server_ip, "-p", str(server_port), "-t", "60", "-i", "1"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            with open(log_file.replace("_client", "_iperf"), "a", encoding="utf-8") as iperf_log:
                while proc.poll() is None:
                    line = proc.stdout.readline()
                    if line:
                        iperf_log.write(line)
                proc.wait()
            stop_event.set()
            indicator_thread.join()

            stop_event = threading.Event()
            message = f"Running iperf3 to the server in reverse mode"
            indicator_thread = threading.Thread(target=animated_indicator, args=(message, stop_event), daemon=True)
            indicator_thread.start()

            proc = subprocess.Popen(
                [exe_path, "-c", server_ip, "-p", str(server_port), "-t", "60", "-i", "1", "--reverse"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            with open(log_file.replace("_client", "_iperf"), "a", encoding="utf-8") as iperf_log:
                while proc.poll() is None:
                    line = proc.stdout.readline()
                    if line:
                        iperf_log.write(line)
                proc.wait()
            stop_event.set()
            indicator_thread.join()

        log("Test completed. Opening log file...", log_file)
        os.startfile(log_file.replace("_client", "_iperf"))
    except Exception as e:
        log(f"Error running client: {e}", log_file)

if __name__ == "__main__":
    ensure_tools_exist()

    while True:
        print("========================================")
        print("|                iPerf3                |")
        print("========================================")
        print("|   1. Start Server                    |")
        print("|   2. Start Client                    |")
        print("|   0. Exit                            |")
        print("========================================")

        try:
            choice = int(input("Enter your choice (1/2/0): "))
            if choice == 1:
                start_server()
            elif choice == 2:
                start_client()
            elif choice == 0:
                log("Exiting... Goodbye!", os.path.join(os.environ['TEMP'], "iperf3_client_log.txt"))
                sys.exit(0)
            else:
                print("Invalid choice. Please enter 1, 2, or 0.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")