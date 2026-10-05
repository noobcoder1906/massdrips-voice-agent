"""
push_changes.py

Push all local code changes to the E2E GPU node via SCP/SFTP.
Run this after powering on the node.

Usage:
  python push_changes.py --host <node-ip> --key <path-to-ssh-key>
  
Or set HOST and KEY_PATH in this file directly.
"""

import paramiko
import argparse
import os
import sys

# -- Set these --
DEFAULT_HOST = "164.52.212.94"
DEFAULT_KEY  = os.path.expanduser("~/.ssh/id_rsa")  # Update this to your key path

# Files changed in this session that need to be pushed
CHANGED_FILES = [
    # Local path                                         # Remote path in container
    ("backend/main.py",                                  "/app/backend/main.py"),
    ("backend/voice/tts.py",                             "/app/backend/voice/tts.py"),
    ("backend/voice/chatterbox_pipeline.py",             "/app/backend/voice/chatterbox_pipeline.py"),
    ("backend/agent/prompts.py",                         "/app/backend/agent/prompts.py"),
    (".env",                                             "/app/.env"),
    ("startup_check.py",                                 "/app/startup_check.py"),
    ("node_manager.py",                                  "/app/node_manager.py"),
]

def push(host, key_path):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {host}...")
    ssh.connect(host, username="root", key_filename=key_path, timeout=30)
    sftp = ssh.open_sftp()
    
    container_name = "massdrips-voice-agent-voxsales-1"
    
    for local_path, remote_path in CHANGED_FILES:
        full_local = os.path.join(os.path.dirname(__file__), local_path)
        if not os.path.exists(full_local):
            print(f"  [SKIP] {local_path} -- file not found locally")
            continue
        
        # Copy to host first, then into container
        tmp_path = f"/tmp/{os.path.basename(local_path)}"
        sftp.put(full_local, tmp_path)
        stdin, stdout, stderr = ssh.exec_command(
            f"docker cp {tmp_path} {container_name}:{remote_path}"
        )
        err = stderr.read().decode().strip()
        if err:
            print(f"  [FAIL] {local_path}: {err}")
        else:
            print(f"  [OK]   {local_path} -> {remote_path}")
    
    sftp.close()
    
    # Restart container to pick up changes
    print("\nRestarting container...")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /app && docker-compose restart voxsales 2>&1"
    )
    print(stdout.read().decode())
    
    # Run startup check
    print("\nRunning startup check...")
    stdin, stdout, stderr = ssh.exec_command(
        f"docker exec {container_name} python startup_check.py 2>&1"
    )
    for line in stdout:
        print(line, end="")
    
    ssh.close()
    print("\nDone!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--key",  default=DEFAULT_KEY)
    args = parser.parse_args()
    
    if not os.path.exists(args.key):
        print(f"SSH key not found: {args.key}")
        print("Get your key from E2E Networks dashboard -> SSH Keys")
        sys.exit(1)
    
    push(args.host, args.key)
