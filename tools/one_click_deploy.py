#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键部署脚本
自动准备环境 + 构建部署，适合新服务器
"""

import os
import sys
import subprocess
import argparse
import getpass

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def print_banner():
    """显示横幅"""
    banner = f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║                海光DCU Exporter 一键部署                        ║
║              One-Click Deploy for New Servers                 ║
╚══════════════════════════════════════════════════════════════╝{Colors.NC}
"""
    print(banner)

def get_server_info(args):
    """获取服务器信息"""
    if args.host and args.username and args.password:
        return {
            'host': args.host,
            'username': args.username,
            'password': args.password,
            'port': args.port
        }
    
    print(f"{Colors.BLUE}📝 请输入服务器信息:{Colors.NC}")
    
    host = input("服务器地址: ").strip()
    if not host:
        print(f"{Colors.RED}❌ 服务器地址不能为空{Colors.NC}")
        return None
    
    username = input("用户名 [root]: ").strip() or "root"
    
    if args.password:
        password = args.password
    else:
        password = getpass.getpass("密码: ")
        if not password:
            print(f"{Colors.RED}❌ 密码不能为空{Colors.NC}")
            return None
    
    port = input("SSH端口 [22]: ").strip() or "22"
    try:
        port = int(port)
    except ValueError:
        print(f"{Colors.RED}❌ 端口必须是数字{Colors.NC}")
        return None
    
    return {
        'host': host,
        'username': username,
        'password': password,
        'port': port
    }

def run_script(script_name, server_info, description):
    """运行指定脚本"""
    print(f"\n{Colors.BLUE}🚀 {description}...{Colors.NC}")
    
    if not os.path.exists(script_name):
        print(f"{Colors.RED}❌ 脚本不存在: {script_name}{Colors.NC}")
        return False
    
    cmd = [
        'python', script_name,
        '--host', server_info['host'],
        '--username', server_info['username'],
        '--password', server_info['password'],
        '--port', str(server_info['port'])
    ]
    
    try:
        print(f"执行: python {script_name} --host {server_info['host']} --username {server_info['username']} --port {server_info['port']}")
        result = subprocess.run(cmd, timeout=600)  # 10分钟超时
        
        if result.returncode == 0:
            print(f"{Colors.GREEN}✅ {description}成功{Colors.NC}")
            return True
        else:
            print(f"{Colors.RED}❌ {description}失败{Colors.NC}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"{Colors.RED}❌ {description}超时{Colors.NC}")
        return False
    except KeyboardInterrupt:
        print(f"{Colors.YELLOW}⚠️ {description}被用户中断{Colors.NC}")
        return False
    except Exception as e:
        print(f"{Colors.RED}❌ {description}出错: {e}{Colors.NC}")
        return False

def show_post_deployment_info(server_info):
    """显示部署后信息"""
    print(f"\n{Colors.CYAN}🎉 部署完成！{Colors.NC}")
    print(f"\n{Colors.PURPLE}📋 后续操作指南:{Colors.NC}")
    print(f"1. SSH登录服务器:")
    print(f"   ssh {server_info['username']}@{server_info['host']}")
    print(f"")
    print(f"2. 查看构建结果:")
    print(f"   ls -la /opt/hygon-dcgm-exporter-build/hygon-dcgm-exporter-*")
    print(f"")
    print(f"3. 安装程序:")
    print(f"   cd /opt/hygon-dcgm-exporter-build/hygon-dcgm-exporter-*")
    print(f"   sudo ./install.sh")
    print(f"")
    print(f"4. 启动服务:")
    print(f"   cd /opt/hygon-dcgm-exporter")
    print(f"   ./start.sh")
    print(f"")
    print(f"5. 访问指标:")
    print(f"   http://{server_info['host']}:9400/metrics")
    print(f"   http://{server_info['host']}:9400/health")
    print(f"")
    print(f"6. 测试部署:")
    print(f"   python tools/test_deploy.py --host {server_info['host']} --username {server_info['username']} --password ****")
    print(f"\n{Colors.YELLOW}💡 提示: 确保服务器已安装海光DCU驱动和hy-smi工具{Colors.NC}")

def main():
    parser = argparse.ArgumentParser(description='海光DCU Exporter 一键部署')
    parser.add_argument('--host', help='服务器地址')
    parser.add_argument('--username', default='root', help='用户名')
    parser.add_argument('--password', help='密码')
    parser.add_argument('--port', type=int, default=22, help='SSH端口')
    parser.add_argument('--skip-env-prepare', action='store_true', help='跳过环境准备步骤')
    parser.add_argument('--env-only', action='store_true', help='只执行环境准备')
    
    args = parser.parse_args()
    
    print_banner()
    
    # 获取服务器信息
    server_info = get_server_info(args)
    if not server_info:
        sys.exit(1)
    
    print(f"\n{Colors.YELLOW}🎯 部署计划:{Colors.NC}")
    if not args.skip_env_prepare:
        print("  1. 准备构建环境（安装Go、配置代理、修复兼容性）")
    if not args.env_only:
        print("  2. 构建部署程序")
    
    if not args.skip_env_prepare and not args.env_only:
        confirm = input(f"\n是否继续? (Y/n): ").lower()
        if confirm == 'n':
            sys.exit(0)
    
    success_steps = []
    
    # 步骤1: 环境准备
    if not args.skip_env_prepare:
        if run_script('tools/prepare_build_environment.py', server_info, '环境准备'):
            success_steps.append('环境准备')
        else:
            print(f"{Colors.RED}❌ 环境准备失败，无法继续{Colors.NC}")
            sys.exit(1)
    
    # 如果只是环境准备，到此结束
    if args.env_only:
        print(f"\n{Colors.GREEN}🎉 环境准备完成！{Colors.NC}")
        print(f"{Colors.BLUE}下一步可以运行: python tools/remote_deploy.py --host {server_info['host']} --username {server_info['username']} --password ****{Colors.NC}")
        sys.exit(0)
    
    # 步骤2: 构建部署
    if run_script('tools/remote_deploy.py', server_info, '构建部署'):
        success_steps.append('构建部署')
    else:
        print(f"{Colors.RED}❌ 构建部署失败{Colors.NC}")
        sys.exit(1)
    
    # 显示结果
    print(f"\n{Colors.GREEN}🎉 所有步骤完成！{Colors.NC}")
    print(f"成功步骤: {', '.join(success_steps)}")
    
    show_post_deployment_info(server_info)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
