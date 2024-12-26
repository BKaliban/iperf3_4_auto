# iPerf3 Network Testing (Server & Client)

## Description
This project provides a simple implementation of an **iPerf3** network testing framework using Python. It consists of two main components:

- **iPerf3 Server**: A server that listens for incoming client connections and runs performance tests.
- **iPerf3 Client**: A client that connects to the server, runs tests, and reports the results.

The server and client communicate using multicast or can be configured manually to connect to the server IP.

## Requirements
- **Python 3.x**: Ensure that Python 3 or later is installed.
- **iPerf3**: The script will automatically download and set up **iPerf3** (including the required `cygwin1.dll`).
- **Windows OS**: The scripts are designed for Windows and automatically set up necessary tools.