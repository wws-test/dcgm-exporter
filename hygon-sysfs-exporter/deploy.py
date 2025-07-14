#!/usr/bin/env python3
"""
海光DCU Exporter 部署脚本
支持本地编译和远程部署
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """执行命令"""
    print(f"执行命令: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"命令执行失败: {result.stderr}")
        sys.exit(1)
    return result

def build_exporter():
    """编译exporter"""
    print("开始编译海光DCU Exporter...")
    
    # 设置Go环境变量
    env = os.environ.copy()
    env['GOOS'] = 'linux'
    env['GOARCH'] = 'amd64'
    env['CGO_ENABLED'] = '0'
    
    # 编译
    cmd = "go build -ldflags '-s -w' -o hygon-dcu-exporter ."
    result = subprocess.run(cmd, shell=True, env=env, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"编译失败: {result.stderr}")
        return False
    
    print("编译成功!")
    return True

def deploy_local():
    """本地部署"""
    print("开始本地部署...")
    
    # 复制二进制文件
    if not os.path.exists("hygon-dcu-exporter"):
        print("二进制文件不存在，请先编译")
        return False
    
    run_command("sudo cp hygon-dcu-exporter /usr/local/bin/")
    run_command("sudo chmod +x /usr/local/bin/hygon-dcu-exporter")
    
    # 安装systemd服务
    run_command("sudo cp hygon-dcu-exporter.service /etc/systemd/system/")
    run_command("sudo systemctl daemon-reload")
    run_command("sudo systemctl enable hygon-dcu-exporter")
    
    print("本地部署完成!")
    print("启动服务: sudo systemctl start hygon-dcu-exporter")
    print("查看状态: sudo systemctl status hygon-dcu-exporter")
    print("查看日志: sudo journalctl -u hygon-dcu-exporter -f")
    
    return True

def deploy_remote(host, user="root"):
    """远程部署"""
    print(f"开始远程部署到 {user}@{host}...")
    
    if not os.path.exists("hygon-dcu-exporter"):
        print("二进制文件不存在，请先编译")
        return False
    
    # 上传文件
    run_command(f"scp hygon-dcu-exporter {user}@{host}:/tmp/")
    run_command(f"scp hygon-dcu-exporter.service {user}@{host}:/tmp/")
    
    # 远程安装
    remote_commands = [
        "sudo mv /tmp/hygon-dcu-exporter /usr/local/bin/",
        "sudo chmod +x /usr/local/bin/hygon-dcu-exporter",
        "sudo mv /tmp/hygon-dcu-exporter.service /etc/systemd/system/",
        "sudo systemctl daemon-reload",
        "sudo systemctl enable hygon-dcu-exporter",
        "sudo systemctl restart hygon-dcu-exporter"
    ]
    
    for cmd in remote_commands:
        run_command(f"ssh {user}@{host} '{cmd}'")
    
    print(f"远程部署到 {host} 完成!")
    print(f"查看状态: ssh {user}@{host} 'sudo systemctl status hygon-dcu-exporter'")
    print(f"查看指标: curl http://{host}:9400/metrics")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="海光DCU Exporter 部署工具")
    parser.add_argument("--build", action="store_true", help="编译exporter")
    parser.add_argument("--deploy-local", action="store_true", help="本地部署")
    parser.add_argument("--deploy-remote", help="远程部署到指定主机")
    parser.add_argument("--user", default="root", help="远程部署用户名")
    
    args = parser.parse_args()
    
    if args.build:
        if not build_exporter():
            sys.exit(1)
    
    if args.deploy_local:
        if not deploy_local():
            sys.exit(1)
    
    if args.deploy_remote:
        if not deploy_remote(args.deploy_remote, args.user):
            sys.exit(1)
    
    if not any([args.build, args.deploy_local, args.deploy_remote]):
        parser.print_help()

if __name__ == "__main__":
    main()
