#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查Prometheus配置和系统指标可用性
"""

import requests
import subprocess
import json

def check_prometheus_targets():
    """检查Prometheus targets状态"""
    try:
        response = requests.get('http://192.7.111.66:9090/api/v1/targets', timeout=10)
        if response.status_code == 200:
            data = response.json()
            targets = data.get('data', {}).get('activeTargets', [])
            
            print("=== Prometheus Targets 状态 ===")
            for target in targets:
                job = target.get('labels', {}).get('job', 'unknown')
                instance = target.get('labels', {}).get('instance', 'unknown')
                health = target.get('health', 'unknown')
                last_error = target.get('lastError', '')
                
                status_icon = "✅" if health == "up" else "❌"
                print(f"{status_icon} {job} ({instance}) - {health}")
                if last_error:
                    print(f"   错误: {last_error}")
            
            return True
        else:
            print(f"❌ 无法访问Prometheus API: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 检查Prometheus targets失败: {e}")
        return False

def check_local_exporters():
    """检查本地exporter服务"""
    exporters = [
        ("海光DCU Exporter", "http://localhost:9400/metrics"),
        ("Node Exporter", "http://localhost:9100/metrics"),
    ]
    
    print("\n=== 本地Exporter状态 ===")
    for name, url in exporters:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                lines = response.text.split('\n')
                metric_lines = [line for line in lines if line and not line.startswith('#')]
                print(f"✅ {name} - 正常运行 ({len(metric_lines)} 个指标)")
            else:
                print(f"❌ {name} - HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {name} - 连接失败")
        except Exception as e:
            print(f"❌ {name} - 错误: {e}")

def check_system_metrics():
    """检查系统指标可用性"""
    print("\n=== 系统指标检查 ===")
    
    # 检查关键系统指标
    metrics_to_check = [
        ("CPU使用率", "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"),
        ("内存使用率", "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100"),
        ("系统负载", "node_load1"),
        ("磁盘IO", "irate(node_disk_read_bytes_total[5m])"),
        ("网络IO", "irate(node_network_receive_bytes_total{device!=\"lo\"}[5m])"),
    ]
    
    for metric_name, query in metrics_to_check:
        try:
            # 查询Prometheus
            params = {
                'query': query
            }
            response = requests.get('http://192.7.111.66:9090/api/v1/query', 
                                  params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('data', {}).get('result', [])
                if result:
                    print(f"✅ {metric_name} - 有数据 ({len(result)} 个数据点)")
                else:
                    print(f"⚠️  {metric_name} - 无数据")
            else:
                print(f"❌ {metric_name} - 查询失败 HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {metric_name} - 错误: {e}")

def check_hygon_metrics():
    """检查海光DCU指标"""
    print("\n=== 海光DCU指标检查 ===")
    
    hygon_metrics = [
        ("DCU使用率", "hygon_dcu_utilization_percent"),
        ("DCU温度", "hygon_temperature_celsius"),
        ("DCU功耗", "hygon_power_watts"),
        ("显存使用", "hygon_vram_usage_bytes"),
    ]
    
    for metric_name, query in hygon_metrics:
        try:
            params = {
                'query': query
            }
            response = requests.get('http://192.7.111.66:9090/api/v1/query', 
                                  params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('data', {}).get('result', [])
                if result:
                    print(f"✅ {metric_name} - 有数据 ({len(result)} 个DCU)")
                    # 显示第一个DCU的示例数据
                    if result:
                        sample = result[0]
                        labels = sample.get('metric', {})
                        value = sample.get('value', [None, 'N/A'])[1]
                        gpu = labels.get('gpu', 'unknown')
                        print(f"   示例: DCU {gpu} = {value}")
                else:
                    print(f"⚠️  {metric_name} - 无数据")
            else:
                print(f"❌ {metric_name} - 查询失败 HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {metric_name} - 错误: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("Prometheus配置和系统指标检查工具")
    print("=" * 60)
    
    # 检查Prometheus targets
    check_prometheus_targets()
    
    # 检查本地exporters
    check_local_exporters()
    
    # 检查系统指标
    check_system_metrics()
    
    # 检查海光DCU指标
    check_hygon_metrics()
    
    print("\n" + "=" * 60)
    print("检查完成！")
    print("\n如果发现问题，请检查:")
    print("1. Prometheus配置文件是否包含所有targets")
    print("2. Node exporter是否正常运行")
    print("3. 海光DCU exporter是否正常运行")
    print("4. 防火墙设置是否正确")

if __name__ == "__main__":
    main()
