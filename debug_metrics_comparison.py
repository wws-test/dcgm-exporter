#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海光DCU指标对比调试工具
比较hy-smi输出与exporter指标的差异
"""

import subprocess
import requests
import re
import json
from typing import Dict, List, Any

def run_hy_smi() -> Dict[str, Any]:
    """运行hy-smi并解析输出"""
    try:
        result = subprocess.run(['/usr/local/hyhal/bin/hy-smi'], 
                              capture_output=True, text=True, check=True)
        
        lines = result.stdout.strip().split('\n')
        devices = {}
        
        # 查找数据行（跳过标题行）
        data_started = False
        for line in lines:
            if 'DCU' in line and 'Temp' in line:
                data_started = True
                continue
            
            if data_started and line.strip() and not line.startswith('='):
                parts = line.split()
                if len(parts) >= 8:
                    dcu_id = parts[0]
                    temp = float(parts[1].replace('C', ''))
                    power = float(parts[2].replace('W', ''))
                    perf = parts[3]
                    power_cap = float(parts[4].replace('W', ''))
                    vram_percent = float(parts[5].replace('%', ''))
                    dcu_percent = float(parts[6].replace('%', ''))
                    mode = parts[7]
                    
                    devices[dcu_id] = {
                        'temperature': temp,
                        'power': power,
                        'performance': perf,
                        'power_cap': power_cap,
                        'vram_utilization': vram_percent,
                        'dcu_utilization': dcu_percent,
                        'mode': mode
                    }
        
        return devices
    except Exception as e:
        print(f"运行hy-smi失败: {e}")
        return {}

def get_exporter_metrics() -> Dict[str, Any]:
    """获取exporter指标"""
    try:
        response = requests.get('http://localhost:9400/metrics', timeout=10)
        response.raise_for_status()
        
        metrics = {}
        lines = response.text.strip().split('\n')
        
        for line in lines:
            if line.startswith('#') or not line.strip():
                continue
            
            # 解析指标行
            if 'hygon' in line.lower():
                # 提取指标名称和值
                parts = line.split()
                if len(parts) >= 2:
                    metric_part = parts[0]
                    value = parts[1]
                    
                    # 解析标签
                    if '{' in metric_part:
                        metric_name = metric_part.split('{')[0]
                        labels_str = metric_part.split('{')[1].split('}')[0]
                        labels = {}
                        for label_pair in labels_str.split(','):
                            if '=' in label_pair:
                                key, val = label_pair.split('=', 1)
                                labels[key.strip()] = val.strip('"')
                    else:
                        metric_name = metric_part
                        labels = {}
                    
                    if metric_name not in metrics:
                        metrics[metric_name] = []
                    
                    metrics[metric_name].append({
                        'labels': labels,
                        'value': float(value)
                    })
        
        return metrics
    except Exception as e:
        print(f"获取exporter指标失败: {e}")
        return {}

def compare_metrics():
    """对比hy-smi和exporter指标"""
    print("=" * 80)
    print("海光DCU指标对比分析")
    print("=" * 80)
    
    # 获取hy-smi数据
    print("\n1. 获取hy-smi数据...")
    hy_smi_data = run_hy_smi()
    if hy_smi_data:
        print(f"   发现 {len(hy_smi_data)} 个DCU设备")
        for dcu_id, data in hy_smi_data.items():
            print(f"   DCU {dcu_id}: 温度={data['temperature']}°C, "
                  f"功耗={data['power']}W, DCU使用率={data['dcu_utilization']}%, "
                  f"显存使用率={data['vram_utilization']}%")
    else:
        print("   未获取到hy-smi数据")
    
    # 获取exporter数据
    print("\n2. 获取exporter指标...")
    exporter_data = get_exporter_metrics()
    if exporter_data:
        print(f"   发现 {len(exporter_data)} 种指标类型")
        for metric_name, values in exporter_data.items():
            print(f"   {metric_name}: {len(values)} 个数据点")
    else:
        print("   未获取到exporter指标")
    
    # 对比分析
    print("\n3. 对比分析...")
    if not hy_smi_data:
        print("   无法进行对比：hy-smi数据为空")
        return
    
    if not exporter_data:
        print("   无法进行对比：exporter数据为空")
        print("   可能的原因：")
        print("   - exporter服务未运行")
        print("   - exporter端口不是9400")
        print("   - exporter没有正确读取DCU数据")
        return
    
    # 检查设备数量匹配
    hy_smi_count = len(hy_smi_data)
    exporter_device_count = 0
    
    # 尝试从不同指标中获取设备数量
    for metric_name, values in exporter_data.items():
        if 'utilization' in metric_name or 'temperature' in metric_name:
            exporter_device_count = max(exporter_device_count, len(values))
    
    print(f"\n   设备数量对比:")
    print(f"   hy-smi: {hy_smi_count} 个设备")
    print(f"   exporter: {exporter_device_count} 个设备")
    
    if hy_smi_count != exporter_device_count:
        print("   ⚠️  设备数量不匹配！")
    else:
        print("   ✅ 设备数量匹配")
    
    # 详细指标对比
    print(f"\n   详细指标对比:")
    for dcu_id, hy_data in hy_smi_data.items():
        print(f"\n   DCU {dcu_id}:")
        
        # 查找对应的exporter数据
        found_temp = False
        found_power = False
        found_util = False
        found_mem = False
        
        for metric_name, values in exporter_data.items():
            for value_data in values:
                labels = value_data['labels']
                if labels.get('device_id') == dcu_id:
                    if 'temperature' in metric_name:
                        print(f"     温度: hy-smi={hy_data['temperature']}°C, exporter={value_data['value']}°C")
                        found_temp = True
                    elif 'power' in metric_name:
                        print(f"     功耗: hy-smi={hy_data['power']}W, exporter={value_data['value']}W")
                        found_power = True
                    elif 'utilization' in metric_name and 'memory' not in metric_name:
                        print(f"     DCU使用率: hy-smi={hy_data['dcu_utilization']}%, exporter={value_data['value']}%")
                        found_util = True
                    elif 'memory' in metric_name and 'utilization' in metric_name:
                        print(f"     显存使用率: hy-smi={hy_data['vram_utilization']}%, exporter={value_data['value']}%")
                        found_mem = True
        
        if not found_temp:
            print(f"     ❌ 未找到温度指标")
        if not found_power:
            print(f"     ❌ 未找到功耗指标")
        if not found_util:
            print(f"     ❌ 未找到DCU使用率指标")
        if not found_mem:
            print(f"     ❌ 未找到显存使用率指标")

def main():
    """主函数"""
    try:
        compare_metrics()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序执行出错: {e}")

if __name__ == "__main__":
    main()
