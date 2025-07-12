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
./deploy_to_servers.sh user@server1 user@server2 user@server3
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

## 📚 文档

- **[📖 完整使用指南](快速开始.md)** - 详细的安装、配置和故障排除指南
- **[🚀 部署文档](deployment/)** - Kubernetes和Docker部署配置
- **[🔧 开发文档](internal/)** - 代码结构和开发指南

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
