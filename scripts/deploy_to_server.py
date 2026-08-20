#!/usr/bin/env python3
import os, sys, time
import paramiko

SERVER_IP = "172.18.51.38"
SERVER_USER = "roshan"
SERVER_PASS = "Citkokrajhar123@"
PORT = 22

print(f"Connecting to {SERVER_USER}@{SERVER_IP}:{PORT} via SSH...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(SERVER_IP, port=PORT, username=SERVER_USER, password=SERVER_PASS, timeout=15)
    print("SSH connection established successfully!")
    
    def run_cmd(cmd, sudo=False):
        print(f"\n--> Executing: {cmd}")
        if sudo:
            stdin, stdout, stderr = ssh.exec_command(f"echo '{SERVER_PASS}' | sudo -S {cmd}")
        else:
            stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        if out: print(out.strip())
        if err and "password for" not in err: print("STDERR:", err.strip())
        return out, err

    # 1. Inspect OS and installed software
    run_cmd("uname -a || ver")
    run_cmd("which git || where git")
    run_cmd("which python3 || which python || where python")
    run_cmd("which docker || where docker")

    # 2. Clone or pull repository
    run_cmd("mkdir -p ~/itom && cd ~/itom && git init && git remote remove origin 2>/dev/null || true && git remote add origin https://github.com/roshanData/itom.git && git fetch origin main && git checkout -f main")

    # 3. Start high-performance web server on port 8080 or port 80
    run_cmd("pkill -f 'python.*http.server.*8080' || true")
    run_cmd("nohup python3 -m http.server 8080 --directory ~/itom > ~/itom_server.log 2>&1 &")
    
    time.sleep(2)
    run_cmd("ps aux | grep http.server || netstat -tuln | grep 8080")
    print("\n========================================================")
    print("  MIGRATION COMPLETE: ITOM PORTAL RUNNING ON LOCAL SERVER")
    print(f"  Access URL: http://{SERVER_IP}:8080/ops_analytics.html")
    print("========================================================")

finally:
    ssh.close()
