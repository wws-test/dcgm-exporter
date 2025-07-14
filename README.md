# DCGM Exporter (海光DCU支持版)

[![Go](https://img.shields.io/badge/Go-1.21+-blue.svg)](https://golang.org)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

基于NVIDIA DCGM-Exporter改造的GPU/DCU监控解决方案，支持**NVIDIA GPU**和**海光DCU**双模式运行。

## ✨ 主要特性

- 🔥 **海光DCU支持**: 新增海光DCU监控功能
- 🟢 **NVIDIA GPU兼容**: 保持原有NVIDIA GPU监控功能
- 🔄 **双模式切换**: 通过命令行参数轻松切换监控模式
- 📊 **Prometheus兼容**: 标准Prometheus指标格式
- 🚀 **生产就绪**: 完整的部署和运维方案

## 🚀 快速开始

### 海光DCU模式
```bash
# 启动海光DCU监控
./dcgm-exporter --use-hygon-mode

# 查看指标
curl http://localhost:9400/metrics | grep hygon_temperature
```

### NVIDIA GPU模式
```bash
# 启动NVIDIA GPU监控（默认模式）
./dcgm-exporter

# 查看指标
curl http://localhost:9400/metrics | grep DCGM_FI
```

## 📊 支持的指标

### 海光DCU指标
- `hygon_temperature` - DCU温度
- `hygon_avg_power` - 平均功耗
- `hygon_dcu_usage` - DCU使用率
- `hygon_vram_usage` - 显存使用率
- `hygon_power_cap` - 功耗上限
- `hygon_performance_mode` - 性能模式
- `hygon_device_mode` - 设备状态

### NVIDIA GPU指标
- `DCGM_FI_DEV_GPU_UTIL` - GPU使用率
- `DCGM_FI_DEV_GPU_TEMP` - GPU温度
- `DCGM_FI_DEV_POWER_USAGE` - 功耗
- `DCGM_FI_DEV_FB_USED` - 显存使用量
- 更多DCGM标准指标...

## 📦 安装部署

### 方法1: 预编译包（推荐）
```bash
# 下载并安装
wget https://your-server/hygon-dcgm-exporter-release.tar.gz
tar -xzf hygon-dcgm-exporter-release.tar.gz
cd hygon-dcgm-exporter-*
sudo ./install.sh
```

### 方法2: 源码构建
```bash
# 在Linux环境构建
git clone https://github.com/your-repo/dcgm-exporter.git
cd dcgm-exporter
go build -o dcgm-exporter ./cmd/dcgm-exporter
```

### 方法3: 批量部署
```bash
# 部署到多台服务器
./tools/deploy_to_servers.sh user@server1 user@server2 user@server3

# 验证部署状态
./tools/verify_deployment.sh user@server1 user@server2 user@server3
```

## 🔧 配置选项

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `--use-hygon-mode` | 启用海光DCU模式 | false |
| `--address` | 监听地址 | :9400 |
| `--collectors` | 指标配置文件 | default-counters.csv |
| `--hygon-devices` | 监控的DCU设备 | f (全部) |
| `--hy-smi-path` | hy-smi命令路径 | hy-smi |

## 🌐 Prometheus配置

```yaml
scrape_configs:
  - job_name: 'hygon-dcu'
    static_configs:
      - targets: ['server1:9400', 'server2:9400']
    scrape_interval: 30s
```

## 📊 Grafana监控仪表板

### 快速导入仪表板

项目提供了预配置的Grafana仪表板，包含海光DCU的关键监控指标：

```bash
# 方法1: 通过Grafana Web界面导入
# 1. 登录Grafana -> 点击"+" -> Import
# 2. 上传 hygon-dcu-dashboard-simple.json 文件
# 3. 选择Prometheus数据源并导入

# 方法2: 使用API自动导入
curl -X POST \
  http://192.7.111.66:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -u admin:your_password \
  -d @hygon-dcu-dashboard-simple.json
```

### 仪表板功能特性

- 🔥 **实时监控**: 5秒刷新间隔，实时显示DCU状态
- 📈 **时序图表**: DCU使用率、温度、功耗、显存使用率趋势
- 📊 **统计面板**: 设备数量、平均温度、总功耗等关键指标
- 🚨 **阈值告警**: 预设温度、功耗、使用率告警阈值
- 🎨 **中文界面**: 完全中文化的监控面板

### 监控面板说明

| 面板名称 | 指标 | 阈值设置 | 说明 |
|---------|------|----------|------|
| 海光DCU使用率 | `hygon_dcu_utilization_percent` | >80%告警 | 显示各DCU设备使用率趋势 |
| 海光DCU温度 | `hygon_temperature_celsius` | >70°C警告, >85°C告警 | 监控DCU温度变化 |
| 海光DCU功耗 | `hygon_power_watts` | >200W警告, >300W告警 | 实时功耗监控 |
| 海光DCU显存使用率 | `hygon_memory_utilization_percent` | >80%警告, >95%告警 | 显存使用情况 |
| 设备统计 | `count(hygon_dcu_utilization_percent)` | - | 在线DCU设备数量 |
| 平均温度 | `avg(hygon_temperature_celsius)` | 颜色编码 | 所有DCU平均温度 |
| 总功耗 | `sum(hygon_power_watts)` | 颜色编码 | 系统总功耗统计 |
| 平均使用率 | `avg(hygon_dcu_utilization_percent)` | 颜色编码 | 整体使用率概览 |

### 自定义仪表板

如需自定义监控面板，可以：

1. **修改现有面板**: 编辑JSON配置文件中的查询语句和阈值
2. **添加新面板**: 参考现有面板结构添加新的监控指标
3. **调整布局**: 修改`gridPos`参数调整面板位置和大小

```json
{
  "gridPos": {
    "h": 8,    // 面板高度
    "w": 12,   // 面板宽度
    "x": 0,    // X轴位置
    "y": 0     // Y轴位置
  }
}
```

## 🔍 故障排除

### 常见问题
1. **hy-smi未找到**: 使用`--hy-smi-path`指定完整路径
2. **权限被拒绝**: 添加用户到hygon组或使用sudo
3. **端口被占用**: 使用`--address`指定其他端口

### 调试命令
```bash
# 启用调试模式
./dcgm-exporter --use-hygon-mode --debug

# 检查服务状态
systemctl status hygon-dcgm-exporter

# 查看日志
journalctl -u hygon-dcgm-exporter -f
```

## 📁 项目结构

```
dcgm-exporter/
├── 📚 docs/          # 📖 项目文档
├── 🛠️ tools/         # 🔧 运维工具脚本
├── 🏗️ build/         # 📦 构建相关文件
├── 💡 examples/      # 📋 配置示例
├── 💻 cmd/           # 🚀 主程序入口
├── 🔒 internal/      # 🏠 内部代码
├── ⚙️ etc/           # 📝 配置文件
├── ☸️ deployment/    # 🚀 K8s部署配置
└── 🐳 docker/        # 🐋 Docker配置
```

## 📚 文档

- **[📖 完整使用指南](docs/快速开始.md)** - 详细的安装、配置和故障排除指南
- **[📊 Grafana监控指南](docs/Grafana监控配置.md)** - Grafana仪表板配置和使用说明
- **[📁 项目结构](docs/项目结构.md)** - 项目目录结构说明
- **[🛠️ 工具脚本](tools/)** - 运维和部署工具
- **[💡 配置示例](examples/)** - 各种部署配置示例
- **[📈 监控仪表板](hygon-dcu-dashboard-simple.json)** - Grafana仪表板JSON配置文件

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建特性分支: `git checkout -b feature/your-feature`
3. 提交更改: `git commit -am 'Add some feature'`
4. 推送分支: `git push origin feature/your-feature`
5. 创建Pull Request

## 📄 许可证

本项目基于Apache 2.0许可证开源。详见[LICENSE](LICENSE)文件。

## 🙏 致谢

- [NVIDIA DCGM](https://github.com/NVIDIA/dcgm) - 原始DCGM项目
- [NVIDIA DCGM-Exporter](https://github.com/NVIDIA/dcgm-exporter) - 原始Exporter项目
- 海光信息技术股份有限公司 - DCU硬件支持

---

**🎉 让GPU/DCU监控变得简单！**
