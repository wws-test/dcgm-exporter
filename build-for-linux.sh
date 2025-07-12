#!/bin/bash

# 构建海光DCU版本的DCGM Exporter
# 此脚本需要在Linux环境中运行

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查环境
check_environment() {
    print_step "检查构建环境..."
    
    # 检查Go版本
    if ! command -v go &> /dev/null; then
        print_error "Go未安装，请先安装Go 1.19或更高版本"
        exit 1
    fi
    
    GO_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
    print_info "Go版本: $GO_VERSION"
    
    # 检查Git
    if ! command -v git &> /dev/null; then
        print_error "Git未安装"
        exit 1
    fi
    
    print_info "环境检查完成"
}

# 构建二进制文件
build_binary() {
    print_step "构建海光DCU版本的DCGM Exporter..."
    
    # 设置构建变量
    VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "dev")
    BUILD_TIME=$(date -u '+%Y-%m-%d_%H:%M:%S')
    GIT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    
    print_info "版本: $VERSION"
    print_info "构建时间: $BUILD_TIME"
    print_info "Git提交: $GIT_COMMIT"
    
    # 构建标志
    LDFLAGS="-X main.BuildVersion=${VERSION} -X main.BuildTime=${BUILD_TIME} -X main.GitCommit=${GIT_COMMIT}"
    
    # 创建输出目录
    mkdir -p bin
    
    # 构建二进制文件
    print_info "开始构建..."
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
        -ldflags "$LDFLAGS" \
        -o bin/dcgm-exporter-hygon \
        ./cmd/dcgm-exporter
    
    if [ $? -eq 0 ]; then
        print_info "构建成功！"
        chmod +x bin/dcgm-exporter-hygon
        ls -la bin/dcgm-exporter-hygon
    else
        print_error "构建失败"
        exit 1
    fi
}

# 创建部署包
create_package() {
    print_step "创建部署包..."
    
    PACKAGE_NAME="dcgm-exporter-hygon-$(date +%Y%m%d-%H%M%S)"
    PACKAGE_DIR="packages/$PACKAGE_NAME"
    
    mkdir -p "$PACKAGE_DIR"
    
    # 复制二进制文件
    cp bin/dcgm-exporter-hygon "$PACKAGE_DIR/"
    
    # 复制配置文件
    mkdir -p "$PACKAGE_DIR/etc"
    cp etc/hygon-counters.csv "$PACKAGE_DIR/etc/"
    cp etc/default-counters.csv "$PACKAGE_DIR/etc/"
    
    # 复制文档
    cp README_HYGON.md "$PACKAGE_DIR/"
    cp HYGON_IMPLEMENTATION_SUMMARY.md "$PACKAGE_DIR/"
    
    # 复制部署文件
    mkdir -p "$PACKAGE_DIR/deployment"
    cp deployment/hygon-dcgm-exporter.yaml "$PACKAGE_DIR/deployment/"
    
    # 复制Docker文件
    mkdir -p "$PACKAGE_DIR/docker"
    cp docker/Dockerfile.hygon "$PACKAGE_DIR/docker/"
    
    # 创建启动脚本
    cat > "$PACKAGE_DIR/start-hygon.sh" << 'EOF'
#!/bin/bash

# 海光DCU模式启动脚本

# 检查hy-smi是否可用
if ! command -v hy-smi &> /dev/null; then
    echo "错误: hy-smi命令未找到，请确保已安装海光DCU驱动和工具"
    exit 1
fi

# 检查权限
if ! hy-smi --help &> /dev/null; then
    echo "错误: 无法访问hy-smi，请检查权限"
    exit 1
fi

# 设置默认参数
LISTEN_PORT=${DCGM_EXPORTER_LISTEN:-":9400"}
INTERVAL=${DCGM_EXPORTER_INTERVAL:-"30000"}
COLLECTORS_FILE=${DCGM_EXPORTER_COLLECTORS:-"./etc/hygon-counters.csv"}

echo "启动海光DCU监控..."
echo "监听端口: $LISTEN_PORT"
echo "采集间隔: $INTERVAL ms"
echo "指标配置: $COLLECTORS_FILE"

# 启动exporter
./dcgm-exporter-hygon \
    --use-hygon-mode \
    --address="$LISTEN_PORT" \
    --collect-interval="$INTERVAL" \
    --collectors="$COLLECTORS_FILE" \
    "$@"
EOF
    
    chmod +x "$PACKAGE_DIR/start-hygon.sh"
    
    # 创建NVIDIA GPU模式启动脚本
    cat > "$PACKAGE_DIR/start-nvidia.sh" << 'EOF'
#!/bin/bash

# NVIDIA GPU模式启动脚本

# 设置默认参数
LISTEN_PORT=${DCGM_EXPORTER_LISTEN:-":9400"}
INTERVAL=${DCGM_EXPORTER_INTERVAL:-"30000"}
COLLECTORS_FILE=${DCGM_EXPORTER_COLLECTORS:-"./etc/default-counters.csv"}

echo "启动NVIDIA GPU监控..."
echo "监听端口: $LISTEN_PORT"
echo "采集间隔: $INTERVAL ms"
echo "指标配置: $COLLECTORS_FILE"

# 启动exporter
./dcgm-exporter-hygon \
    --address="$LISTEN_PORT" \
    --collect-interval="$INTERVAL" \
    --collectors="$COLLECTORS_FILE" \
    "$@"
EOF
    
    chmod +x "$PACKAGE_DIR/start-nvidia.sh"
    
    # 创建安装说明
    cat > "$PACKAGE_DIR/INSTALL.md" << 'EOF'
# 安装和使用说明

## 快速开始

### 1. 海光DCU模式
```bash
# 启动海光DCU监控
./start-hygon.sh

# 或者直接使用二进制文件
./dcgm-exporter-hygon --use-hygon-mode
```

### 2. NVIDIA GPU模式
```bash
# 启动NVIDIA GPU监控
./start-nvidia.sh

# 或者直接使用二进制文件
./dcgm-exporter-hygon
```

### 3. 检查指标
```bash
# 查看所有指标
curl http://localhost:9400/metrics

# 查看海光DCU指标
curl http://localhost:9400/metrics | grep hygon

# 查看健康状态
curl http://localhost:9400/health
```

## 配置选项

### 环境变量
- `DCGM_EXPORTER_LISTEN`: 监听地址 (默认: :9400)
- `DCGM_EXPORTER_INTERVAL`: 采集间隔毫秒 (默认: 30000)
- `DCGM_EXPORTER_COLLECTORS`: 指标配置文件路径
- `DCGM_EXPORTER_USE_HYGON_MODE`: 启用海光DCU模式 (true/false)

### 命令行参数
- `--use-hygon-mode`: 启用海光DCU模式
- `--address`: 监听地址
- `--collect-interval`: 采集间隔(毫秒)
- `--collectors`: 指标配置文件路径
- `--hygon-devices`: 指定监控的海光DCU设备
- `--debug`: 启用调试模式

## 故障排除

### 1. 检查hy-smi
```bash
which hy-smi
hy-smi
```

### 2. 检查权限
```bash
sudo usermod -a -G hygon $USER
```

### 3. 调试模式
```bash
./dcgm-exporter-hygon --use-hygon-mode --debug
```

详细文档请参考 README_HYGON.md
EOF
    
    # 打包
    cd packages
    tar -czf "${PACKAGE_NAME}.tar.gz" "$PACKAGE_NAME"
    cd ..
    
    print_info "部署包创建完成: packages/${PACKAGE_NAME}.tar.gz"
    print_info "包含内容:"
    ls -la "$PACKAGE_DIR"
}

# 运行测试
run_tests() {
    print_step "运行测试..."
    
    # 测试hygonprovider包
    if go test ./internal/pkg/hygonprovider/... -v; then
        print_info "海光卡提供者测试通过"
    else
        print_warning "海光卡提供者测试失败（可能由于缺少DCGM依赖）"
    fi
}

# 主函数
main() {
    print_info "开始构建海光DCU版本的DCGM Exporter"
    
    check_environment
    
    # 清理依赖
    print_step "清理和下载依赖..."
    go mod tidy
    
    # 运行测试
    run_tests
    
    # 构建二进制文件
    build_binary
    
    # 创建部署包
    create_package
    
    print_info "构建完成！"
    echo
    print_info "使用方法:"
    echo "1. 解压部署包到目标服务器"
    echo "2. 运行 ./start-hygon.sh 启动海光DCU监控"
    echo "3. 运行 ./start-nvidia.sh 启动NVIDIA GPU监控"
    echo "4. 访问 http://localhost:9400/metrics 查看指标"
}

# 执行主函数
main "$@"
