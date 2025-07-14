#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海光DCU Exporter 远程构建部署脚本
功能：在远程服务器构建海光DCU Exporter，然后下载到本地
支持异步操作和实时进度显示
"""

import os
import sys
import time
import threading
import subprocess
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
import paramiko
from scp import SCPClient
import argparse

class Colors:
    """终端颜色定义"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

class ProgressIndicator:
    """进度指示器"""
    def __init__(self, message):
        self.message = message
        self.running = False
        self.thread = None
        
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        print()  # 换行
        
    def _animate(self):
        chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        while self.running:
            print(f"\r{Colors.CYAN}{chars[i % len(chars)]}{Colors.NC} {self.message}", end="", flush=True)
            time.sleep(0.1)
            i += 1

class Logger:
    """日志输出类"""
    @staticmethod
    def info(msg):
        print(f"{Colors.GREEN}[INFO]{Colors.NC} {msg}")
    
    @staticmethod
    def warning(msg):
        print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {msg}")
    
    @staticmethod
    def error(msg):
        print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")
    
    @staticmethod
    def step(msg):
        print(f"{Colors.BLUE}[STEP]{Colors.NC} {msg}")
    
    @staticmethod
    def success(msg):
        print(f"{Colors.GREEN}✅{Colors.NC} {msg}")

class RemoteDeployer:
    """远程部署器"""
    
    def __init__(self, host, username, password, remote_dir="/opt/hygon-dcgm-exporter-build"):
        self.host = host
        self.username = username
        self.password = password
        self.remote_dir = remote_dir
        self.local_download_dir = Path("./downloads")
        self.ssh_client = None
        
    def connect(self):
        """建立SSH连接"""
        progress = ProgressIndicator(f"连接到 {self.username}@{self.host}")
        progress.start()
        
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(
                hostname=self.host,
                username=self.username,
                password=self.password,
                timeout=10
            )
            progress.stop()
            Logger.success(f"SSH连接成功: {self.username}@{self.host}")
            return True
        except Exception as e:
            progress.stop()
            Logger.error(f"SSH连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开SSH连接"""
        if self.ssh_client:
            self.ssh_client.close()
    
    def prepare_source_package(self):
        """准备源码包"""
        Logger.step("准备源码包...")
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        temp_source = f"hygon-dcgm-exporter-source-{timestamp}.tar.gz"
        
        progress = ProgressIndicator("创建源码包")
        progress.start()
        
        try:
            # 创建tar包，排除不需要的文件
            with tarfile.open(temp_source, "w:gz") as tar:
                exclude_patterns = [
                    './downloads', './build/dcgm-exporter-hygon-source.zip',
                    './.git', './node_modules', './vendor', './__pycache__',
                    './tools/*.bat', './tools/*.ps1'
                ]
                
                include_dirs = ['cmd/', 'internal/', 'pkg/', 'etc/']
                include_files = ['go.mod', 'go.sum', 'Makefile', 'LICENSE']
                
                for item in include_dirs + include_files:
                    if os.path.exists(item):
                        tar.add(item)
            
            progress.stop()
            
            if os.path.exists(temp_source):
                size = os.path.getsize(temp_source) / 1024 / 1024
                Logger.success(f"源码包创建成功: {temp_source} ({size:.2f}MB)")
                return temp_source
            else:
                Logger.error("源码包创建失败")
                return None
                
        except Exception as e:
            progress.stop()
            Logger.error(f"创建源码包失败: {e}")
            return None
    
    def upload_source(self, source_file):
        """上传源码到远程服务器"""
        Logger.step("上传源码到远程服务器...")
        
        try:
            # 创建远程目录
            stdin, stdout, stderr = self.ssh_client.exec_command(f"mkdir -p {self.remote_dir} && rm -rf {self.remote_dir}/*")
            stdout.channel.recv_exit_status()
            
            # 上传文件
            progress = ProgressIndicator(f"上传 {source_file}")
            progress.start()
            
            with SCPClient(self.ssh_client.get_transport()) as scp:
                scp.put(source_file, f"{self.remote_dir}/{source_file}")
            
            progress.stop()
            Logger.success(f"文件上传成功: {source_file}")
            
            # 清理本地临时文件
            os.remove(source_file)
            return True

        except Exception as e:
            if 'progress' in locals():
                progress.stop()
            Logger.error(f"上传失败: {e}")
            return False

    def remote_build(self, source_file):
        """在远程服务器构建"""
        Logger.step("在远程服务器构建...")

        build_script = f'''
set -e
cd {self.remote_dir}
echo "当前目录: $(pwd)"

# 解压源码
echo "解压源码包..."
tar -xzf {source_file}
echo "解压完成"

# 检查并安装/升级Go环境
echo "检查Go环境..."
if ! command -v go &> /dev/null; then
    echo "未找到Go，开始安装..."
    apt update
    apt install -y wget
    INSTALL_GO=true
else
    GO_VERSION=$(go version | grep -oP 'go\K[0-9]+\.[0-9]+')
    echo "当前Go版本: $GO_VERSION"

    # 检查Go版本是否足够新（需要1.21+）
    if [[ $(echo "$GO_VERSION 1.21" | tr " " "\n" | sort -V | head -n1) != "1.21" ]]; then
        echo "Go版本过旧（需要1.21+），开始升级..."
        INSTALL_GO=true
    else
        echo "✅ Go版本满足要求"
        INSTALL_GO=false
    fi
fi

# 安装/升级Go
if [ "$INSTALL_GO" = true ]; then
    echo "下载并安装Go 1.21.13..."
    cd /tmp
    wget -q https://go.dev/dl/go1.21.13.linux-amd64.tar.gz
    if [ $? -ne 0 ]; then
        echo "❌ Go下载失败，尝试使用系统包管理器..."
        apt update
        apt install -y golang-go
    else
        rm -rf /usr/local/go
        tar -C /usr/local -xzf go1.21.13.linux-amd64.tar.gz
        export PATH=/usr/local/go/bin:$PATH
        echo "✅ Go 1.21.13 安装完成"
    fi
fi

# 确保Go在PATH中
export PATH=/usr/local/go/bin:$PATH
echo "最终Go版本: $(go version)"

# 配置Go代理（解决网络问题）
echo "配置Go代理..."
go env -w GOPROXY="https://goproxy.cn,direct"
go env -w GOSUMDB="sum.golang.google.cn"
go env -w GO111MODULE=on

# 测试Go代理连接
echo "测试Go代理连接..."
if curl -I --connect-timeout 10 https://goproxy.cn > /dev/null 2>&1; then
    echo "✅ goproxy.cn 可访问"
else
    echo "⚠️ goproxy.cn 不可访问，使用备用代理"
    go env -w GOPROXY="https://goproxy.io,https://proxy.golang.org,direct"
fi

GO_VERSION=$(go version | grep -oP 'go\K[0-9]+\.[0-9]+')
echo "检测到Go版本: $GO_VERSION"

if [ -f "go.mod" ]; then
    # 检查go.mod中的版本格式
    CURRENT_GO_VERSION=$(grep "^go " go.mod | awk '{{print $2}}')
    echo "go.mod中的Go版本: $CURRENT_GO_VERSION"

    # 自动修复go.mod版本以匹配当前Go版本
    if [[ "$CURRENT_GO_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "检测到三位版本号格式，转换为两位格式"
        FIXED_VERSION=$(echo "$CURRENT_GO_VERSION" | cut -d. -f1,2)
        sed -i "s/^go .*/go $FIXED_VERSION/" go.mod
        echo "已修复go.mod版本为: $FIXED_VERSION"
    elif [[ "$CURRENT_GO_VERSION" != "$GO_VERSION" ]]; then
        echo "更新go.mod版本以匹配当前Go版本"
        sed -i "s/^go .*/go $GO_VERSION/" go.mod
        echo "已更新go.mod版本为: $GO_VERSION"
    fi

    # 修复代码兼容性问题（针对NVIDIA库冲突）
    echo "修复代码兼容性问题..."

    # 修复os变量冲突
    if [ -f "internal/pkg/collector/variables.go" ]; then
        sed -i 's/var os osinterface.OS = osinterface.RealOS{{}}/var osInterface osinterface.OS = osinterface.RealOS{{}}/' internal/pkg/collector/variables.go
        find internal/pkg/collector -name "*.go" -exec sed -i 's/\\bos\\./osInterface\\./g' {{}} \\;
        sed -i '/^[[:space:]]*"os"$/d' internal/pkg/collector/collector_factory.go
        echo "✅ 修复os变量冲突"
    fi

    # 修复Metric结构体问题
    if [ -f "internal/pkg/collector/hygon_collector.go" ]; then
        sed -i 's/Name:   metricName,/Counter: counters.Counter{{PromType: "gauge", FieldName: metricName}},/' internal/pkg/collector/hygon_collector.go
        echo "✅ 修复Metric结构体"
    fi
fi

# 检查hy-smi
if [ -f "/usr/local/hyhal/bin/hy-smi" ]; then
    echo "✅ 找到hy-smi: /usr/local/hyhal/bin/hy-smi"
else
    echo "⚠️  未找到hy-smi，构建的程序可能无法正常工作"
fi

# 构建程序
echo "开始构建..."

# 确保使用正确的PATH
export PATH=/usr/local/go/bin:$PATH

# 显示当前Go配置
echo "当前Go配置:"
go env GOPROXY
go env GOSUMDB
go env GO111MODULE

# 清理模块缓存
echo "清理模块缓存..."
go clean -modcache

echo "开始下载依赖..."
if ! go mod download; then
    echo "❌ 依赖下载失败，尝试使用详细模式..."
    go mod download -x
    if [ $? -ne 0 ]; then
        echo "❌ 依赖下载仍然失败"
        exit 1
    fi
fi

echo "整理依赖..."
go mod tidy

echo "开始编译（使用hygon标签避免NVIDIA依赖冲突）..."
if ! CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -tags="hygon" -o hygon-dcgm-exporter ./cmd/dcgm-exporter; then
    echo "❌ 使用hygon标签构建失败，尝试标准构建..."
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -v -o hygon-dcgm-exporter ./cmd/dcgm-exporter
    if [ $? -ne 0 ]; then
        echo "❌ 标准构建也失败"
        exit 1
    fi
fi

if [ ! -f "hygon-dcgm-exporter" ]; then
    echo "❌ 构建失败"
    exit 1
fi

echo "✅ 构建成功"
ls -la hygon-dcgm-exporter

# 创建分发包
PACKAGE_NAME="hygon-dcgm-exporter-$(date +%Y%m%d-%H%M%S)"
echo "创建分发包: $PACKAGE_NAME"

mkdir -p "$PACKAGE_NAME"
cp hygon-dcgm-exporter "$PACKAGE_NAME/"
chmod +x "$PACKAGE_NAME/hygon-dcgm-exporter"

# 复制配置文件
mkdir -p "$PACKAGE_NAME/etc"
cp etc/hygon-counters.csv "$PACKAGE_NAME/etc/" 2>/dev/null || echo "# 海光DCU指标配置" > "$PACKAGE_NAME/etc/hygon-counters.csv"

# 创建启动脚本
cat > "$PACKAGE_NAME/start.sh" << 'SCRIPT_EOF'
#!/bin/bash
echo "🚀 启动海光DCU Prometheus Exporter"
echo "端口: 9400"
echo "指标端点: http://localhost:9400/metrics"
echo "健康检查: http://localhost:9400/health"
echo ""
echo "按 Ctrl+C 停止服务"
./hygon-dcgm-exporter --use-hygon-mode
SCRIPT_EOF

chmod +x "$PACKAGE_NAME/start.sh"

# 创建安装脚本
cat > "$PACKAGE_NAME/install.sh" << 'INSTALL_EOF'
#!/bin/bash
echo "📦 安装海光DCU Exporter"
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用root权限运行"
    exit 1
fi

INSTALL_DIR="/opt/hygon-dcgm-exporter"
mkdir -p "$INSTALL_DIR"
cp hygon-dcgm-exporter "$INSTALL_DIR/"
cp -r etc "$INSTALL_DIR/" 2>/dev/null || true
cp start.sh "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/hygon-dcgm-exporter"
chmod +x "$INSTALL_DIR/start.sh"

echo "✅ 安装完成！"
echo "启动命令: cd $INSTALL_DIR && ./start.sh"
INSTALL_EOF

chmod +x "$PACKAGE_NAME/install.sh"

# 创建README
cat > "$PACKAGE_NAME/README.md" << 'README_EOF'
# 海光DCU Prometheus Exporter

## 快速开始
```bash
# 直接运行
./start.sh

# 或安装为系统服务
sudo ./install.sh
```

## 验证
```bash
curl http://localhost:9400/health
curl http://localhost:9400/metrics | grep hygon_temperature
```
README_EOF

# 打包
tar -czf "$PACKAGE_NAME.tar.gz" "$PACKAGE_NAME"
echo "✅ 分发包创建完成: $PACKAGE_NAME.tar.gz"
ls -la "$PACKAGE_NAME.tar.gz"

echo "PACKAGE_NAME=$PACKAGE_NAME" > build_info.txt
'''

        progress = ProgressIndicator("远程构建中")
        progress.start()

        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(build_script)

            # 实时显示构建输出
            progress.stop()
            Logger.info("构建输出:")

            while True:
                line = stdout.readline()
                if not line:
                    break
                print(f"  {line.rstrip()}")

            exit_status = stdout.channel.recv_exit_status()

            if exit_status == 0:
                Logger.success("远程构建成功")
                return True
            else:
                error_output = stderr.read().decode()
                Logger.error(f"远程构建失败: {error_output}")
                return False

        except Exception as e:
            if 'progress' in locals():
                progress.stop()
            Logger.error(f"远程构建异常: {e}")
            return False

    def download_package(self):
        """下载构建产物"""
        Logger.step("下载构建产物...")

        try:
            # 获取包名
            stdin, stdout, stderr = self.ssh_client.exec_command(f"cd {self.remote_dir} && cat build_info.txt 2>/dev/null || echo 'PACKAGE_NAME=hygon-dcgm-exporter'")
            package_info = stdout.read().decode().strip()

            package_name = None
            for line in package_info.split('\n'):
                if line.startswith('PACKAGE_NAME='):
                    package_name = line.split('=', 1)[1]
                    break

            if not package_name:
                Logger.error("无法获取包名")
                return None

            # 创建本地下载目录
            self.local_download_dir.mkdir(exist_ok=True)

            remote_file = f"{self.remote_dir}/{package_name}.tar.gz"
            local_file = self.local_download_dir / f"{package_name}.tar.gz"

            Logger.info(f"下载包: {package_name}.tar.gz")

            # 下载文件
            progress = ProgressIndicator(f"下载 {package_name}.tar.gz")
            progress.start()

            with SCPClient(self.ssh_client.get_transport()) as scp:
                scp.get(remote_file, str(local_file))

            progress.stop()

            if local_file.exists():
                size = local_file.stat().st_size / 1024 / 1024
                Logger.success(f"下载成功: {local_file} ({size:.2f}MB)")
                return str(local_file)
            else:
                Logger.error("下载失败")
                return None

        except Exception as e:
            if 'progress' in locals():
                progress.stop()
            Logger.error(f"下载失败: {e}")
            return None

    def cleanup_remote(self):
        """清理远程临时文件"""
        Logger.step("清理远程临时文件...")

        progress = ProgressIndicator("清理远程文件")
        progress.start()

        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(f"rm -rf {self.remote_dir}")
            stdout.channel.recv_exit_status()
            progress.stop()
            Logger.success("远程清理完成")
        except Exception as e:
            progress.stop()
            Logger.warning(f"远程清理失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='海光DCU Exporter 远程构建部署脚本')
    parser.add_argument('--host', default='192.7.111.66', help='远程服务器地址')
    parser.add_argument('--user', default='root', help='远程服务器用户名')
    parser.add_argument('--password', default='123', help='远程服务器密码')
    parser.add_argument('--remote-dir', default='/opt/hygon-dcgm-exporter-build', help='远程构建目录')
    parser.add_argument('--no-confirm', action='store_true', help='跳过确认提示')

    args = parser.parse_args()

    print(f"{Colors.PURPLE}🚀 海光DCU Exporter 远程构建部署脚本{Colors.NC}")
    print("=" * 50)
    print(f"远程服务器: {args.user}@{args.host}")
    print(f"远程目录: {args.remote_dir}")
    print(f"本地下载目录: ./downloads")
    print()

    # 确认执行
    if not args.no_confirm:
        try:
            confirm = input("确认开始远程构建? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("取消执行")
                return 0
        except KeyboardInterrupt:
            print("\n取消执行")
            return 0

    # 创建部署器
    deployer = RemoteDeployer(args.host, args.user, args.password, args.remote_dir)

    try:
        # 执行部署流程
        if not deployer.connect():
            return 1

        source_file = deployer.prepare_source_package()
        if not source_file:
            return 1

        if not deployer.upload_source(source_file):
            return 1

        if not deployer.remote_build(os.path.basename(source_file)):
            return 1

        downloaded_file = deployer.download_package()
        if not downloaded_file:
            return 1

        deployer.cleanup_remote()

        print()
        Logger.success("🎉 远程构建完成！")
        print(f"下载的文件: {downloaded_file}")
        print()
        print("使用方法:")
        print(f"1. 解压: tar -xzf {downloaded_file}")
        print("2. 进入目录: cd hygon-dcgm-exporter-*")
        print("3. 安装: sudo ./install.sh")
        print("4. 启动: ./start.sh")

        return 0

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}用户中断操作{Colors.NC}")
        return 1
    except Exception as e:
        Logger.error(f"执行失败: {e}")
        return 1
    finally:
        deployer.disconnect()

if __name__ == "__main__":
    # 检查依赖
    try:
        import paramiko
        from scp import SCPClient
    except ImportError as e:
        print(f"{Colors.RED}[ERROR]{Colors.NC} 缺少依赖包: {e}")
        print("请安装依赖: pip install paramiko scp")
        sys.exit(1)

    sys.exit(main())
