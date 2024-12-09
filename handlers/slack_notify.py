#!/usr/bin/env python3

import sys
import json
import requests
from typing import Dict, Any

def notify_slack(event_data: Dict[str, Any]) -> None:
    """Send notification to Slack"""
    webhook_url = "YOUR_WEBHOOK_URL"
    message = f"Honeypot alert!\nHost: {event_data['hostname']}\nAttacker IP: {event_data['ip']}\nTime: {event_data['time']}"
    
    requests.post(webhook_url, json={"text": message})

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: slack_notify.py '<json_data>'")
        sys.exit(1)

    try:
        event_data = json.loads(sys.argv[1])
        notify_slack(event_data)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
