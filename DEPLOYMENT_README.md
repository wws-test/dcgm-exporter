# 海光DCU监控系统部署指南

[![海光DCU](https://img.shields.io/badge/海光DCU-支持-blue.svg)](https://www.hygon.cn/)
[![Prometheus](https://img.shields.io/badge/Prometheus-监控-orange.svg)](https://prometheus.io/)
[![Grafana](https://img.shields.io/badge/Grafana-可视化-green.svg)](https://grafana.com/)

## 🚀 快速部署

### 一键部署（推荐）

```bash
# 1. 进入部署目录
cd deploy/scripts

# 2. 一键部署完整监控系统
python one_click_deploy.py --servers 192.2.111.66

# 3. 验证部署
curl http://192.2.111.66:9400/metrics | grep hygon_
```

### 分步部署

```bash
# 1. 构建海光DCU Exporter
cd build
./build-hygon.sh

# 2. 部署到远程服务器
cd ../deploy/scripts
python remote_deploy.py --servers 192.2.111.66

# 3. 设置Grafana监控
python setup_grafana_monitoring.py --grafana-url http://192.2.111.66:3000
```

## 📋 部署前准备

### 系统要求
- **操作系统**: Linux (Ubuntu 18.04+, CentOS 7+)
- **海光DCU**: 已安装海光DCU驱动和hy-smi工具
- **Go环境**: Go 1.21+ (用于编译)
- **Python**: Python 3.6+ (用于部署脚本)

### 网络端口
- **9400**: 海光DCU Exporter
- **9090**: Prometheus
- **3000**: Grafana
- **9100**: Node Exporter (可选)

## 🛠️ 部署脚本说明

### 核心部署脚本

#### 1. 一键部署脚本
**位置**: `deploy/scripts/one_click_deploy.py`

**功能**:
- ✅ 自动构建海光DCU Exporter
- ✅ 部署Prometheus配置
- ✅ 部署Grafana仪表板
- ✅ 远程部署到多台服务器
- ✅ 验证部署结果

**使用方法**:
```bash
python one_click_deploy.py [选项]

选项:
  --servers SERVERS     目标服务器列表，逗号分隔 (默认: 192.2.111.66)
  --skip-build         跳过构建步骤
  --skip-deploy        跳过远程部署步骤
  --help               显示帮助信息
```

**示例**:
```bash
# 部署到单台服务器
python one_click_deploy.py --servers 192.2.111.66

# 部署到多台服务器
python one_click_deploy.py --servers 192.2.111.66,192.2.111.67,192.2.111.68

# 跳过构建，仅部署
python one_click_deploy.py --servers 192.2.111.66 --skip-build
```

#### 2. Grafana监控设置脚本
**位置**: `deploy/scripts/setup_grafana_monitoring.py`

**功能**:
- ✅ 自动创建Prometheus数据源
- ✅ 导入海光DCU监控仪表板
- ✅ 配置告警规则
- ✅ 验证监控设置

**使用方法**:
```bash
python setup_grafana_monitoring.py [选项]

选项:
  --grafana-url URL     Grafana地址 (默认: http://localhost:3000)
  --prometheus-url URL  Prometheus地址 (默认: http://localhost:9090)
  --username USER       Grafana用户名 (默认: admin)
  --password PASS       Grafana密码 (默认: admin)
  --dashboard-file FILE 仪表板文件路径
  --skip-datasource     跳过数据源创建
  --skip-dashboard      跳过仪表板导入
  --verify-only         仅验证现有配置
```

**示例**:
```bash
# 基本设置
python setup_grafana_monitoring.py --grafana-url http://192.2.111.66:3000

# 使用自定义密码
python setup_grafana_monitoring.py \
  --grafana-url http://192.2.111.66:3000 \
  --username admin \
  --password mypassword

# 仅验证配置
python setup_grafana_monitoring.py --verify-only
```

#### 3. Shell版本Grafana设置
**位置**: `deploy/scripts/setup_grafana_monitoring.sh`

**功能**: 轻量级Shell实现，无需Python依赖

**使用方法**:
```bash
./setup_grafana_monitoring.sh [选项]

选项:
  -g, --grafana-url URL     Grafana地址
  -p, --prometheus-url URL  Prometheus地址
  -u, --username USER       用户名
  -P, --password PASS       密码
  -d, --dashboard-file FILE 仪表板文件
  -h, --help               显示帮助
```

## 📊 监控配置

### Prometheus配置
**位置**: `deploy/monitoring/prometheus/prometheus.yml`

**关键配置**:
```yaml
scrape_configs:
  - job_name: 'hygon-dcu-exporter'
    static_configs:
      - targets: ['192.2.111.66:9400']
    scrape_interval: 30s
    scrape_timeout: 10s
    metrics_path: /metrics
```

### Grafana仪表板
**位置**: `deploy/monitoring/grafana/dashboards/hygon-dcu-dashboard.json`

**包含面板**:
- 🔥 海光DCU使用率
- 🌡️ 海光DCU温度
- ⚡ 海光DCU功耗
- 💾 海光DCU显存使用率
- 📊 设备统计信息

## 🔍 部署验证

### 1. 检查服务状态
```bash
# 检查海光DCU Exporter
curl http://192.2.111.66:9400/metrics | grep hygon_

# 检查Prometheus
curl http://192.2.111.66:9090/api/v1/targets

# 检查Grafana
curl http://192.2.111.66:3000/api/health
```

### 2. 验证指标收集
```bash
# 查看海光DCU使用率
curl -s "http://192.2.111.66:9090/api/v1/query?query=hygon_dcu_utilization_percent"

# 查看海光DCU温度
curl -s "http://192.2.111.66:9090/api/v1/query?query=hygon_temperature_celsius"

# 查看海光DCU功耗
curl -s "http://192.2.111.66:9090/api/v1/query?query=hygon_power_watts"
```

### 3. 访问监控界面
- **Prometheus**: http://192.2.111.66:9090
- **Grafana**: http://192.2.111.66:3000
  - 用户名: `admin`
  - 密码: `admin`

## 🚨 常见问题

### Q1: 海光DCU Exporter无法启动
**解决方案**:
```bash
# 检查海光DCU驱动
hy-smi

# 检查sysfs路径
ls -la /sys/class/drm/card*/device/

# 检查权限
sudo chown root:root /opt/hygon-dcu-exporter/hygon-dcu-exporter
sudo chmod +x /opt/hygon-dcu-exporter/hygon-dcu-exporter
```

### Q2: Prometheus无法抓取指标
**解决方案**:
```bash
# 检查配置文件
cat /etc/prometheus/prometheus.yml | grep hygon

# 重新加载配置
curl -X POST http://localhost:9090/-/reload

# 检查目标状态
curl http://localhost:9090/api/v1/targets
```

### Q3: Grafana仪表板无数据
**解决方案**:
```bash
# 检查数据源配置
curl -u admin:admin http://localhost:3000/api/datasources

# 重新设置监控
cd deploy/scripts
python setup_grafana_monitoring.py --grafana-url http://192.2.111.66:3000
```

### Q4: IP地址变更后的处理
**影响的配置文件**:
- `/etc/prometheus/prometheus.yml`
- Grafana数据源配置

**解决方案**:
```bash
# 更新Prometheus配置
sudo sed -i 's/旧IP/新IP/g' /etc/prometheus/prometheus.yml
curl -X POST http://localhost:9090/-/reload

# 重新设置Grafana
python setup_grafana_monitoring.py --grafana-url http://新IP:3000
```

## 📈 监控指标说明

### 海光DCU核心指标

| 指标名称 | 类型 | 说明 | 单位 |
|---------|------|------|------|
| `hygon_dcu_utilization_percent` | Gauge | DCU使用率 | % |
| `hygon_temperature_celsius` | Gauge | DCU温度 | °C |
| `hygon_power_watts` | Gauge | DCU功耗 | W |
| `hygon_power_cap_watts` | Gauge | DCU功耗上限 | W |
| `hygon_memory_utilization_percent` | Gauge | 显存使用率 | % |
| `hygon_vram_total_bytes` | Gauge | 显存总量 | Bytes |
| `hygon_vram_usage_bytes` | Gauge | 显存使用量 | Bytes |
| `hygon_fan_speed_rpm` | Gauge | 风扇转速 | RPM |
| `hygon_device_info` | Info | 设备信息 | - |

### 标签说明
- `device`: DCU设备名称 (hygon1, hygon2, ...)
- `gpu`: GPU编号 (1, 2, 3, ...)
- `hostname`: 主机名
- `serial`: 设备序列号
- `uuid`: 设备UUID

## 🔧 高级配置

### 自定义抓取间隔
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'hygon-dcu-exporter'
    static_configs:
      - targets: ['192.2.111.66:9400']
    scrape_interval: 15s  # 自定义间隔
    scrape_timeout: 5s    # 自定义超时
```

### 添加告警规则
```yaml
# rules/hygon-alerts.yml
groups:
  - name: hygon-dcu-alerts
    rules:
      - alert: HygonDCUHighTemperature
        expr: hygon_temperature_celsius > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "海光DCU温度过高"
          description: "设备 {{ $labels.device }} 温度达到 {{ $value }}°C"
```

## 📞 技术支持

如果在部署过程中遇到问题：

1. **查看日志**:
   ```bash
   # Exporter日志
   tail -f /opt/hygon-dcu-exporter/exporter.log
   
   # Prometheus日志
   sudo journalctl -u prometheus -f
   
   # Grafana日志
   tail -f /opt/grafana/grafana.log
   ```

2. **检查系统状态**:
   ```bash
   # 检查端口占用
   netstat -tlnp | grep -E "(9090|9400|3000)"
   
   # 检查进程状态
   ps aux | grep -E "(prometheus|grafana|hygon)"
   ```

3. **重启服务**:
   ```bash
   # 重启所有监控服务
   sudo systemctl restart prometheus
   sudo systemctl restart grafana-server
   pkill -f hygon-dcu-exporter
   cd /opt/hygon-dcu-exporter && nohup ./hygon-dcu-exporter --web.listen-address=:9400 > exporter.log 2>&1 &
   ```

---

**🎯 让海光DCU监控部署变得简单！**
