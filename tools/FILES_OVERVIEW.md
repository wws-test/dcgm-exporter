# Tools 目录文件说明

## 📁 当前文件结构

```
tools/
├── 📄 README.md                      # 详细使用说明
├── 📄 DEPLOYMENT_SUMMARY.md          # 部署问题解决方案总结
├── 📄 FILES_OVERVIEW.md              # 本文件，文件结构说明
├── 📄 requirements.txt               # Python依赖包列表
│
├── 🚀 one_click_deploy.py            # 一键部署脚本（推荐新服务器）
├── 🔧 prepare_build_environment.py   # 构建环境准备脚本
├── 📦 remote_deploy.py               # 远程构建部署脚本
├── 🔍 diagnose_go_proxy.py           # Go代理问题诊断工具
├── 🧪 test_deploy.py                 # 部署测试验证脚本
│
├── 🐛 debug_exporter.sh              # 交互式调试工具（Linux）
└── 📊 start-monitoring.sh            # 监控栈启动脚本（Linux/macOS）
```

## 🎯 脚本用途

### 核心部署脚本
- **`one_click_deploy.py`** - 新服务器一键部署，自动处理环境配置
- **`prepare_build_environment.py`** - 单独的环境准备，解决Go版本和代理问题
- **`remote_deploy.py`** - 核心构建部署脚本，包含所有兼容性修复

### 辅助工具
- **`diagnose_go_proxy.py`** - 诊断Go代理和网络问题
- **`test_deploy.py`** - 验证部署结果和功能测试
- **`debug_exporter.sh`** - Linux服务器上的交互式调试工具
- **`start-monitoring.sh`** - 启动Prometheus+Grafana监控栈

### 文档文件
- **`README.md`** - 完整的使用说明和示例
- **`DEPLOYMENT_SUMMARY.md`** - 问题解决方案总结
- **`requirements.txt`** - Python依赖包列表

## 🚀 推荐使用流程

### 新服务器首次部署
```bash
python tools/one_click_deploy.py --host IP --username USER --password PASS
```

### 已配置环境的服务器
```bash
python tools/remote_deploy.py --host IP --username USER --password PASS
```

### 遇到问题时
```bash
python tools/diagnose_go_proxy.py --host IP --username USER --password PASS
```

## 🧹 清理说明

已删除的冗余文件：
- `test_go_version_fix.py` - 功能已集成到新脚本
- `remote_build_deploy.sh` - 被Python版本替代
- `deploy_to_servers.sh` - 功能重复
- `verify_deployment.sh` - 功能重复
- `PYTHON_DEPLOY_GUIDE.md` - 内容已整合到README
- `__pycache__/` - Python缓存目录

保留的文件都有明确的用途，没有功能重复。
