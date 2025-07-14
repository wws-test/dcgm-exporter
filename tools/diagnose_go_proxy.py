#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Go代理问题诊断脚本
快速找出为什么无法下载Go依赖
"""

import paramiko
import sys
import argparse

def diagnose_go_proxy(host, username, password, port=22):
    """诊断Go代理问题"""
    
    try:
        # 连接SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=username, password=password)
        print(f"✅ SSH连接成功")
        
        # 诊断命令列表
        commands = [
            ("基本网络连接", "ping -c 3 8.8.8.8"),
            ("DNS解析测试", "nslookup proxy.golang.org"),
            ("Go代理连接测试", "curl -I --connect-timeout 10 https://proxy.golang.org"),
            ("国内Go代理测试", "curl -I --connect-timeout 10 https://goproxy.cn"),
            ("Go版本", "go version"),
            ("当前Go环境", "go env GOPROXY GOSUMDB GO111MODULE"),
            ("测试简单下载", "timeout 30 go mod download github.com/sirupsen/logrus@v1.9.3"),
        ]
        
        print("\n" + "="*60)
        print("Go代理问题诊断报告")
        print("="*60)
        
        for desc, cmd in commands:
            print(f"\n🔍 {desc}:")
            print(f"命令: {cmd}")
            
            stdin, stdout, stderr = ssh.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            output = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8').strip()
            
            if exit_status == 0:
                print(f"✅ 成功")
                if output:
                    print(f"输出: {output}")
            else:
                print(f"❌ 失败 (退出码: {exit_status})")
                if error:
                    print(f"错误: {error}")
                if output:
                    print(f"输出: {output}")
        
        # 尝试修复Go代理设置
        print(f"\n🔧 尝试修复Go代理设置...")
        
        fix_commands = [
            'export GOPROXY="https://goproxy.cn,direct"',
            'export GOSUMDB="sum.golang.google.cn"', 
            'export GO111MODULE=on',
            'go env -w GOPROXY="https://goproxy.cn,direct"',
            'go env -w GOSUMDB="sum.golang.google.cn"',
            'go clean -modcache',
        ]
        
        for cmd in fix_commands:
            print(f"执行: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error = stderr.read().decode('utf-8').strip()
                print(f"  ⚠️ 警告: {error}")
        
        # 再次测试
        print(f"\n🧪 修复后测试...")
        test_cmd = 'export GOPROXY="https://goproxy.cn,direct" && timeout 30 go mod download github.com/sirupsen/logrus@v1.9.3'
        stdin, stdout, stderr = ssh.exec_command(test_cmd)
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print(f"✅ 修复成功！现在可以下载Go依赖了")
        else:
            error = stderr.read().decode('utf-8').strip()
            print(f"❌ 仍然失败: {error}")
            
            # 提供具体建议
            print(f"\n💡 建议:")
            if "timeout" in error.lower():
                print("- 网络超时，尝试使用更稳定的代理")
            elif "certificate" in error.lower():
                print("- SSL证书问题，可能需要更新系统证书")
            elif "connection refused" in error.lower():
                print("- 连接被拒绝，可能是防火墙问题")
            else:
                print("- 检查系统时间是否正确")
                print("- 检查是否有企业防火墙阻止")
                print("- 尝试使用HTTP代理而不是HTTPS")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description='诊断Go代理问题')
    parser.add_argument('--host', required=True, help='服务器地址')
    parser.add_argument('--username', required=True, help='用户名')
    parser.add_argument('--password', required=True, help='密码')
    parser.add_argument('--port', type=int, default=22, help='SSH端口')
    
    args = parser.parse_args()
    
    success = diagnose_go_proxy(args.host, args.username, args.password, args.port)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
