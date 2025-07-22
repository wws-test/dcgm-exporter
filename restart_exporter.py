#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海光DCU Exporter重启工具
"""

import subprocess
import time
import requests
import sys

def kill_exporter():
    """停止exporter进程"""
    try:
        # 查找并杀死exporter进程
        result = subprocess.run(['pkill', '-f', 'hygon-dcu-exporter'], 
                              capture_output=True, text=True)
        print("已停止现有exporter进程")
        time.sleep(2)
    except Exception as e:
        print(f"停止exporter进程时出错: {e}")

def start_exporter():
    """启动exporter"""
    try:
        # 切换到exporter目录并启动
        cmd = [
            'bash', '-c', 
            'cd /opt/hygon-dcu-exporter && ./hygon-dcu-exporter --web.listen-address=:9400 > exporter.log 2>&1 &'
        ]
        subprocess.run(cmd, check=True)
        print("已启动exporter服务")
        time.sleep(3)
    except Exception as e:
        print(f"启动exporter时出错: {e}")
        return False
    return True

def check_exporter():
    """检查exporter是否正常工作"""
    try:
        response = requests.get('http://localhost:9400/metrics', timeout=5)
        if response.status_code == 200:
            lines = response.text.split('\n')
            hygon_metrics = [line for line in lines if 'hygon' in line.lower() and not line.startswith('#')]
            
            print(f"✅ Exporter正常运行")
            print(f"   - HTTP状态: {response.status_code}")
            print(f"   - 总指标行数: {len(lines)}")
            print(f"   - 海光相关指标: {len(hygon_metrics)}")
            
            if hygon_metrics:
                print("   - 海光指标示例:")
                for metric in hygon_metrics[:3]:
                    print(f"     {metric}")
            else:
                print("   ⚠️  未发现海光相关指标")
            
            return True
        else:
            print(f"❌ Exporter响应异常: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到exporter (连接被拒绝)")
        return False
    except Exception as e:
        print(f"❌ 检查exporter时出错: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("海光DCU Exporter重启工具")
    print("=" * 50)
    
    print("\n1. 停止现有exporter进程...")
    kill_exporter()
    
    print("\n2. 启动新的exporter进程...")
    if not start_exporter():
        print("启动失败，退出")
        sys.exit(1)
    
    print("\n3. 检查exporter状态...")
    if check_exporter():
        print("\n✅ Exporter重启成功！")
        print("\n可以使用以下命令进行测试:")
        print("   curl http://localhost:9400/metrics | grep hygon")
        print("   python3 debug_metrics_comparison.py")
    else:
        print("\n❌ Exporter重启失败")
        print("\n请检查日志:")
        print("   tail -20 /opt/hygon-dcu-exporter/exporter.log")

if __name__ == "__main__":
    main()
