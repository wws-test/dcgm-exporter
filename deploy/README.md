# 部署目录

包含项目部署相关的脚本和配置文件。

## 目录结构

- `scripts/` - 部署脚本
- `configs/` - 部署配置文件  
- `monitoring/` - 监控系统配置
- `k8s/` - Kubernetes部署配置

## 快速开始

```bash
# 一键部署监控系统
python scripts/one_click_deploy.py

# 设置Grafana监控
./scripts/setup_grafana_monitoring.sh
```

## 脚本说明

### 核心部署脚本

- **`one_click_deploy.py`** - 一键部署完整监控系统
  - 自动部署Prometheus、Grafana、DCGM-Exporter
  - 支持多服务器批量部署
  - 自动配置监控仪表板

- **`remote_deploy.py`** - 远程服务器部署脚本
  - SSH远程部署DCGM-Exporter
  - 支持海光DCU和NVIDIA GPU模式
  - 自动处理依赖和配置

- **`setup_grafana_monitoring.py`** - Grafana监控设置（Python版）
  - 自动创建Prometheus数据源
  - 导入海光DCU监控仪表板
  - 配置告警规则

- **`setup_grafana_monitoring.sh`** - Grafana监控设置（Shell版）
  - 轻量级Shell实现
  - 快速设置监控环境

## 监控配置

### Prometheus配置
- `monitoring/prometheus/prometheus.yml` - 主配置文件
- `monitoring/prometheus/rules/` - 告警规则

### Grafana配置  
- `monitoring/grafana/dashboards/` - 仪表板配置
- `monitoring/grafana/provisioning/` - 自动配置文件

## 使用示例

```bash
# 完整部署流程
cd deploy/scripts

# 1. 一键部署所有组件
python one_click_deploy.py --servers 192.7.111.66,192.7.111.67,192.7.111.68

# 2. 或者分步部署
python remote_deploy.py --servers 192.7.111.66:9400
python setup_grafana_monitoring.py --grafana-url http://192.7.111.66:3000

# 3. 验证部署
curl http://192.7.111.66:9400/metrics | grep hygon_
```
