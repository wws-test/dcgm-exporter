#!/usr/bin/env python3
"""
海光DCU Grafana监控设置脚本
自动配置Grafana数据源和导入监控仪表板
"""

import json
import requests
import argparse
import sys
import os
from pathlib import Path
from urllib.parse import urljoin
from requests.auth import HTTPBasicAuth

class GrafanaSetup:
    def __init__(self, grafana_url, username, password):
        self.grafana_url = grafana_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.project_root = Path(__file__).parent.parent.parent
        
    def test_connection(self):
        """测试Grafana连接"""
        try:
            response = self.session.get(f"{self.grafana_url}/api/health")
            if response.status_code == 200:
                print("✅ Grafana连接成功")
                return True
            else:
                print(f"❌ Grafana连接失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 连接Grafana时出错: {e}")
            return False
    
    def create_datasource(self, prometheus_url):
        """创建Prometheus数据源"""
        datasource_config = {
            "name": "Prometheus",
            "type": "prometheus",
            "url": prometheus_url,
            "access": "proxy",
            "isDefault": True,
            "basicAuth": False,
            "jsonData": {
                "httpMethod": "POST",
                "queryTimeout": "60s",
                "timeInterval": "15s"
            }
        }
        
        try:
            # 检查数据源是否已存在
            response = self.session.get(f"{self.grafana_url}/api/datasources/name/Prometheus")
            if response.status_code == 200:
                print("ℹ️  Prometheus数据源已存在，跳过创建")
                return True
            
            # 创建新数据源
            response = self.session.post(
                f"{self.grafana_url}/api/datasources",
                json=datasource_config
            )
            
            if response.status_code == 200:
                print("✅ Prometheus数据源创建成功")
                return True
            else:
                print(f"❌ 创建数据源失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 创建数据源时出错: {e}")
            return False
    
    def import_dashboard(self, dashboard_file=None):
        """导入仪表板"""
        if dashboard_file is None:
            # 尝试多个可能的仪表板文件位置
            possible_files = [
                self.project_root / "hygon-dcu-dashboard-simple.json",
                self.project_root / "deploy" / "monitoring" / "grafana" / "dashboards" / "hygon-dcu-dashboard.json",
                Path(__file__).parent.parent / "monitoring" / "grafana" / "dashboards" / "hygon-dcu-dashboard.json"
            ]
            
            dashboard_file = None
            for file_path in possible_files:
                if file_path.exists():
                    dashboard_file = file_path
                    break
        
        if not dashboard_file or not Path(dashboard_file).exists():
            print(f"❌ 仪表板文件不存在")
            print("请确保以下文件之一存在:")
            for file_path in possible_files:
                print(f"   - {file_path}")
            return False
        
        try:
            with open(dashboard_file, 'r', encoding='utf-8') as f:
                dashboard_json = json.load(f)
            
            # 准备导入数据
            import_data = {
                "dashboard": dashboard_json,
                "overwrite": True,
                "inputs": [
                    {
                        "name": "DS_PROMETHEUS",
                        "type": "datasource",
                        "pluginId": "prometheus",
                        "value": "Prometheus"
                    }
                ]
            }
            
            response = self.session.post(
                f"{self.grafana_url}/api/dashboards/import",
                json=import_data
            )
            
            if response.status_code == 200:
                result = response.json()
                dashboard_url = f"{self.grafana_url}/d/{result.get('uid', '')}/{result.get('slug', '')}"
                print(f"✅ 仪表板导入成功")
                print(f"🔗 仪表板地址: {dashboard_url}")
                return True
            else:
                print(f"❌ 导入仪表板失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 导入仪表板时出错: {e}")
            return False
    
    def create_folder(self, folder_name):
        """创建仪表板文件夹"""
        folder_config = {
            "title": folder_name
        }
        
        try:
            response = self.session.post(
                f"{self.grafana_url}/api/folders",
                json=folder_config
            )
            
            if response.status_code == 200:
                print(f"✅ 文件夹 '{folder_name}' 创建成功")
                return True
            elif response.status_code == 409:
                print(f"ℹ️  文件夹 '{folder_name}' 已存在")
                return True
            else:
                print(f"❌ 创建文件夹失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 创建文件夹时出错: {e}")
            return False

    def verify_setup(self):
        """验证监控设置"""
        print("\n🔍 验证监控设置...")
        
        # 检查数据源
        try:
            response = self.session.get(f"{self.grafana_url}/api/datasources")
            if response.status_code == 200:
                datasources = response.json()
                prometheus_ds = [ds for ds in datasources if ds['type'] == 'prometheus']
                if prometheus_ds:
                    print(f"✅ 发现 {len(prometheus_ds)} 个Prometheus数据源")
                else:
                    print("❌ 未发现Prometheus数据源")
            else:
                print("❌ 无法获取数据源列表")
        except Exception as e:
            print(f"❌ 检查数据源时出错: {e}")
        
        # 检查仪表板
        try:
            response = self.session.get(f"{self.grafana_url}/api/search?type=dash-db")
            if response.status_code == 200:
                dashboards = response.json()
                hygon_dashboards = [db for db in dashboards if 'hygon' in db.get('title', '').lower() or 'dcu' in db.get('title', '').lower()]
                if hygon_dashboards:
                    print(f"✅ 发现 {len(hygon_dashboards)} 个海光DCU相关仪表板")
                    for db in hygon_dashboards:
                        print(f"   - {db['title']}: {self.grafana_url}/d/{db['uid']}")
                else:
                    print("❌ 未发现海光DCU相关仪表板")
            else:
                print("❌ 无法获取仪表板列表")
        except Exception as e:
            print(f"❌ 检查仪表板时出错: {e}")

def main():
    parser = argparse.ArgumentParser(description='海光DCU Grafana监控设置脚本')
    parser.add_argument('--grafana-url', default='http://192.7.111.66:3000',
                       help='Grafana服务器地址 (默认: http://192.7.111.66:3000)')
    parser.add_argument('--prometheus-url', default='http://192.7.111.66:9090',
                       help='Prometheus服务器地址 (默认: http://192.7.111.66:9090)')
    parser.add_argument('--username', default='admin',
                       help='Grafana用户名 (默认: admin)')
    parser.add_argument('--password', default='admin',
                       help='Grafana密码 (默认: admin)')
    parser.add_argument('--dashboard-file',
                       help='仪表板JSON文件路径 (可选，自动查找)')
    parser.add_argument('--skip-datasource', action='store_true',
                       help='跳过数据源创建')
    parser.add_argument('--skip-dashboard', action='store_true',
                       help='跳过仪表板导入')
    parser.add_argument('--verify-only', action='store_true',
                       help='仅验证现有配置')
    
    args = parser.parse_args()
    
    print("🚀 开始设置海光DCU Grafana监控...")
    print(f"📊 Grafana地址: {args.grafana_url}")
    print(f"📈 Prometheus地址: {args.prometheus_url}")
    
    # 初始化Grafana设置
    grafana = GrafanaSetup(args.grafana_url, args.username, args.password)
    
    # 测试连接
    if not grafana.test_connection():
        sys.exit(1)
    
    if args.verify_only:
        grafana.verify_setup()
        sys.exit(0)
    
    success = True
    
    # 创建数据源
    if not args.skip_datasource:
        print("\n📊 配置Prometheus数据源...")
        if not grafana.create_datasource(args.prometheus_url):
            success = False
    
    # 创建文件夹
    print("\n📁 创建仪表板文件夹...")
    if not grafana.create_folder("海光DCU监控"):
        success = False
    
    # 导入仪表板
    if not args.skip_dashboard:
        print("\n📈 导入监控仪表板...")
        if not grafana.import_dashboard(args.dashboard_file):
            success = False
    
    # 验证设置
    grafana.verify_setup()
    
    if success:
        print("\n🎉 海光DCU Grafana监控设置完成！")
        print(f"🔗 访问仪表板: {args.grafana_url}/dashboards")
        print("\n📋 后续步骤:")
        print("1. 确保DCGM-Exporter正在运行 (--use-hygon-mode)")
        print("2. 验证Prometheus正在抓取指标")
        print("3. 检查仪表板是否显示数据")
        print("4. 根据需要配置告警规则")
    else:
        print("\n❌ 设置过程中出现错误，请检查上述错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()
