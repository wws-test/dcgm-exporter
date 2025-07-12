#!/bin/bash

# GPU 监控系统启动脚本
# 作者: AI Assistant
# 用途: 快速部署 Prometheus + Grafana + DCGM Exporter 监控系统

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    # 检查 Docker 服务状态
    if ! docker info &> /dev/null; then
        log_error "Docker 服务未运行，请启动 Docker 服务"
        exit 1
    fi
    
    log_success "依赖检查通过"
}

# 检查 GPU 支持
check_gpu_support() {
    log_info "检查 GPU 支持..."
    
    # 检查 NVIDIA GPU
    if command -v nvidia-smi &> /dev/null; then
        log_success "检测到 NVIDIA GPU"
        nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
        return 0
    fi
    
    # 检查其他 GPU (海光卡等)
    if lspci | grep -i "vga\|3d\|display" | grep -i "hygon\|amd"; then
        log_warning "检测到非 NVIDIA GPU，需要自定义 exporter"
        log_warning "请参考 README_CN.md 中的海光卡适配指南"
    else
        log_warning "未检测到 GPU，将跳过 GPU 监控"
    fi
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p prometheus/rules
    mkdir -p grafana/provisioning/datasources
    mkdir -p grafana/provisioning/dashboards
    mkdir -p grafana/dashboards
    
    log_success "目录创建完成"
}

# 检查配置文件
check_config_files() {
    log_info "检查配置文件..."
    
    local missing_files=()
    
    # 检查必要的配置文件
    if [[ ! -f "docker-compose.yml" ]]; then
        missing_files+=("docker-compose.yml")
    fi
    
    if [[ ! -f "prometheus/prometheus.yml" ]]; then
        missing_files+=("prometheus/prometheus.yml")
    fi
    
    if [[ ! -f "grafana/provisioning/datasources/prometheus.yml" ]]; then
        missing_files+=("grafana/provisioning/datasources/prometheus.yml")
    fi
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        log_error "缺少以下配置文件:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        log_error "请确保所有配置文件都已创建"
        exit 1
    fi
    
    log_success "配置文件检查通过"
}

# 启动服务
start_services() {
    log_info "启动监控服务..."
    
    # 拉取最新镜像
    log_info "拉取 Docker 镜像..."
    docker-compose pull
    
    # 启动服务
    log_info "启动服务容器..."
    docker-compose up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    log_success "服务启动完成"
}

# 检查服务状态
check_services() {
    log_info "检查服务状态..."
    
    # 检查容器状态
    docker-compose ps
    
    # 检查服务健康状态
    local services=("prometheus:9090" "grafana:3000")
    
    for service in "${services[@]}"; do
        local name=$(echo $service | cut -d: -f1)
        local port=$(echo $service | cut -d: -f2)
        
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port" | grep -q "200\|302"; then
            log_success "$name 服务正常运行"
        else
            log_warning "$name 服务可能未完全启动，请稍后检查"
        fi
    done
}

# 显示访问信息
show_access_info() {
    log_success "监控系统部署完成！"
    echo
    echo "=========================================="
    echo "           服务访问信息"
    echo "=========================================="
    echo "🎯 Grafana 仪表板:"
    echo "   URL: http://localhost:3000"
    echo "   用户名: admin"
    echo "   密码: admin123"
    echo
    echo "📊 Prometheus 监控:"
    echo "   URL: http://localhost:9090"
    echo
    echo "🔧 DCGM Exporter 指标:"
    echo "   URL: http://localhost:9400/metrics"
    echo
    echo "💻 Node Exporter 指标:"
    echo "   URL: http://localhost:9100/metrics"
    echo
    echo "🐳 cAdvisor 容器监控:"
    echo "   URL: http://localhost:8080"
    echo "=========================================="
    echo
    log_info "使用 'docker-compose logs -f' 查看日志"
    log_info "使用 'docker-compose down' 停止服务"
    log_info "使用 'docker-compose restart' 重启服务"
}

# 主函数
main() {
    echo "=========================================="
    echo "      GPU 监控系统部署脚本"
    echo "=========================================="
    echo
    
    check_dependencies
    check_gpu_support
    create_directories
    check_config_files
    start_services
    check_services
    show_access_info
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
