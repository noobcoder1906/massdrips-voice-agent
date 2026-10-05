import paramiko

def get_logs():
    host = "164.52.212.94"
    password = "SWGRXF@txsvh575"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username="root", password=password)
        stdin, stdout, stderr = ssh.exec_command("docker logs --tail 80 massdrips-voice-agent-voxsales-1 2>&1")
        print(stdout.read().decode())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    get_logs()
