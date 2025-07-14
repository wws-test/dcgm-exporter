# 💡 配置示例

本目录包含各种部署和配置示例。

## 📋 文件说明

| 文件 | 描述 | 用途 |
|------|------|------|
| `dcgm-exporter.yaml` | 基础K8s部署配置 | 单独部署exporter |
| `service-monitor.yaml` | ServiceMonitor配置 | Prometheus Operator监控 |
| `docker-compose.yml` | Docker Compose配置 | 完整监控栈部署 |

## 🚀 使用示例

### Kubernetes部署
```bash
# 部署exporter
kubectl apply -f examples/dcgm-exporter.yaml

# 配置ServiceMonitor（需要Prometheus Operator）
kubectl apply -f examples/service-monitor.yaml
```

### Docker Compose部署
```bash
# 启动完整监控栈
cd examples/
docker-compose up -d

# 查看服务状态
docker-compose ps

# 访问服务
# Grafana: http://localhost:3000 (admin/admin123)
# Prometheus: http://localhost:9090
# DCGM Exporter: http://localhost:9400/metrics
```

## 🔧 自定义配置

### 修改端口
编辑配置文件中的端口设置：
```yaml
# dcgm-exporter.yaml
spec:
  containers:
  - name: dcgm-exporter
    args:
    - --address=:9401  # 修改端口
```

### 启用海光DCU模式
```yaml
# dcgm-exporter.yaml
spec:
  containers:
  - name: dcgm-exporter
    args:
    - --use-hygon-mode  # 启用海光DCU模式
    env:
    - name: HYGON_HY_SMI_PATH
      value: "/usr/local/hyhal/bin/hy-smi"
```

### 配置资源限制
```yaml
# dcgm-exporter.yaml
spec:
  containers:
  - name: dcgm-exporter
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "200m"
```

## 📊 Prometheus配置示例

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'hygon-dcu'
    static_configs:
      - targets: ['server1:9400', 'server2:9400']
    scrape_interval: 30s
    metrics_path: /metrics
```

## 📈 Grafana仪表板

导入仪表板后，使用以下查询：
```promql
# DCU温度
hygon_temperature

# DCU使用率
hygon_dcu_usage

# 平均功耗
hygon_avg_power
```
