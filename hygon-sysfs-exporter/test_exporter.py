#!/usr/bin/env python3
"""
海光DCU Exporter 测试脚本
用于测试exporter的各项功能
"""

import requests
import time
import sys
import argparse
from urllib.parse import urljoin

class HygonExporterTester:
    def __init__(self, base_url="http://localhost:9400"):
        self.base_url = base_url
        self.metrics_url = urljoin(base_url, "/metrics")
        
    def test_connection(self):
        """测试连接"""
        print(f"测试连接到 {self.base_url}...")
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code == 200:
                print("✓ 连接成功")
                return True
            else:
                print(f"✗ 连接失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 连接失败: {e}")
            return False
    
    def get_metrics(self):
        """获取指标"""
        try:
            response = requests.get(self.metrics_url, timeout=10)
            if response.status_code == 200:
                return response.text
            else:
                print(f"获取指标失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            print(f"获取指标失败: {e}")
            return None
    
    def parse_metrics(self, metrics_text):
        """解析指标"""
        metrics = {}
        for line in metrics_text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split(' ')
                if len(parts) >= 2:
                    metric_name = parts[0]
                    metric_value = parts[1]
                    metrics[metric_name] = metric_value
        return metrics
    
    def test_metrics(self):
        """测试指标"""
        print("测试指标获取...")
        metrics_text = self.get_metrics()
        if not metrics_text:
            return False
        
        metrics = self.parse_metrics(metrics_text)
        
        # 检查关键指标
        key_metrics = [
            'hygon_dcu_utilization_percent',
            'hygon_memory_utilization_percent', 
            'hygon_power_watts',
            'hygon_vram_total_bytes',
            'hygon_vram_usage_bytes',
            'hygon_temperature_celsius',
            'hygon_device_info'
        ]
        
        found_metrics = []
        missing_metrics = []
        
        for key_metric in key_metrics:
            found = False
            for metric_name in metrics.keys():
                if metric_name.startswith(key_metric):
                    found_metrics.append(metric_name)
                    found = True
                    break
            if not found:
                missing_metrics.append(key_metric)
        
        print(f"✓ 找到 {len(found_metrics)} 个关键指标")
        for metric in found_metrics[:5]:  # 显示前5个
            print(f"  - {metric}: {metrics.get(metric, 'N/A')}")
        
        if missing_metrics:
            print(f"✗ 缺失 {len(missing_metrics)} 个关键指标:")
            for metric in missing_metrics:
                print(f"  - {metric}")
        
        return len(missing_metrics) == 0
    
    def test_device_discovery(self):
        """测试设备发现"""
        print("测试设备发现...")
        metrics_text = self.get_metrics()
        if not metrics_text:
            return False
        
        device_count = 0
        device_serials = set()
        
        for line in metrics_text.split('\n'):
            if 'hygon_device_info' in line and not line.startswith('#'):
                device_count += 1
                # 提取序列号
                if 'serial=' in line:
                    start = line.find('serial="') + 8
                    end = line.find('"', start)
                    if end > start:
                        serial = line[start:end]
                        device_serials.add(serial)
        
        print(f"✓ 发现 {device_count} 个DCU设备")
        for i, serial in enumerate(device_serials):
            print(f"  设备{i+1}: {serial}")
        
        return device_count > 0
    
    def monitor_metrics(self, duration=60, interval=5):
        """监控指标变化"""
        print(f"开始监控指标变化 (持续{duration}秒，间隔{interval}秒)...")
        
        start_time = time.time()
        iteration = 0
        
        while time.time() - start_time < duration:
            iteration += 1
            print(f"\n--- 第{iteration}次采样 ---")
            
            metrics_text = self.get_metrics()
            if metrics_text:
                metrics = self.parse_metrics(metrics_text)
                
                # 显示关键指标
                key_patterns = [
                    'hygon_dcu_utilization_percent',
                    'hygon_power_watts',
                    'hygon_temperature_celsius'
                ]
                
                for pattern in key_patterns:
                    for metric_name, value in metrics.items():
                        if pattern in metric_name:
                            print(f"{metric_name}: {value}")
                            break
            
            time.sleep(interval)
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=== 海光DCU Exporter 测试 ===\n")
        
        tests = [
            ("连接测试", self.test_connection),
            ("指标测试", self.test_metrics),
            ("设备发现测试", self.test_device_discovery)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            if test_func():
                passed += 1
                print(f"✓ {test_name} 通过")
            else:
                print(f"✗ {test_name} 失败")
        
        print(f"\n=== 测试结果: {passed}/{total} 通过 ===")
        return passed == total

def main():
    parser = argparse.ArgumentParser(description="海光DCU Exporter 测试工具")
    parser.add_argument("--url", default="http://localhost:9400", help="Exporter URL")
    parser.add_argument("--test", choices=["all", "connection", "metrics", "devices", "monitor"], 
                       default="all", help="测试类型")
    parser.add_argument("--duration", type=int, default=60, help="监控持续时间(秒)")
    parser.add_argument("--interval", type=int, default=5, help="监控间隔(秒)")
    
    args = parser.parse_args()
    
    tester = HygonExporterTester(args.url)
    
    if args.test == "all":
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    elif args.test == "connection":
        success = tester.test_connection()
    elif args.test == "metrics":
        success = tester.test_metrics()
    elif args.test == "devices":
        success = tester.test_device_discovery()
    elif args.test == "monitor":
        tester.monitor_metrics(args.duration, args.interval)
        success = True
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
