import os
import tempfile
import requests
import subprocess
import zipfile
import shutil
import sys
from datetime import datetime
import configparser
#from logger import setup_logger

class IperfClient:
    def __init__(self):
        self.config = self.load_config()
        self.logger = setup_logger(self.config['settings']['log_file'])
        
        self.port = int(self.config['settings']['port'])
        self.iperf_path = self.setup_iperf()

    def load_config(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        return config

    def log(self, message):
        self.logger.info(message)

    def setup_iperf(self):
        iperf_path = self.config['settings']['iperf_path']
        cygwin_dll_path = self.config['settings']['cygwin_dll_path']
        
        if not os.path.exists(iperf_path):
            try:
                self.log("Downloading iperf3...")
                url = self.config['settings']['iperf_url']
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                zip_path = os.path.join(tempfile.gettempdir(), "iperf3.14_64.zip")

                with open(zip_path, "wb") as f:
                    f.write(response.content)
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(os.path.dirname(iperf_path))
                
                os.remove(zip_path)
                self.log(f"iperf3 and cygwin1.dll downloaded to {iperf_path}")
                
                if not os.path.exists(iperf_path) or not os.path.exists(cygwin_dll_path):
                    raise FileNotFoundError(f"Files not found in {iperf_path} or {cygwin_dll_path}")
                
            except Exception as e:
                self.log(f"Error downloading iperf3: {str(e)}")
                sys.exit(1)
        
        return iperf_path

    def run_test(self, server_ip, reverse=False):
        self.log(f"Starting iperf3 client test to {server_ip}:{self.port} with {'reverse' if reverse else 'regular'} mode")
        try:
            cmd = [
                self.iperf_path, "-c", server_ip, "-p", str(self.port),
                "--format", "m", "-t", "60"
            ]
            if reverse:
                cmd.append("--reverse")
            
            self.log(f"Running command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            output, error = process.communicate()

            if process.returncode != 0:
                self.log(f"Test failed with exit code {process.returncode}. Error: {error.strip()}")
                return False
            
            self.log(f"Test completed successfully (Reverse: {reverse})")
            return True
        except Exception as e:
            self.log(f"Error running test: {str(e)}")
            return False