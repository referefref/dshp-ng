#!/usr/bin/env python3
import socket
import sys
import json
import os
import subprocess
import datetime
import time
import logging
from threading import Thread

current_run_unix_time = time.time() 

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def read_config(conf_var, conf_file, default_conf):
    try:
        conf_value = os.environ.get(conf_var.upper(), conf_file.get(conf_var, default_conf.get(conf_var)))
        if conf_var == "handlers":
            conf_value_list = conf_value.split(",")
            return conf_value_list
    except Exception as e:
        logging.critical(f"Missing config value for {conf_var}: {e}")
        sys.exit(2)
    return conf_value

def client_thread(conn, addr, reply):
    try:
        logging.info(f"Connection established with {addr}")
        # Receiving data from client (example: 1024 bytes)
        data = conn.recv(1024)
        logging.debug(f"Received data: {data.decode('utf-8')}")
        # Sending reply to connected client
        conn.sendall(reply.encode('utf-8'))
        logging.info(f"Reply sent to {addr}")
    except Exception as e:
        logging.error(f"Error during communication with {addr}: {e}")
    finally:
        # Closing connection
        conn.close()
        logging.info(f"Connection closed with {addr}")

def run_handlers(handlers, last_run_unix_time, timeout, handler_exec, hostname, offender_ip):
    now = datetime.datetime.now()
    current_run_unix_time = time.time()
    if current_run_unix_time > float(last_run_unix_time + timeout):
        logging.info("Running handlers due to timeout condition.")
        for handler in handlers:
            logging.debug(f"Calling handler {handler} for IP {offender_ip}")
            json_reply = json.dumps({
                "hostname": hostname,
                "ip": offender_ip,
                "time": now.isoformat()
            })
            try:
                subprocess.run([handler_exec, f"handlers/{handler}", json_reply], capture_output=True, check=True)
                logging.info(f"Handler {handler} executed. STDOUT: {result.stdout} STDERR: {result.stderr}")
            except Exception as e:
                logging.error(f"Error executing handler {handler} for IP {offender_ip}: {e}")
        return current_run_unix_time
    else:
        logging.debug("No need to run handlers yet. Waiting for next timeout.")
        return last_run_unix_time

# Load configuration
default_conf = {"port": 8888, "interface": "", "reply": "Hello, World!", "timeout": 300, "handler_exec": "/usr/bin/python3"}
try:
    conf_file = json.load(open("conf.json"))
    logging.info("Loaded conf.json file")
except Exception as e:
    logging.warning("Unable to load correctly phrased json config file: {}".format(e))

try:
    port = int(read_config('port', conf_file, default_conf))
    interface = str(read_config('interface', conf_file, default_conf))
    timeout = int(read_config('timeout', conf_file, default_conf))
    reply = str(read_config('reply', conf_file, default_conf))
    handlers = read_config('handlers', conf_file, default_conf)
    handler_exec = read_config('handler_exec', conf_file, default_conf)
    hostname = socket.gethostname()
    last_run_unix_time = 0
except Exception as e:
    logging.critical(f"Critical - problem setting config variable: {e}")
    sys.exit(2)

# Bind socket and start listening
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind((interface, port))
    s.listen(5)
    logging.info(f'Socket listening on {interface}:{port}')
except socket.error as msg:
    logging.critical(f'Bind failed. Error Code : {msg.errno} Message {msg.strerror}')
    sys.exit(2)

# Main loop to accept connections
while True:
    try:
        conn, addr = s.accept()
        logging.info(f"New connection from {addr}")
        logging.debug(f"Checking if handlers should be run. Current time: {current_run_unix_time}, Last run time: {last_run_unix_time}, Timeout: {timeout}")
        Thread(target=client_thread, args=(conn, addr, reply)).start()
    except Exception as e:
        logging.error(f"Error accepting connection: {e}")

s.close()
