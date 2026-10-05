"""
node_manager.py

Comprehensive GPU node management script.
Run from local machine to manage the E2E GPU node.

Commands:
  python node_manager.py logs          -- Stream live logs
  python node_manager.py startup       -- Run pre-flight startup check
  python node_manager.py restart       -- Restart the voice agent server
  python node_manager.py status        -- Check server status
  python node_manager.py ssh           -- Open interactive SSH session
  python node_manager.py push          -- Sync local code changes to server
"""

import paramiko
import sys
import os

HOST = "164.52.212.94"
USER = "root"
PASSWORD = "SWGRXF@txsvh575"
APP_DIR = "/app"

def ssh_connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD)
    return ssh

def run_command(ssh, command, stream=False):
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
    if stream:
        for line in stdout:
            print(line, end="")
    else:
        out = stdout.read().decode()
        err = stderr.read().decode()
        if out: print(out)
        if err: print(err)

def cmd_logs():
    """Stream live docker logs."""
    ssh = ssh_connect()
    print(f"Streaming logs from {HOST}...")
    run_command(ssh, "docker logs -f --tail 100 massdrips-voice-agent-voxsales-1 2>&1", stream=True)
    ssh.close()

def cmd_startup():
    """Run pre-flight startup check inside container."""
    ssh = ssh_connect()
    print("Running startup check on GPU node...")
    run_command(ssh, "docker exec massdrips-voice-agent-voxsales-1 python startup_check.py 2>&1", stream=True)
    ssh.close()

def cmd_restart():
    """Restart the voice agent container."""
    ssh = ssh_connect()
    print("Restarting voice agent...")
    run_command(ssh, "cd /app && docker-compose restart voxsales", stream=True)
    ssh.close()

def cmd_status():
    """Check container status."""
    ssh = ssh_connect()
    run_command(ssh, "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'", stream=True)
    ssh.close()

def cmd_exec(command):
    """Run a command inside the container."""
    ssh = ssh_connect()
    run_command(ssh, f"docker exec massdrips-voice-agent-voxsales-1 {command} 2>&1", stream=True)
    ssh.close()

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "logs"
    
    if cmd == "logs":
        cmd_logs()
    elif cmd == "startup":
        cmd_startup()
    elif cmd == "restart":
        cmd_restart()
    elif cmd == "status":
        cmd_status()
    elif cmd == "exec" and len(sys.argv) > 2:
        cmd_exec(" ".join(sys.argv[2:]))
    else:
        print(__doc__)
