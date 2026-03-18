import time
import requests
import os
import datetime
import subprocess
import re

# Configuration
API_URL = "http://127.0.0.1:8000/ingest/log"

# Keep track of sent logs to avoid duplicates within a session
sent_logs = set()

# Simulated logs for fallback (with a small note)
SIMULATED_LOGS = [
    {"source": "system-auth", "level": "INFO", "message": "[SIMULATED] User sergiu logged in successfully from 192.168.1.100"},
    {"source": "firewall", "level": "INFO", "message": "[SIMULATED] Connection from 192.168.1.10 to 8.8.8.8 accepted"},
    {"source": "webserver", "level": "WARNING", "message": "[SIMULATED] High latency detected on API endpoint /api/v1/data"},
    {"source": "system-auth", "level": "ERROR", "message": "[SIMULATED] Failed login attempt from 10.0.0.5 for user admin"},
    {"source": "ids", "level": "CRITICAL", "message": "[SIMULATED] SQL Injection detected from 172.16.0.1 on /products?id=1'OR'1'='1"},
    {"source": "antivirus", "level": "INFO", "message": "[SIMULATED] Virus definition update successful"},
    {"source": "dns", "level": "WARNING", "message": "[SIMULATED] DNS resolution timeout for maliciousexample.com"},
    {"source": "system", "level": "INFO", "message": "[SIMULATED] System uptime: 5 days, 3 hours"},
    {"source": "database", "level": "ERROR", "message": "[SIMULATED] Database connection failed for user 'app_user'"},
    {"source": "network", "level": "CRITICAL", "message": "[SIMULATED] Unauthorized access attempt on SSH port from 203.0.113.45"},
]

def send_log(log_data):
    # Create a unique key for the log to prevent duplicates
    log_key = f"{log_data['timestamp']}-{log_data['source']}-{log_data['level']}-{log_data['message']}"
    if log_key in sent_logs:
        return # Skip if already sent

    try:
        response = requests.post(API_URL, json=log_data)
        response.raise_for_status()  # Raise an exception for HTTP errors
        print(f"Sent log: {log_data['message']}")
        sent_logs.add(log_key)
    except requests.exceptions.ConnectionError:
        print(f"Connection error: Backend not available at {API_URL}. Retrying...")
    except requests.exceptions.RequestException as e:
        print(f"Error sending log: {e}")

def get_current_timestamp():
    return datetime.datetime.utcnow().isoformat(timespec='seconds') + 'Z'

def parse_last_output(command_output, log_type):
    logs = []
    for line in command_output.splitlines():
        line = line.strip()
        if not line or line.startswith(("wtmp begins", "btmp begins", "reboot")): 
            continue

        # Example lines for last/lastb:
        # sergiu   pts/0        192.168.1.100    Tue Mar 19 10:00   still logged in
        # root     ssh:notty    192.168.1.100    Mon Jul 22 10:30 - 10:30 (00:00)

        user = "N/A"
        remote_ip = "N/A"
        message = line
        level = "INFO"
        timestamp_str = get_current_timestamp()

        # More robust parsing for last/lastb
        # Capture user, tty/host, remote_ip (optional), timestamp_part, and status/duration
        match = re.match(r'^(\S+)\s+\S+\s+(?:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|\S+)\s+)?(.*?)(?:\s+still logged in|\s+still running|\s+\(.*\))?$|(.+)', line)
        if match:
            user = match.group(1) or "N/A"
            remote_ip = match.group(2) if match.group(2) and re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', match.group(2)) else "N/A"
            timestamp_part = match.group(3).strip() if match.group(3) else ""
            
            # Attempt to parse a more accurate timestamp
            date_time_match = re.search(r'(\w{3}\s+\w{3}\s+\d{1,2}\s+\d{2}:\d{2})', timestamp_part)
            if date_time_match:
                try:
                    current_year = datetime.datetime.now().year
                    parsed_date_time_str = f"{date_time_match.group(1)} {current_year}"
                    dt_obj = datetime.datetime.strptime(parsed_date_time_str, "%a %b %d %H:%M %Y")
                    timestamp_str = dt_obj.isoformat(timespec='seconds') + 'Z'
                except ValueError:
                    pass
            
            if log_type == "lastb":
                level = "ERROR"
                message = f"Failed login attempt for user {user} from {remote_ip}. Details: {line}"
            elif log_type == "last":
                level = "INFO"
                if "still logged in" in line:
                    message = f"User {user} currently logged in from {remote_ip}. Details: {line}"
                else:
                    message = f"User {user} logged in from {remote_ip}. Details: {line}"

        logs.append({
            "timestamp": timestamp_str,
            "source": f"system-{log_type}",
            "level": level,
            "message": message,
            "ip": remote_ip 
        })
    return logs

def parse_lastlog_output(command_output):
    logs = []
    for line in command_output.splitlines():
        line = line.strip()
        if not line or line.startswith(("Username")): # Skip header
            continue

        # Example lastlog line:
        # sergiu       pts/0    192.168.1.100      Tue Mar 19 10:00:00 +0000 2026
        parts = line.split(maxsplit=4)
        if len(parts) < 4:
            continue

        user = parts[0]
        tty = parts[1]
        remote_ip = parts[2] if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', parts[2]) else "N/A"
        timestamp_str = get_current_timestamp() # Default

        # Attempt to parse a more accurate timestamp from lastlog
        # This regex is specifically for the lastlog output format
        lastlog_timestamp_match = re.search(r'(\w{3}\s+\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+[+\-]\d{4}\s+\d{4})', line)
        if lastlog_timestamp_match:
            try:
                # Example: Tue Mar 19 10:00:00 +0000 2026
                dt_obj = datetime.datetime.strptime(lastlog_timestamp_match.group(1), "%a %b %d %H:%M:%S %z %Y")
                timestamp_str = dt_obj.isoformat(timespec='seconds') + 'Z'
            except ValueError:
                pass
        
        message = f"User {user} last logged in from {remote_ip} on {tty}. Details: {line}"
        level = "INFO"
        if remote_ip == "N/A" and tty == "**Never logged in**":
            message = f"User {user} has never logged in."
            level = "INFO"
        elif remote_ip == "N/A" and tty != "**Never logged in**":
            message = f"User {user} last logged in locally on {tty}. Details: {line}"
        
        logs.append({
            "timestamp": timestamp_str,
            "source": "system-lastlog",
            "level": level,
            "message": message,
            "ip": remote_ip
        })
    return logs

def get_system_logs():
    new_logs = []
    commands_to_run = {
        "lastb": {"cmd": ["lastb", "-F", "-w", "-x"], "parser": parse_last_output, "type": "lastb"},
        "last": {"cmd": ["last", "-F", "-w", "-x"], "parser": parse_last_output, "type": "last"},
        "lastlog": {"cmd": ["lastlog", "-t", "7"], "parser": parse_lastlog_output, "type": "lastlog"}, # -t 7 for last 7 days
    }

    for name, config in commands_to_run.items():
        try:
            result = subprocess.run(config["cmd"], capture_output=True, text=True, check=True, encoding='utf-8')
            parsed = config["parser"](result.stdout, config["type"])
            for log in parsed:
                log_key = f"{log['timestamp']}-{log['source']}-{log['level']}-{log['message']}"
                if log_key not in sent_logs:
                    new_logs.append(log)
        except FileNotFoundError:
            print(f"Command '{config['cmd'][0]}' not found. Skipping {name} logs.")
        except subprocess.CalledProcessError as e:
            print(f"Error running '{config['cmd'][0]}': {e.stderr}")
        except Exception as e:
            print(f"An unexpected error occurred while processing {name} logs: {e}")
    
    # Sort new logs by timestamp before returning to ensure order
    new_logs.sort(key=lambda x: x['timestamp'])
    return new_logs

def run_log_agent():
    print("Starting SevinHub Log Agent...")
    simulated_log_index = 0
    while True:
        real_logs_this_cycle = []
        try:
            system_logs = get_system_logs()
            if system_logs:
                for log in system_logs:
                    send_log(log)
                    real_logs_this_cycle.append(log)
                print(f"Sent {len(real_logs_this_cycle)} real system logs.")
            else:
                print("No new real system logs found in this cycle. Checking again soon.")
        except Exception as e:
            print(f"Error fetching real system logs: {e}. Falling back to simulated logs for this cycle.")

        if not real_logs_this_cycle:
            # If no real logs were sent in this cycle, send a simulated one
            sim_log = SIMULATED_LOGS[simulated_log_index % len(SIMULATED_LOGS)]
            data = {
                "timestamp": get_current_timestamp(),
                "source": sim_log["source"],
                "level": sim_log["level"],
                "message": sim_log["message"]
            }
            send_log(data)
            simulated_log_index += 1
        
        time.sleep(5) # Poll for new logs every 5 seconds (can be adjusted)

if __name__ == "__main__":
    run_log_agent()
