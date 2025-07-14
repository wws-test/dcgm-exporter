# 海光DCU Exporter

基于sysfs的海光DCU监控指标导出器，专为海光DCU设计的Prometheus exporter。

## 特性

- **纯sysfs实现**: 直接读取Linux内核sysfs文件系统，无需依赖hy-smi工具
- **高性能**: 避免外部命令调用开销，直接文件读取
- **实时监控**: 支持所有关键DCU指标的实时采集
- **标准格式**: 输出标准Prometheus格式的metrics
- **自动发现**: 自动发现系统中的海光DCU设备

## 支持的指标

### 基础性能指标
- `hygon_dcu_utilization_percent`: DCU使用率 (%)
- `hygon_memory_utilization_percent`: 内存使用率 (%)
- `hygon_power_watts`: 平均功耗 (W)

### 内存指标
- `hygon_vram_total_bytes`: VRAM总量 (bytes)
- `hygon_vram_usage_bytes`: VRAM使用量 (bytes)

### 温度指标
- `hygon_temperature_celsius`: 温度 (°C)
  - `sensor="edge"`: 边缘温度
  - `sensor="junction"`: 结温
  - `sensor="memory"`: 显存温度

### 功耗指标
- `hygon_power_cap_watts`: 功耗上限 (W)

### 风扇指标
- `hygon_fan_speed_rpm`: 风扇转速 (RPM)

### 设备信息
- `hygon_device_info`: 设备信息标签 (值恒为1)

## 快速开始

### 编译
```bash
go build -o hygon-dcu-exporter .
```

### 运行
```bash
./hygon-dcu-exporter
```

默认监听端口: `:9400`

### 查看指标
```bash
curl http://localhost:9400/metrics
```

## 命令行参数

- `-web.listen-address`: HTTP服务监听地址 (默认: `:9400`)

## 系统要求

- Linux系统
- 海光DCU驱动已安装
- Go 1.21+

## sysfs数据源

本exporter直接读取以下sysfs路径：

```
/sys/class/drm/card{N}/device/
├── gpu_busy_percent          # DCU使用率
├── mem_busy_percent          # 内存使用率
├── chip_power_average        # 平均功耗(mW)
├── mem_info_vram_total       # VRAM总量
├── mem_info_vram_used        # VRAM使用量
├── serial_number             # 序列号
├── unique_id                 # 唯一ID
├── product_name              # 产品名称
├── vbios_version             # VBIOS版本
└── hwmon/hwmon{X}/
    ├── temp1_input           # edge温度(毫摄氏度)
    ├── temp2_input           # junction温度(毫摄氏度)
    ├── temp3_input           # memory温度(毫摄氏度)
    ├── power1_cap            # 功耗上限(微瓦)
    └── fan1_input            # 风扇转速(RPM)
```

## 与Prometheus集成

在prometheus.yml中添加：

```yaml
scrape_configs:
  - job_name: 'hygon-dcu'
    static_configs:
      - targets: ['localhost:9400']
    scrape_interval: 15s
```

## 许可证

MIT License
