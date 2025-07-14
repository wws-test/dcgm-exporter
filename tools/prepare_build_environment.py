#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建环境准备脚本
自动检测并修复Go环境、网络代理等问题
确保在任何服务器上都能成功构建
"""

import paramiko
import sys
import argparse

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def prepare_environment(host, username, password, port=22):
    """准备构建环境"""
    
    try:
        # 连接SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=username, password=password)
        print(f"{Colors.GREEN}✅ SSH连接成功{Colors.NC}")
        
        # 环境准备脚本
        prepare_script = '''#!/bin/bash
set -e

echo "🔧 开始准备构建环境..."

# 1. 检查并安装基础工具
echo "检查基础工具..."
apt update
apt install -y wget curl git build-essential

# 2. 检查并安装/升级Go环境
echo "检查Go环境..."
if ! command -v go &> /dev/null; then
    echo "未找到Go，开始安装..."
    INSTALL_GO=true
else
    GO_VERSION=$(go version | grep -oP 'go\\K[0-9]+\\.[0-9]+')
    echo "当前Go版本: $GO_VERSION"
    
    # 检查Go版本是否足够新（需要1.21+）
    if [[ $(echo "$GO_VERSION 1.21" | tr " " "\\n" | sort -V | head -n1) != "1.21" ]]; then
        echo "Go版本过旧（需要1.21+），开始升级..."
        INSTALL_GO=true
    else
        echo "✅ Go版本满足要求"
        INSTALL_GO=false
    fi
fi

# 安装/升级Go
if [ "$INSTALL_GO" = true ]; then
    echo "下载并安装Go 1.21.13..."
    cd /tmp
    wget -q https://go.dev/dl/go1.21.13.linux-amd64.tar.gz
    if [ $? -ne 0 ]; then
        echo "❌ Go下载失败，尝试使用系统包管理器..."
        apt install -y golang-go
    else
        rm -rf /usr/local/go
        tar -C /usr/local -xzf go1.21.13.linux-amd64.tar.gz
        echo "✅ Go 1.21.13 安装完成"
    fi
fi

# 3. 配置Go环境
echo "配置Go环境..."
export PATH=/usr/local/go/bin:$PATH

# 永久添加到PATH
if ! grep -q "/usr/local/go/bin" /etc/profile; then
    echo 'export PATH=/usr/local/go/bin:$PATH' >> /etc/profile
fi

# 配置Go代理（解决网络问题）
echo "配置Go代理..."
go env -w GOPROXY="https://goproxy.cn,direct"
go env -w GOSUMDB="sum.golang.google.cn"
go env -w GO111MODULE=on

# 测试Go代理连接
echo "测试Go代理连接..."
if curl -I --connect-timeout 10 https://goproxy.cn > /dev/null 2>&1; then
    echo "✅ goproxy.cn 可访问"
else
    echo "⚠️ goproxy.cn 不可访问，使用备用代理"
    go env -w GOPROXY="https://goproxy.io,https://proxy.golang.org,direct"
fi

# 4. 测试Go环境
echo "测试Go环境..."
go version
echo "Go代理: $(go env GOPROXY)"
echo "Go模块: $(go env GO111MODULE)"

# 5. 测试依赖下载
echo "测试依赖下载..."
cd /tmp
timeout 30 go mod download github.com/sirupsen/logrus@v1.9.3
if [ $? -eq 0 ]; then
    echo "✅ 依赖下载测试成功"
else
    echo "⚠️ 依赖下载测试失败，但环境已配置"
fi

# 6. 检查海光DCU环境
echo "检查海光DCU环境..."
if [ -f "/usr/local/hyhal/bin/hy-smi" ]; then
    echo "✅ 找到hy-smi: /usr/local/hyhal/bin/hy-smi"
    /usr/local/hyhal/bin/hy-smi --version 2>/dev/null || echo "hy-smi版本信息获取失败"
else
    echo "⚠️ 未找到hy-smi，请确保已安装海光DCU驱动"
fi

echo "🎉 构建环境准备完成！"
echo ""
echo "环境信息:"
echo "- Go版本: $(go version)"
echo "- Go代理: $(go env GOPROXY)"
echo "- hy-smi: $([ -f "/usr/local/hyhal/bin/hy-smi" ] && echo "已安装" || echo "未安装")"
'''
        
        # 执行环境准备脚本
        print(f"{Colors.BLUE}🔧 执行环境准备脚本...{Colors.NC}")
        stdin, stdout, stderr = ssh.exec_command(prepare_script)
        
        # 实时显示输出
        while True:
            line = stdout.readline()
            if not line:
                break
            print(line.strip())
        
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print(f"{Colors.GREEN}🎉 环境准备成功！{Colors.NC}")
        else:
            error = stderr.read().decode('utf-8')
            print(f"{Colors.RED}❌ 环境准备失败: {error}{Colors.NC}")
            return False
        
        # 验证环境
        print(f"{Colors.BLUE}🧪 验证环境配置...{Colors.NC}")
        
        verification_commands = [
            ("Go版本", "go version"),
            ("Go代理", "go env GOPROXY"),
            ("Go模块", "go env GO111MODULE"),
            ("网络连接", "curl -I --connect-timeout 5 https://goproxy.cn"),
            ("hy-smi", "ls -la /usr/local/hyhal/bin/hy-smi"),
        ]
        
        all_good = True
        for desc, cmd in verification_commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                output = stdout.read().decode('utf-8').strip()
                print(f"{Colors.GREEN}✅ {desc}: {output.split()[0] if output else '正常'}{Colors.NC}")
            else:
                print(f"{Colors.YELLOW}⚠️ {desc}: 检查失败{Colors.NC}")
                if desc != "hy-smi":  # hy-smi不是必需的
                    all_good = False
        
        ssh.close()
        
        if all_good:
            print(f"\n{Colors.GREEN}🎉 环境验证通过！现在可以运行构建部署了{Colors.NC}")
            print(f"{Colors.BLUE}下一步: python tools/remote_deploy.py --host {host} --username {username} --password ****{Colors.NC}")
        else:
            print(f"\n{Colors.YELLOW}⚠️ 部分检查失败，但基本环境已准备好{Colors.NC}")
        
        return all_good
        
    except Exception as e:
        print(f"{Colors.RED}❌ 环境准备失败: {e}{Colors.NC}")
        return False

def main():
    parser = argparse.ArgumentParser(description='准备构建环境')
    parser.add_argument('--host', required=True, help='服务器地址')
    parser.add_argument('--username', required=True, help='用户名')
    parser.add_argument('--password', required=True, help='密码')
    parser.add_argument('--port', type=int, default=22, help='SSH端口')
    
    args = parser.parse_args()
    
    print(f"{Colors.CYAN}🚀 海光DCU Exporter 构建环境准备{Colors.NC}")
    print(f"目标服务器: {args.host}")
    print(f"用户: {args.username}")
    print()
    
    success = prepare_environment(args.host, args.username, args.password, args.port)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
