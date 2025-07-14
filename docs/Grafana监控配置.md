# Grafana监控配置指南

本文档详细介绍如何配置Grafana监控海光DCU设备，包括仪表板导入、自定义配置和故障排除。

## 📋 目录

- [环境准备](#环境准备)
- [仪表板导入](#仪表板导入)
- [监控面板说明](#监控面板说明)
- [自定义配置](#自定义配置)
- [告警配置](#告警配置)
- [故障排除](#故障排除)

## 🔧 环境准备

### 前置条件

1. **Prometheus服务器**: 已配置并运行
2. **DCGM-Exporter**: 海光DCU模式正常运行
3. **Grafana服务器**: 版本 >= 8.0
4. **网络连通性**: Grafana能访问Prometheus和Exporter

### Prometheus配置

确保Prometheus配置文件包含海光DCU监控目标：

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'hygon-dcu-exporter'
    static_configs:
      - targets: 
          - '192.7.111.66:9400'  # 替换为实际的exporter地址
          - '192.7.111.67:9400'
          - '192.7.111.68:9400'
    scrape_interval: 30s
    scrape_timeout: 10s
    metrics_path: /metrics
    
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

### Grafana数据源配置

1. 登录Grafana管理界面
2. 导航到 **Configuration** > **Data Sources**
3. 点击 **Add data source**
4. 选择 **Prometheus**
5. 配置连接信息：
   - **Name**: `Prometheus`
   - **URL**: `http://192.7.111.66:9090`
   - **Access**: `Server (default)`
6. 点击 **Save & Test** 验证连接

## 📊 仪表板导入

### 方法1: Web界面导入（推荐）

1. **下载仪表板文件**
   ```bash
   # 从项目根目录获取仪表板文件
   cp hygon-dcu-dashboard-simple.json /tmp/
   ```

2. **导入步骤**
   - 登录Grafana
   - 点击左侧菜单 **"+"** > **Import**
   - 点击 **Upload JSON file**
   - 选择 `hygon-dcu-dashboard-simple.json`
   - 选择Prometheus数据源
   - 点击 **Import**

### 方法2: API自动导入

```bash
#!/bin/bash
# 自动导入仪表板脚本

GRAFANA_URL="http://192.7.111.66:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="your_password"
DASHBOARD_FILE="hygon-dcu-dashboard-simple.json"

# 准备导入数据
IMPORT_DATA=$(cat <<EOF
{
  "dashboard": $(cat $DASHBOARD_FILE),
  "overwrite": true,
  "inputs": [
    {
      "name": "DS_PROMETHEUS",
      "type": "datasource",
      "pluginId": "prometheus",
      "value": "Prometheus"
    }
  ]
}
EOF
)

# 执行导入
curl -X POST \
  "$GRAFANA_URL/api/dashboards/import" \
  -H "Content-Type: application/json" \
  -u "$GRAFANA_USER:$GRAFANA_PASS" \
  -d "$IMPORT_DATA"
```

### 方法3: Provisioning自动配置

创建provisioning配置文件：

```yaml
# /etc/grafana/provisioning/dashboards/hygon-dcu.yml
apiVersion: 1

providers:
  - name: 'hygon-dcu-dashboards'
    orgId: 1
    folder: 'DCU监控'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards/hygon-dcu
```

将仪表板文件放置到指定目录：
```bash
sudo mkdir -p /etc/grafana/provisioning/dashboards/hygon-dcu
sudo cp hygon-dcu-dashboard-simple.json /etc/grafana/provisioning/dashboards/hygon-dcu/
sudo systemctl restart grafana-server
```

## 📈 监控面板说明

### 主要监控面板

#### 1. 海光DCU使用率
- **指标**: `hygon_dcu_utilization_percent`
- **类型**: 时序图表
- **阈值**: >80% 红色告警
- **说明**: 显示各DCU设备的实时使用率趋势

#### 2. 海光DCU温度
- **指标**: `hygon_temperature_celsius`
- **类型**: 时序图表
- **阈值**: >70°C 黄色警告, >85°C 红色告警
- **说明**: 监控DCU设备温度变化，防止过热

#### 3. 海光DCU功耗
- **指标**: `hygon_power_watts`
- **类型**: 时序图表
- **阈值**: >200W 黄色警告, >300W 红色告警
- **说明**: 实时功耗监控，优化能耗管理

#### 4. 海光DCU显存使用率
- **指标**: `hygon_memory_utilization_percent`
- **类型**: 时序图表
- **阈值**: >80% 黄色警告, >95% 红色告警
- **说明**: 显存使用情况，避免内存不足

### 统计面板

#### 1. 设备数量统计
- **指标**: `count(hygon_dcu_utilization_percent)`
- **类型**: Stat面板
- **说明**: 显示当前在线的DCU设备总数

#### 2. 平均温度
- **指标**: `avg(hygon_temperature_celsius)`
- **类型**: Stat面板，带颜色编码
- **说明**: 所有DCU设备的平均温度

#### 3. 总功耗
- **指标**: `sum(hygon_power_watts)`
- **类型**: Stat面板，带颜色编码
- **说明**: 系统总功耗统计

#### 4. 平均使用率
- **指标**: `avg(hygon_dcu_utilization_percent)`
- **类型**: Stat面板，带颜色编码
- **说明**: 整体DCU使用率概览

## ⚙️ 自定义配置

### 修改刷新间隔

在仪表板设置中修改刷新间隔：

```json
{
  "refresh": "5s",  // 可选: 5s, 10s, 30s, 1m, 5m, 15m, 30m, 1h, 2h, 1d
  "time": {
    "from": "now-1h",
    "to": "now"
  }
}
```

### 添加新的监控指标

如果exporter新增了指标，可以添加新的面板：

```json
{
  "targets": [
    {
      "datasource": null,
      "expr": "hygon_fan_speed_rpm",  // 新指标
      "interval": "",
      "legendFormat": "DCU{{device_id}} 风扇转速",
      "refId": "A"
    }
  ],
  "title": "海光DCU风扇转速",
  "type": "timeseries"
}
```

### 调整面板布局

修改面板的位置和大小：

```json
{
  "gridPos": {
    "h": 8,    // 高度 (1-24)
    "w": 12,   // 宽度 (1-24)
    "x": 0,    // X轴位置 (0-23)
    "y": 0     // Y轴位置 (0-∞)
  }
}
```

### 自定义阈值颜色

修改告警阈值和颜色：

```json
{
  "thresholds": {
    "mode": "absolute",
    "steps": [
      {
        "color": "green",
        "value": null
      },
      {
        "color": "yellow",
        "value": 70    // 警告阈值
      },
      {
        "color": "red",
        "value": 85    // 告警阈值
      }
    ]
  }
}
```

## 🚨 告警配置

### 创建告警规则

1. **编辑面板** > **Alert** 标签页
2. **Create Alert** 创建新告警
3. 配置告警条件：

```
Query: avg(hygon_temperature_celsius) > 85
Condition: IS ABOVE 85
Evaluation: every 1m for 2m
```

### 告警通知渠道

配置通知渠道（邮件、钉钉、企业微信等）：

```json
{
  "name": "dcu-alerts",
  "type": "email",
  "settings": {
    "addresses": "admin@company.com;ops@company.com",
    "subject": "海光DCU告警: {{range .Alerts}}{{.Annotations.summary}}{{end}}"
  }
}
```

## 🔍 故障排除

### 常见问题

#### 1. 仪表板显示"No data"

**可能原因**:
- Prometheus未正确抓取数据
- Exporter服务未运行
- 网络连接问题

**解决方法**:
```bash
# 检查exporter状态
curl http://192.7.111.66:9400/metrics | grep hygon_

# 检查Prometheus targets
curl http://192.7.111.66:9090/api/v1/targets

# 验证Grafana数据源连接
curl -u admin:password http://192.7.111.66:3000/api/datasources
```

#### 2. 指标名称不匹配

**解决方法**:
检查实际的指标名称并更新仪表板配置：

```bash
# 查看所有可用指标
curl -s http://192.7.111.66:9400/metrics | grep "^hygon_" | cut -d' ' -f1 | sort | uniq
```

#### 3. 权限问题

**解决方法**:
确保Grafana用户有足够权限：
- 数据源访问权限
- 仪表板编辑权限
- 告警配置权限

### 调试技巧

#### 1. 使用Grafana Explore功能

在Grafana中使用Explore功能测试PromQL查询：
- 导航到 **Explore**
- 选择Prometheus数据源
- 输入查询语句测试

#### 2. 检查Prometheus查询

直接在Prometheus界面测试查询：
```
http://192.7.111.66:9090/graph
```

#### 3. 启用Grafana调试日志

```ini
# /etc/grafana/grafana.ini
[log]
level = debug
mode = console file
```

## 📝 最佳实践

1. **定期备份仪表板配置**
2. **设置合理的数据保留策略**
3. **监控Grafana和Prometheus服务状态**
4. **定期更新告警阈值**
5. **使用标签和注释组织面板**

---

更多详细信息请参考 [Grafana官方文档](https://grafana.com/docs/) 和 [Prometheus官方文档](https://prometheus.io/docs/)。
