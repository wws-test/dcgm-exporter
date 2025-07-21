#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海光DCU监控系统一键部署脚本
自动部署Prometheus + Grafana + DCGM-Exporter完整监控方案
"""

import os
import sys
import subprocess
import argparse
import json
import time
from pathlib import Path

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

class OneClickDeployer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.deploy_dir = Path(__file__).parent.parent
        
    def print_colored(self, message, color=Colors.WHITE):
        print(f"{color}{message}{Colors.NC}")
        
    def print_step(self, step, message):
        self.print_colored(f"[步骤 {step}] {message}", Colors.BLUE)
        
    def print_success(self, message):
        self.print_colored(f"✅ {message}", Colors.GREEN)
        
    def print_error(self, message):
        self.print_colored(f"❌ {message}", Colors.RED)
        
    def print_warning(self, message):
        self.print_colored(f"⚠️  {message}", Colors.YELLOW)

    def run_command(self, command, cwd=None, check=True):
        """执行命令并返回结果"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=cwd or self.project_root,
                capture_output=True, 
                text=True, 
                check=check
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr

    def check_prerequisites(self):
        """检查部署前置条件"""
        self.print_step(1, "检查部署环境")
        
        # 检查Python
        success, stdout, stderr = self.run_command("python --version")
        if success:
            self.print_success(f"Python环境: {stdout.strip()}")
        else:
            self.print_error("Python未安装或不在PATH中")
            return False
            
        # 检查Go环境
        success, stdout, stderr = self.run_command("go version")
        if success:
            self.print_success(f"Go环境: {stdout.strip()}")
        else:
            self.print_warning("Go未安装，将跳过本地构建")
            
        # 检查网络连接
        test_urls = [
            "http://192.7.111.66:9090",  # Prometheus
            "http://192.7.111.66:3000",  # Grafana
        ]
        
        for url in test_urls:
            success, _, _ = self.run_command(f"curl -s -f {url}/api/v1/status/config", check=False)
            if success:
                self.print_success(f"服务可访问: {url}")
            else:
                self.print_warning(f"服务不可访问: {url}")
        
        return True

    def build_exporter(self):
        """构建DCGM-Exporter"""
        self.print_step(2, "构建DCGM-Exporter")
        
        build_script = self.project_root / "build" / "build-hygon.sh"
        if not build_script.exists():
            # 如果没有构建脚本，尝试直接构建
            self.print_warning("构建脚本不存在，尝试直接构建")
            success, stdout, stderr = self.run_command("go build -o dcgm-exporter ./cmd/dcgm-exporter")
            if success:
                self.print_success("DCGM-Exporter构建成功")
                return True
            else:
                self.print_error(f"构建失败: {stderr}")
                return False
        
        # 使用构建脚本
        success, stdout, stderr = self.run_command(f"bash {build_script}")
        if success:
            self.print_success("DCGM-Exporter构建成功")
            return True
        else:
            self.print_error(f"构建失败: {stderr}")
            return False

    def deploy_prometheus(self):
        """部署Prometheus"""
        self.print_step(3, "配置Prometheus")
        
        prometheus_config = self.deploy_dir / "monitoring" / "prometheus" / "prometheus.yml"
        if not prometheus_config.exists():
            # 创建默认配置
            config_content = """
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'hygon-dcu-exporter'
    static_configs:
      - targets: 
          - '192.7.111.66:9400'
          - '192.7.111.67:9400'
          - '192.7.111.68:9400'
    scrape_interval: 30s
    scrape_timeout: 10s
    metrics_path: /metrics
    
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
"""
            prometheus_config.parent.mkdir(parents=True, exist_ok=True)
            with open(prometheus_config, 'w') as f:
                f.write(config_content)
            self.print_success("Prometheus配置文件已创建")
        else:
            self.print_success("Prometheus配置文件已存在")
        
        return True

    def deploy_grafana(self):
        """部署Grafana仪表板"""
        self.print_step(4, "配置Grafana监控仪表板")
        
        # 检查仪表板文件
        dashboard_file = self.project_root / "hygon-dcu-dashboard-simple.json"
        if not dashboard_file.exists():
            self.print_error("Grafana仪表板文件不存在")
            return False
        
        # 复制仪表板到监控目录
        target_dashboard = self.deploy_dir / "monitoring" / "grafana" / "dashboards" / "hygon-dcu-dashboard.json"
        target_dashboard.parent.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy2(dashboard_file, target_dashboard)
        self.print_success("Grafana仪表板已准备就绪")
        
        return True

    def deploy_exporters(self, servers):
        """部署DCGM-Exporter到服务器"""
        self.print_step(5, f"部署DCGM-Exporter到服务器: {', '.join(servers)}")
        
        # 调用远程部署脚本
        remote_deploy_script = self.deploy_dir / "scripts" / "remote_deploy.py"
        if remote_deploy_script.exists():
            servers_str = ",".join(servers)
            success, stdout, stderr = self.run_command(
                f"python {remote_deploy_script} --servers {servers_str}"
            )
            if success:
                self.print_success("DCGM-Exporter部署成功")
                return True
            else:
                self.print_error(f"部署失败: {stderr}")
                return False
        else:
            self.print_warning("远程部署脚本不存在，跳过自动部署")
            self.print_colored("请手动部署DCGM-Exporter到目标服务器", Colors.YELLOW)
            return True

    def setup_monitoring(self):
        """设置监控系统"""
        self.print_step(6, "设置Grafana监控")
        
        # 调用Grafana设置脚本
        grafana_setup_script = self.deploy_dir / "scripts" / "setup_grafana_monitoring.py"
        if grafana_setup_script.exists():
            success, stdout, stderr = self.run_command(
                f"python {grafana_setup_script} --grafana-url http://192.7.111.66:3000"
            )
            if success:
                self.print_success("Grafana监控设置完成")
                return True
            else:
                self.print_warning(f"Grafana设置可能有问题: {stderr}")
                return True  # 不阻断流程
        else:
            self.print_warning("Grafana设置脚本不存在")
            return True

    def verify_deployment(self):
        """验证部署结果"""
        self.print_step(7, "验证部署结果")
        
        # 检查exporter指标
        test_urls = [
            "http://192.7.111.66:9400/metrics",
            "http://192.7.111.67:9400/metrics", 
            "http://192.7.111.68:9400/metrics"
        ]
        
        active_exporters = 0
        for url in test_urls:
            success, stdout, stderr = self.run_command(f"curl -s {url} | grep hygon_", check=False)
            if success and "hygon_" in stdout:
                self.print_success(f"Exporter正常: {url}")
                active_exporters += 1
            else:
                self.print_warning(f"Exporter异常: {url}")
        
        if active_exporters > 0:
            self.print_success(f"发现 {active_exporters} 个正常运行的Exporter")
        else:
            self.print_error("没有发现正常运行的Exporter")
        
        # 检查Prometheus
        success, stdout, stderr = self.run_command("curl -s http://192.7.111.66:9090/api/v1/targets", check=False)
        if success:
            self.print_success("Prometheus服务正常")
        else:
            self.print_warning("Prometheus服务异常")
        
        # 检查Grafana
        success, stdout, stderr = self.run_command("curl -s http://192.7.111.66:3000/api/health", check=False)
        if success:
            self.print_success("Grafana服务正常")
        else:
            self.print_warning("Grafana服务异常")

    def deploy(self, servers):
        """执行完整部署流程"""
        self.print_colored("🚀 海光DCU监控系统一键部署", Colors.CYAN)
        self.print_colored("=" * 50, Colors.CYAN)
        
        try:
            # 检查环境
            if not self.check_prerequisites():
                return False
            
            # 构建项目
            if not self.build_exporter():
                self.print_warning("构建失败，将使用预编译版本")
            
            # 部署Prometheus配置
            if not self.deploy_prometheus():
                return False
            
            # 部署Grafana配置
            if not self.deploy_grafana():
                return False
            
            # 部署Exporter
            if not self.deploy_exporters(servers):
                return False
            
            # 设置监控
            if not self.setup_monitoring():
                return False
            
            # 验证部署
            self.verify_deployment()
            
            # 显示结果
            self.print_colored("=" * 50, Colors.GREEN)
            self.print_success("🎉 海光DCU监控系统部署完成！")
            self.print_colored("\n📊 访问地址:", Colors.CYAN)
            self.print_colored("   Prometheus: http://192.7.111.66:9090", Colors.WHITE)
            self.print_colored("   Grafana: http://192.7.111.66:3000", Colors.WHITE)
            self.print_colored("   Exporter指标: http://192.7.111.66:9400/metrics", Colors.WHITE)
            
            self.print_colored("\n📋 后续步骤:", Colors.CYAN)
            self.print_colored("   1. 登录Grafana查看监控仪表板", Colors.WHITE)
            self.print_colored("   2. 根据需要调整告警阈值", Colors.WHITE)
            self.print_colored("   3. 配置告警通知渠道", Colors.WHITE)
            
            return True
            
        except Exception as e:
            self.print_error(f"部署过程中出现错误: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='海光DCU监控系统一键部署脚本')
    parser.add_argument('--servers', 
                       default='192.7.111.66,192.7.111.67,192.7.111.68',
                       help='目标服务器列表，逗号分隔 (默认: 192.7.111.66,192.7.111.67,192.7.111.68)')
    parser.add_argument('--skip-build', action='store_true',
                       help='跳过构建步骤')
    parser.add_argument('--skip-deploy', action='store_true', 
                       help='跳过远程部署步骤')
    
    args = parser.parse_args()
    
    servers = [s.strip() for s in args.servers.split(',')]
    
    deployer = OneClickDeployer()
    success = deployer.deploy(servers)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
