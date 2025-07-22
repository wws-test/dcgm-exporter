# 海光DCU监控系统说明

## DCU设备编号对应关系

### hy-smi vs Grafana面板

| hy-smi显示 | Grafana面板显示 | 设备标识 | 说明 |
|------------|----------------|----------|------|
| DCU 0      | DCU 1          | hygon1   | 第一张卡 |
| DCU 1      | DCU 2          | hygon2   | 第二张卡 |
| DCU 2      | DCU 3          | hygon3   | 第三张卡 |
| DCU 3      | DCU 4          | hygon4   | 第四张卡 |
| DCU 4      | DCU 5          | hygon5   | 第五张卡 |
| DCU 5      | DCU 6          | hygon6   | 第六张卡 |
| DCU 6      | DCU 7          | hygon7   | 第七张卡 |
| DCU 7      | DCU 8          | hygon8   | 第八张卡 |

**注意**: hy-smi使用0-7编号，而exporter使用1-8编号，两者相差1。

## 如何查看单张卡的详细信息

### 方法1: 使用单卡监控面板
1. 导入 `hygon-single-dcu-dashboard.json` 面板
2. 在面板顶部的下拉菜单中选择要查看的DCU编号(1-8)
3. 面板会显示该卡的详细指标

### 方法2: 在现有面板中筛选
1. 在图表的图例中点击其他DCU的名称来隐藏它们
2. 只保留你想查看的DCU可见
3. 可以通过点击图例项目来切换显示/隐藏

### 方法3: 使用Prometheus查询
直接在Grafana的Explore页面使用以下查询：

```promql
# 查看DCU 1的使用率
hygon_dcu_utilization_percent{gpu="1"}

# 查看DCU 1的温度
hygon_temperature_celsius{gpu="1",sensor="edge"}

# 查看DCU 1的功耗
hygon_power_watts{gpu="1"}

# 查看DCU 1的显存使用率
hygon_vram_usage_bytes{gpu="1"} / hygon_vram_total_bytes{gpu="1"} * 100
```

## 指标单位说明

| 指标类型 | hy-smi单位 | Grafana单位 | 说明 |
|----------|------------|-------------|------|
| 温度     | °C         | °C          | 摄氏度 |
| 功耗     | W          | W           | 瓦特 |
| DCU使用率| %          | %           | 百分比 |
| 显存使用率| %         | %           | 百分比 |
| 显存容量 | -          | GB          | 千兆字节 |

## 常见问题排查

### 1. 数据不匹配
如果发现Grafana显示的数据与hy-smi不一致：
- 检查时间范围是否正确
- 确认exporter服务正常运行
- 验证Prometheus是否正常采集数据

### 2. 某张卡数据缺失
- 检查该DCU是否正常工作
- 查看exporter日志是否有错误
- 确认sysfs路径是否可访问

### 3. 温度传感器说明
每张DCU有多个温度传感器：
- `edge`: 核心温度（主要参考）
- `memory`: 显存温度
- `hotspot`: 热点温度

## 调试命令

```bash
# 查看hy-smi输出
/usr/local/hyhal/bin/hy-smi

# 查看exporter指标
curl http://localhost:9400/metrics | grep hygon

# 对比hy-smi和exporter数据
python3 /opt/hygon-dcu-exporter/debug_metrics_comparison.py

# 重启exporter服务
python3 /opt/hygon-dcu-exporter/restart_exporter.py
```

## 面板文件说明

1. **hygon-dcu-dashboard-simple.json**: 基础监控面板，显示所有DCU概览
2. **hygon-single-dcu-dashboard.json**: 单卡详细监控面板
3. **hygon-dcu-detailed-dashboard.json**: 详细监控面板，包含更多传感器数据

选择适合您需求的面板导入到Grafana中使用。

## 新增系统监控功能

### 系统指标监控
最新的面板配置已经包含了以下系统监控功能：

#### 时间序列图表
1. **系统CPU使用率**: 显示CPU整体使用率趋势
2. **系统内存使用率**: 显示内存使用率变化
3. **系统磁盘IO**: 显示各磁盘的读写速度
4. **系统网络IO**: 显示网络接口的收发流量
5. **系统负载**: 显示1分钟、5分钟、15分钟平均负载

#### 状态面板
1. **当前CPU使用率**: 实时CPU使用率百分比
2. **当前内存使用率**: 实时内存使用率百分比
3. **系统总内存**: 显示系统总内存容量
4. **系统运行时间**: 显示系统启动后的运行时间

### 面板布局说明
```
┌─────────────────┬─────────────────┐
│   DCU使用率     │    DCU温度      │
├─────────────────┼─────────────────┤
│   DCU功耗       │   DCU显存使用率 │
├─────────────────┼─────────────────┤
│ DCU设备数量 │平均温度│总功耗│平均使用率│
├─────────────────┼─────────────────┤
│  系统CPU使用率  │  系统内存使用率 │
├─────────────────┼─────────────────┤
│  系统磁盘IO     │   系统负载      │
├─────────────────┼─────────────────┤
│当前CPU│当前内存│总内存│运行时间│
├─────────────────┼─────────────────┤
│   系统网络IO    │                 │
└─────────────────┴─────────────────┘
```

### 系统指标说明

| 指标类型 | 单位 | 说明 | 正常范围 |
|----------|------|------|----------|
| CPU使用率 | % | 系统CPU整体使用率 | < 80% |
| 内存使用率 | % | 系统内存使用率 | < 90% |
| 系统负载 | 数值 | 系统平均负载 | < CPU核心数 |
| 磁盘IO | Bytes/s | 磁盘读写速度 | 根据磁盘性能 |
| 网络IO | Bytes/s | 网络收发速度 | 根据网络带宽 |
| 运行时间 | 秒 | 系统启动后运行时间 | - |

### 依赖服务检查

使用以下命令检查所需服务状态：

```bash
# 检查所有监控服务状态
python3 /opt/hygon-dcu-exporter/check_prometheus_config.py

# 检查node_exporter状态
curl http://localhost:9100/metrics | head -5

# 检查海光DCU exporter状态
curl http://localhost:9400/metrics | grep hygon | head -5
```

### 故障排除

#### 系统指标不显示
1. 检查node_exporter是否运行: `systemctl status node_exporter`
2. 检查端口9100是否可访问: `curl localhost:9100/metrics`
3. 检查Prometheus配置是否包含node_exporter target

#### DCU指标不显示
1. 检查海光DCU exporter是否运行
2. 检查端口9400是否可访问
3. 检查sysfs路径权限

#### 网络连接问题
如果Prometheus服务器无法访问，请检查：
1. 网络连通性: `ping 192.7.111.66`
2. 防火墙设置
3. Prometheus服务状态
