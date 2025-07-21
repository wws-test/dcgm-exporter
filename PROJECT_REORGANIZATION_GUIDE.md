# 项目结构重组指南

## 📋 重组概述

本文档说明了DCGM-Exporter项目的结构重组方案，旨在解决项目文件分散、脚本过时、结构混乱的问题。

## 🎯 重组目标

1. **清晰的目录结构** - 按功能分类组织文件
2. **精简的脚本集合** - 保留核心脚本，删除过时文件
3. **统一的部署方案** - 集中管理部署相关文件
4. **完善的文档体系** - 提供清晰的使用指南

## 📁 新的项目结构

```
dcgm-exporter/
├── 📦 build/                      # 构建相关文件
│   ├── build-hygon.sh             # 海光DCU构建脚本
│   ├── Makefile                   # Make构建配置
│   └── docker/                    # Docker构建文件
│       ├── Dockerfile.hygon       # 海光DCU Docker文件
│       ├── Dockerfile.ubuntu      # Ubuntu Docker文件
│       └── dcgm-exporter-entrypoint.sh
│
├── 🚀 deploy/                     # 部署相关（新增）
│   ├── scripts/                   # 核心部署脚本
│   │   ├── one_click_deploy.py    # 一键部署脚本
│   │   ├── remote_deploy.py       # 远程部署脚本
│   │   ├── setup_grafana_monitoring.py  # Grafana设置（Python）
│   │   ├── setup_grafana_monitoring.sh  # Grafana设置（Shell）
│   │   └── README.md              # 脚本使用说明
│   ├── configs/                   # 部署配置文件
│   ├── monitoring/                # 监控系统配置
│   │   ├── prometheus/            # Prometheus配置
│   │   │   ├── prometheus.yml     # 主配置文件
│   │   │   └── rules/             # 告警规则
│   │   └── grafana/               # Grafana配置
│   │       ├── dashboards/        # 仪表板配置
│   │       │   └── hygon-dcu-dashboard.json
│   │       └── provisioning/      # 自动配置
│   └── k8s/                       # Kubernetes部署配置
│       ├── Chart.yaml
│       ├── hygon-dcgm-exporter.yaml
│       └── templates/
│
├── 💻 src/                        # 源代码（重新组织）
│   ├── cmd/                       # 主程序入口
│   │   └── dcgm-exporter/
│   ├── internal/                  # 内部代码
│   │   ├── mocks/
│   │   └── pkg/
│   ├── pkg/                       # 公共包
│   │   └── cmd/
│   └── hygon-sysfs-exporter/      # 海光sysfs exporter
│       ├── main.go
│       ├── Makefile
│       └── README.md
│
├── ⚙️ configs/                    # 配置文件
│   ├── default-counters.csv       # 默认计数器
│   ├── hygon-counters.csv         # 海光计数器
│   ├── dcp-metrics-included.csv   # DCP指标
│   └── 1.x-compatibility-metrics.csv
│
├── 💡 examples/                   # 示例配置
│   ├── dcgm-exporter.yaml         # K8s部署示例
│   ├── docker-compose.yml         # Docker Compose示例
│   ├── service-monitor.yaml       # ServiceMonitor示例
│   └── README.md
│
├── 🧪 tests/                      # 测试文件
│   ├── e2e/                       # 端到端测试
│   ├── integration/               # 集成测试
│   └── gpu-pod.yaml
│
├── 📚 docs/                       # 文档
│   ├── 快速开始.md                 # 快速开始指南
│   ├── Grafana监控配置.md          # Grafana配置指南
│   ├── 项目结构.md                 # 项目结构说明
│   └── security.md               # 安全相关文档
│
├── 📄 根目录文件
│   ├── README.md                  # 主README（已更新）
│   ├── LICENSE                    # 许可证
│   ├── go.mod                     # Go模块文件
│   ├── go.sum                     # Go依赖校验
│   └── PROJECT_REORGANIZATION_GUIDE.md  # 本文档
```

## 🔄 文件迁移映射

### 核心脚本迁移

| 原位置 | 新位置 | 说明 |
|--------|--------|------|
| `tools/one_click_deploy.py` | `deploy/scripts/one_click_deploy.py` | 一键部署脚本 |
| `tools/remote_deploy.py` | `deploy/scripts/remote_deploy.py` | 远程部署脚本 |
| `tools/setup_grafana_monitoring.py` | `deploy/scripts/setup_grafana_monitoring.py` | Grafana设置脚本 |
| `tools/setup_grafana_monitoring.sh` | `deploy/scripts/setup_grafana_monitoring.sh` | Grafana设置脚本（Shell版） |
| `tools/start-monitoring.sh` | `deploy/scripts/start-monitoring.sh` | 监控启动脚本 |

### 配置文件迁移

| 原位置 | 新位置 | 说明 |
|--------|--------|------|
| `etc/` | `configs/` | 配置文件目录 |
| `prometheus/` | `deploy/monitoring/prometheus/` | Prometheus配置 |
| `grafana/` | `deploy/monitoring/grafana/` | Grafana配置 |
| `deployment/` | `deploy/k8s/` | Kubernetes部署配置 |
| `hygon-dcu-dashboard-simple.json` | `deploy/monitoring/grafana/dashboards/hygon-dcu-dashboard.json` | Grafana仪表板 |

### 源代码迁移

| 原位置 | 新位置 | 说明 |
|--------|--------|------|
| `cmd/` | `src/cmd/` | 主程序入口 |
| `internal/` | `src/internal/` | 内部代码 |
| `pkg/` | `src/pkg/` | 公共包 |
| `hygon-sysfs-exporter/` | `src/hygon-sysfs-exporter/` | 海光sysfs exporter |

### 构建文件迁移

| 原位置 | 新位置 | 说明 |
|--------|--------|------|
| `scripts/build-hygon.sh` | `build/build-hygon.sh` | 构建脚本 |
| `Makefile` | `build/Makefile` | Make配置 |
| `docker/` | `build/docker/` | Docker文件 |

## 🗑️ 删除的过时文件

### 压缩包文件
- `go1.21.13.linux-amd64.tar.gz`
- `grafana-11.4.0.linux-amd64.tar.gz`
- `node_exporter-1.8.2.linux-amd64.tar.gz`
- `prometheus-2.55.1.linux-amd64.tar.gz`
- `build/dcgm-exporter-hygon-source.zip`

### 过时的工具脚本
- `tools/DEPLOYMENT_SUMMARY.md`
- `tools/FILES_OVERVIEW.md`
- `tools/debug_exporter.sh`
- `tools/diagnose_go_proxy.py`
- `tools/prepare_build_environment.py`
- `tools/requirements.txt`
- `tools/test_deploy.py`

### 过时的配置和文档
- `hygon-sysfs-research.md`
- `staticcheck.conf`
- `hack/` 目录
- `packaging/` 目录

## 🚀 核心脚本说明

### 1. 一键部署脚本
**位置**: `deploy/scripts/one_click_deploy.py`

**功能**:
- 自动构建DCGM-Exporter
- 部署Prometheus配置
- 部署Grafana仪表板
- 远程部署Exporter到多台服务器
- 验证部署结果

**使用方法**:
```bash
cd deploy/scripts
python one_click_deploy.py --servers 192.7.111.66,192.7.111.67,192.7.111.68
```

### 2. 远程部署脚本
**位置**: `deploy/scripts/remote_deploy.py`

**功能**:
- SSH远程部署DCGM-Exporter
- 支持海光DCU和NVIDIA GPU模式
- 自动处理依赖和服务配置
- 批量部署到多台服务器

**使用方法**:
```bash
cd deploy/scripts
python remote_deploy.py --servers server1,server2,server3 --mode hygon
```

### 3. Grafana监控设置脚本
**位置**: `deploy/scripts/setup_grafana_monitoring.py` (Python版)
**位置**: `deploy/scripts/setup_grafana_monitoring.sh` (Shell版)

**功能**:
- 自动创建Prometheus数据源
- 导入海光DCU监控仪表板
- 配置告警规则
- 验证监控设置

**使用方法**:
```bash
cd deploy/scripts
# Python版本
python setup_grafana_monitoring.py --grafana-url http://192.7.111.66:3000

# Shell版本
./setup_grafana_monitoring.sh -g http://192.7.111.66:3000
```

### 4. 构建脚本
**位置**: `build/build-hygon.sh`

**功能**:
- 构建海光DCU版本的DCGM-Exporter
- 处理Go依赖
- 生成可执行文件

**使用方法**:
```bash
cd build
./build-hygon.sh
```

## 📊 监控配置

### Prometheus配置
**位置**: `deploy/monitoring/prometheus/prometheus.yml`

包含海光DCU Exporter的抓取配置，支持多服务器监控。

### Grafana仪表板
**位置**: `deploy/monitoring/grafana/dashboards/hygon-dcu-dashboard.json`

预配置的海光DCU监控仪表板，包含：
- DCU使用率监控
- 温度监控
- 功耗监控
- 显存使用率监控
- 统计面板

## 🔧 使用流程

### 完整部署流程
```bash
# 1. 克隆项目
git clone <repository-url>
cd dcgm-exporter

# 2. 一键部署（推荐）
cd deploy/scripts
python one_click_deploy.py --servers 192.7.111.66,192.7.111.67,192.7.111.68

# 3. 验证部署
curl http://192.7.111.66:9400/metrics | grep hygon_
curl http://192.7.111.66:9090/api/v1/targets
curl http://192.7.111.66:3000/api/health
```

### 分步部署流程
```bash
# 1. 构建项目
cd build
./build-hygon.sh

# 2. 远程部署
cd ../deploy/scripts
python remote_deploy.py --servers server1,server2,server3

# 3. 设置监控
./setup_grafana_monitoring.sh

# 4. 验证结果
curl http://server1:9400/metrics | grep hygon_
```

## 📝 重组执行步骤

如果您需要手动执行重组，可以按以下步骤操作：

### 1. 备份当前项目
```bash
cp -r dcgm-exporter dcgm-exporter-backup
```

### 2. 创建新目录结构
```bash
mkdir -p deploy/{scripts,configs,monitoring/{prometheus,grafana/dashboards},k8s}
mkdir -p src/{cmd,internal,pkg}
mkdir -p configs examples tests
```

### 3. 移动核心文件
```bash
# 移动部署脚本
cp tools/one_click_deploy.py deploy/scripts/
cp tools/remote_deploy.py deploy/scripts/
cp tools/setup_grafana_monitoring.* deploy/scripts/

# 移动配置文件
cp -r etc/* configs/
cp -r prometheus/* deploy/monitoring/prometheus/
cp -r grafana/* deploy/monitoring/grafana/
cp hygon-dcu-dashboard-simple.json deploy/monitoring/grafana/dashboards/hygon-dcu-dashboard.json

# 移动源代码
cp -r cmd/* src/cmd/
cp -r internal/* src/internal/
cp -r pkg/* src/pkg/

# 移动构建文件
cp scripts/build-hygon.sh build/
cp Makefile build/
```

### 4. 删除过时文件
```bash
# 删除压缩包
rm -f *.tar.gz *.zip

# 删除过时目录
rm -rf hack/ packaging/

# 删除过时脚本
rm -f tools/debug_exporter.sh tools/diagnose_go_proxy.py
```

### 5. 更新README
```bash
cp README_NEW.md README.md
```

## 🎉 重组完成后的优势

1. **清晰的结构** - 每个目录都有明确的用途
2. **简化的部署** - 核心脚本集中在`deploy/scripts/`
3. **完整的监控** - 监控配置统一管理
4. **易于维护** - 删除了过时和重复的文件
5. **标准化流程** - 提供了标准的部署和使用流程

## 📞 支持

如果在重组过程中遇到问题，请：

1. 查看备份文件
2. 检查`PROJECT_CLEANUP_REPORT.json`报告
3. 参考本文档的详细说明
4. 提交Issue寻求帮助

---

**🎯 重组目标：让项目结构更清晰，使用更简单！**
