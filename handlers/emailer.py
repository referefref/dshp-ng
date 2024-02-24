#!/usr/bin/env python3
import sys
import json
import os
import smtplib
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

try:
    json_args = json.loads(sys.argv[1])
    hostname = json_args["hostname"]
    ip = json_args["ip"]
    time = json_args["time"]

    mail_from = os.getenv("MAIL_FROM")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))  # Ensure port is an integer
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    mail_to = os.getenv("MAIL_TO").split(",")
    smtp_tls = os.getenv("SMTP_TLS", "False")  # Default TLS to False if not specified

    smtpObj = smtplib.SMTP(host=smtp_server, port=smtp_port)
    if smtp_tls == "True":
        smtpObj.starttls()
    smtpObj.login(smtp_user, smtp_pass)

    for mail_address in mail_to:
        message = f"""From: {mail_from}
To: {mail_address}
Subject: DSHP alert: {hostname} access attempt detected

There has been an attempt to access {hostname} at {time} from IP address {ip}."""
        smtpObj.sendmail(mail_from, mail_address, message)
    smtpObj.quit()
    logging.info("Mail sent successfully to all recipients.")
except Exception as e:
    logging.critical(f"Unable to send mail - something went wrong: {e}")
    sys.exit(2)
