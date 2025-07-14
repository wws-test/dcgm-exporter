# 🛠️ 工具脚本说明

本目录包含项目的运维和部署工具脚本。

## 📋 脚本列表

| 脚本 | 功能 | 平台 | 特性 | 用法 |
|------|------|------|------|------|
| `one_click_deploy.py` | 一键部署(新服务器推荐) | 跨平台 | 环境准备+构建部署 | `python one_click_deploy.py` |
| `prepare_build_environment.py` | 构建环境准备 | 跨平台 | 自动配置Go环境 | `python prepare_build_environment.py` |
| `remote_deploy.py` | 远程构建部署 | 跨平台 | 异步进度显示 | `python remote_deploy.py` |
| `diagnose_go_proxy.py` | Go代理问题诊断 | 跨平台 | 网络问题排查 | `python diagnose_go_proxy.py` |
| `test_deploy.py` | 部署测试验证 | 跨平台 | 功能验证 | `python test_deploy.py` |
| `debug_exporter.sh` | 调试工具(交互式菜单) | Linux | 交互式调试 | `./debug_exporter.sh` |
| `start-monitoring.sh` | 启动监控栈 | Linux/macOS | 监控服务 | `./start-monitoring.sh` |

## 🚀 使用示例

### 🚀 快速部署（一键式）

#### ⚡ 一键部署（新服务器推荐）
```bash
# 完全自动化：环境准备 + 构建部署
python tools/one_click_deploy.py --host 192.168.1.100 --username root --password your_password

# 交互式一键部署
python tools/one_click_deploy.py

# 只准备环境（首次使用新服务器）
python tools/one_click_deploy.py --env-only --host 192.168.1.100 --username root --password your_password
```

#### 🔧 分步部署（高级用户）
```bash
# 第一步：准备构建环境（自动安装Go、配置代理、修复兼容性）
python tools/prepare_build_environment.py --host 192.168.1.100 --username root --password your_password

# 第二步：执行构建部署
python tools/remote_deploy.py --host 192.168.1.100 --username root --password your_password
```

### Python远程构建（高级用户）

#### 🎯 最佳方案：Python版本（跨平台，异步进度显示）
```bash
# 1. 安装Python依赖
pip install -r tools/requirements.txt

# 2. 运行远程构建（带进度显示）
python tools/remote_deploy.py

# 3. 自定义参数
python tools/remote_deploy.py --host 192.168.1.100 --user admin --password mypass

# 4. 跳过确认提示
python tools/remote_deploy.py --no-confirm
```

#### 📋 环境诊断
```bash
# 诊断构建环境问题
python tools/diagnose_go_proxy.py --host 192.168.1.100 --username root --password your_password
```

### 测试部署
```bash
# 测试部署结果
python tools/test_deploy.py --host 192.168.1.100 --username root --password your_password
```

### 启动监控
```bash
# 启动完整的监控栈（Prometheus + Grafana + Exporters）
./start-monitoring.sh
```

### 调试工具
```bash
# 在Linux服务器上直接运行调试工具
./debug_exporter.sh
```

## 📝 注意事项

### Python远程构建
1. **Python环境**: 需要Python 3.6+
2. **依赖安装**: `pip install -r tools/requirements.txt`
3. **网络连接**: 确保可以SSH连接到Linux服务器
4. **特性优势**:
   - 跨平台支持（Windows/Linux/macOS）
   - 异步操作和实时进度显示
   - 更好的错误处理和用户体验
   - 命令行参数支持

### Shell脚本部署
1. **权限要求**: 部署脚本需要目标服务器的sudo权限
2. **网络要求**: 确保可以SSH连接到目标服务器
3. **依赖检查**: 脚本会自动检查必要的依赖项

## 🔧 自定义配置

### Python脚本参数
```bash
# 查看所有可用参数
python tools/remote_deploy.py --help

# 常用参数示例
python tools/remote_deploy.py \
  --host 192.168.1.100 \
  --user admin \
  --password mypassword \
  --remote-dir /tmp/build \
  --no-confirm
```

### 环境变量配置
```bash
# 设置自定义端口
export HYGON_EXPORTER_PORT=9401

# 设置自定义hy-smi路径
export HYGON_HY_SMI_PATH=/usr/local/bin/hy-smi

# 然后运行部署脚本
./deploy_to_servers.sh user@server1
```

## 🎯 远程构建流程

1. **准备源码**: 在Windows本地打包源码
2. **上传到服务器**: 通过SSH上传到Linux服务器
3. **远程构建**: 在Linux服务器上编译Go程序
4. **创建分发包**: 生成包含二进制文件和脚本的tar.gz包
5. **下载到本地**: 将构建好的包下载到Windows本地
6. **清理临时文件**: 自动清理服务器上的临时文件

## 🔍 故障排除

### SSH连接问题
- 检查服务器IP、用户名、密码是否正确
- 确保服务器SSH服务正常运行
- 检查防火墙设置

### 构建失败
- 检查服务器Go环境是否正常
- 查看构建日志中的错误信息
- 确保源码完整性

### 下载失败
- 检查本地网络连接
- 确保有足够的磁盘空间
- 检查文件权限

## 🔧 调试工具功能

### 交互式菜单选项
1. **📊 基础检查**
   - 检查环境和依赖（curl、hy-smi等）
   - 测试hy-smi工具
   - 检查exporter服务状态

2. **🔍 指标测试**
   - 查看所有指标
   - 分类查看（温度、功耗、使用率、状态）
   - 统计分析

3. **📈 实时监控**
   - 实时温度监控
   - 实时使用率监控
   - 实时功耗监控

4. **🛠️ 高级功能**
   - 对比hy-smi和exporter数据
   - 性能压力测试
   - 生成监控报告
   - 自定义查询

5. **⚙️ 配置管理**
   - 修改exporter地址
   - 修改hy-smi路径
   - 重启exporter服务

### 使用场景
- **开发调试**: 验证指标数据正确性
- **性能测试**: 测试exporter响应性能
- **故障排除**: 快速定位问题
- **监控验证**: 确认监控系统正常工作
