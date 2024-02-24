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

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# function that sets config variables with the following priority chain
# envvar > config file > default value
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


# function to handle connections
def client_thread(conn, reply):
    # Sending message to connected client
    conn.sendall(reply.encode('utf-8'))
    # came out of loop
    conn.close()


# function to run handlers
def run_handlers(handlers, last_run_unix_time, timeout, handler_exec, hostname, offender_ip):
    now = datetime.datetime.now()
    current_run_unix_time = time.time()
    if current_run_unix_time > (last_run_unix_time + timeout):
        for handler in handlers:
            json_reply = json.dumps({
                "hostname": hostname,
                "ip": offender_ip,
                "time": now.isoformat()
            })
            subprocess.call([f"{handler_exec} {handler} '{json_reply}'"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd="handlers")
        return current_run_unix_time
    else:
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
logging.info('Socket created')
try:
    s.bind((interface, port))
except socket.error as msg:
    logging.critical('Bind failed. Error Code : {} Message {}'.format(msg.errno, msg.strerror))
    sys.exit(2)

logging.info('Socket bind complete')
s.listen(5)
logging.info('Socket now listening')

# Keep waiting for connections
while True:
    conn, addr = s.accept()
    offender_ip = addr[0]
    logging.debug("Attempted connection from " + offender_ip)
    last_run_unix_time = run_handlers(handlers, last_run_unix_time, timeout, handler_exec, hostname, offender_ip)
    Thread(target=client_thread, args=(conn, reply)).start()

s.close()
