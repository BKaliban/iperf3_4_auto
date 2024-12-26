import os
import sys
import subprocess
import zipfile
import tempfile
import requests
from datetime import datetime
from logger import setup_logger
from network_utils import get_local_ip

class IperfServer:
    def __init__(self, config):
        self.config = config
        self.log_file = self.config['settings']['log_file']
        self.logger = setup_logger(self.log_file)
        
        self.temp_dir = tempfile.gettempdir()
        self.tools_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools")
        self.port = int(self.config['settings']['port'])
        self.server_ip = get_local_ip()
        self.iperf_path = self.setup_iperf()
        self.firewall_rule_name = "iperf3"

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.logger.info(log_message)

    def setup_iperf(self):
        iperf_path = self.config['settings']['iperf_path']
        cygwin_dll_path = self.config['settings']['cygwin_dll_path']

        os.makedirs(self.tools_dir, exist_ok=True)

        if not os.path.exists(iperf_path) or not os.path.exists(cygwin_dll_path):
            try:
                self.log("Downloading iperf3...")
                url = self.config['settings']['iperf_url']
                response = requests.get(url)
                
                zip_path = os.path.join(self.temp_dir, "iperf.zip")
                with open(zip_path, "wb") as f:
                    f.write(response.content)
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(self.tools_dir)
                
                os.remove(zip_path)
                self.log(f"iperf3 and cygwin1.dll downloaded and extracted to {self.tools_dir}")
            except Exception as e:
                self.log(f"Error downloading iperf3: {e}")
                sys.exit(1)

        if not os.path.exists(iperf_path):
            self.log(f"Error: iperf3.exe not found at {iperf_path}")
            sys.exit(1)

        if not os.path.exists(cygwin_dll_path):
            self.log(f"Error: cygwin1.dll not found at {cygwin_dll_path}")
            sys.exit(1)

        return iperf_path

    def add_firewall_rule(self):
        self.log("Checking if firewall rule exists...")
        check_command = 'netsh advfirewall firewall show rule name="iperf3"'
        try:
            check_process = subprocess.run(check_command, shell=True, capture_output=True, text=True)
            if "No rules match" in check_process.stdout:
                self.log(f"Firewall rule '{self.firewall_rule_name}' not found. Adding it...")
                add_command = 'netsh advfirewall firewall add rule name="iperf3" dir=in action=allow protocol=TCP localport=5201'
                subprocess.run(add_command, shell=True, check=True)
                self.log(f"Firewall rule '{self.firewall_rule_name}' added successfully.")
            else:
                self.log(f"Firewall rule '{self.firewall_rule_name}' already exists.")
        except subprocess.CalledProcessError as e:
            self.log(f"Error managing firewall rule: {e}")
            sys.exit(1)

    def run(self):
        self.add_firewall_rule()
        self.log(f"Starting iperf3 server on {self.server_ip}:{self.port}")
        while True:
            try:
                process = subprocess.Popen([self.iperf_path, "-s", "-p", str(self.port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                while True:
                    output, error = process.communicate()
                    if error:
                        self.log(f"Server error: {error}")
                    if "iperf Done." in output:
                        self.log("Test completed successfully. Creating new connection...")
                        break
                self.log("Restarting iperf3 server...")
            except KeyboardInterrupt:
                self.log("Server stopping due to KeyboardInterrupt...")
                process.terminate()
                break
            except Exception as e:
                self.log(f"Error running server: {e}")
                sys.exit(1)