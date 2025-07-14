#!/bin/bash
# 海光DCU Grafana监控快速设置脚本

set -e

# 默认配置
GRAFANA_URL="http://192.7.111.66:3000"
PROMETHEUS_URL="http://192.7.111.66:9090"
GRAFANA_USER="admin"
GRAFANA_PASS="admin"
DASHBOARD_FILE="hygon-dcu-dashboard-simple.json"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 显示帮助信息
show_help() {
    cat << EOF
海光DCU Grafana监控设置脚本

用法: $0 [选项]

选项:
    -g, --grafana-url URL      Grafana服务器地址 (默认: $GRAFANA_URL)
    -p, --prometheus-url URL   Prometheus服务器地址 (默认: $PROMETHEUS_URL)
    -u, --username USER        Grafana用户名 (默认: $GRAFANA_USER)
    -P, --password PASS        Grafana密码 (默认: $GRAFANA_PASS)
    -d, --dashboard FILE       仪表板JSON文件 (默认: $DASHBOARD_FILE)
    -h, --help                 显示此帮助信息

示例:
    $0                                          # 使用默认配置
    $0 -g http://localhost:3000 -u admin -P mypass  # 自定义配置
    $0 --dashboard my-dashboard.json            # 使用自定义仪表板

EOF
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--grafana-url)
            GRAFANA_URL="$2"
            shift 2
            ;;
        -p|--prometheus-url)
            PROMETHEUS_URL="$2"
            shift 2
            ;;
        -u|--username)
            GRAFANA_USER="$2"
            shift 2
            ;;
        -P|--password)
            GRAFANA_PASS="$2"
            shift 2
            ;;
        -d|--dashboard)
            DASHBOARD_FILE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    if ! command -v curl &> /dev/null; then
        print_error "curl 未安装，请先安装 curl"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        print_warning "jq 未安装，某些功能可能受限"
    fi
    
    print_success "依赖检查完成"
}

# 测试Grafana连接
test_grafana_connection() {
    print_info "测试Grafana连接..."
    
    if curl -s -f -u "$GRAFANA_USER:$GRAFANA_PASS" "$GRAFANA_URL/api/health" > /dev/null; then
        print_success "Grafana连接成功"
        return 0
    else
        print_error "无法连接到Grafana: $GRAFANA_URL"
        print_error "请检查URL、用户名和密码是否正确"
        return 1
    fi
}

# 测试Prometheus连接
test_prometheus_connection() {
    print_info "测试Prometheus连接..."
    
    if curl -s -f "$PROMETHEUS_URL/api/v1/status/config" > /dev/null; then
        print_success "Prometheus连接成功"
        return 0
    else
        print_warning "无法连接到Prometheus: $PROMETHEUS_URL"
        print_warning "请确保Prometheus服务正在运行"
        return 1
    fi
}

# 创建Prometheus数据源
create_datasource() {
    print_info "创建Prometheus数据源..."
    
    # 检查数据源是否已存在
    if curl -s -f -u "$GRAFANA_USER:$GRAFANA_PASS" "$GRAFANA_URL/api/datasources/name/Prometheus" > /dev/null; then
        print_warning "Prometheus数据源已存在，跳过创建"
        return 0
    fi
    
    # 创建数据源配置
    DATASOURCE_CONFIG=$(cat <<EOF
{
  "name": "Prometheus",
  "type": "prometheus",
  "url": "$PROMETHEUS_URL",
  "access": "proxy",
  "isDefault": true,
  "basicAuth": false,
  "jsonData": {
    "httpMethod": "POST",
    "queryTimeout": "60s",
    "timeInterval": "15s"
  }
}
EOF
)
    
    # 创建数据源
    if curl -s -f -X POST \
        -H "Content-Type: application/json" \
        -u "$GRAFANA_USER:$GRAFANA_PASS" \
        -d "$DATASOURCE_CONFIG" \
        "$GRAFANA_URL/api/datasources" > /dev/null; then
        print_success "Prometheus数据源创建成功"
        return 0
    else
        print_error "创建Prometheus数据源失败"
        return 1
    fi
}

# 导入仪表板
import_dashboard() {
    print_info "导入监控仪表板..."
    
    if [[ ! -f "$DASHBOARD_FILE" ]]; then
        print_error "仪表板文件不存在: $DASHBOARD_FILE"
        return 1
    fi
    
    # 读取仪表板JSON
    DASHBOARD_JSON=$(cat "$DASHBOARD_FILE")
    
    # 准备导入数据
    IMPORT_DATA=$(cat <<EOF
{
  "dashboard": $DASHBOARD_JSON,
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
    
    # 导入仪表板
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -u "$GRAFANA_USER:$GRAFANA_PASS" \
        -d "$IMPORT_DATA" \
        "$GRAFANA_URL/api/dashboards/import")
    
    if echo "$RESPONSE" | grep -q '"status":"success"'; then
        print_success "仪表板导入成功"
        
        # 提取仪表板URL
        if command -v jq &> /dev/null; then
            DASHBOARD_UID=$(echo "$RESPONSE" | jq -r '.uid // empty')
            DASHBOARD_SLUG=$(echo "$RESPONSE" | jq -r '.slug // empty')
            if [[ -n "$DASHBOARD_UID" && -n "$DASHBOARD_SLUG" ]]; then
                print_success "仪表板地址: $GRAFANA_URL/d/$DASHBOARD_UID/$DASHBOARD_SLUG"
            fi
        fi
        return 0
    else
        print_error "导入仪表板失败"
        echo "$RESPONSE"
        return 1
    fi
}

# 验证设置
verify_setup() {
    print_info "验证监控设置..."
    
    # 检查exporter是否运行
    print_info "检查DCGM-Exporter状态..."
    EXPORTER_URLS=(
        "http://192.7.111.66:9400/metrics"
        "http://192.7.111.67:9400/metrics"
        "http://192.7.111.68:9400/metrics"
    )
    
    ACTIVE_EXPORTERS=0
    for url in "${EXPORTER_URLS[@]}"; do
        if curl -s -f "$url" | grep -q "hygon_"; then
            print_success "Exporter运行正常: $url"
            ((ACTIVE_EXPORTERS++))
        else
            print_warning "Exporter未响应: $url"
        fi
    done
    
    if [[ $ACTIVE_EXPORTERS -eq 0 ]]; then
        print_error "没有发现运行中的DCGM-Exporter"
        print_error "请确保使用 --use-hygon-mode 参数启动exporter"
    else
        print_success "发现 $ACTIVE_EXPORTERS 个运行中的Exporter"
    fi
}

# 主函数
main() {
    echo "🚀 开始设置海光DCU Grafana监控..."
    echo "📊 Grafana地址: $GRAFANA_URL"
    echo "📈 Prometheus地址: $PROMETHEUS_URL"
    echo "📄 仪表板文件: $DASHBOARD_FILE"
    echo ""
    
    # 检查依赖
    check_dependencies
    
    # 测试连接
    if ! test_grafana_connection; then
        exit 1
    fi
    
    test_prometheus_connection
    
    # 创建数据源
    if ! create_datasource; then
        exit 1
    fi
    
    # 导入仪表板
    if ! import_dashboard; then
        exit 1
    fi
    
    # 验证设置
    verify_setup
    
    echo ""
    print_success "🎉 海光DCU Grafana监控设置完成！"
    echo ""
    echo "📋 后续步骤:"
    echo "1. 访问Grafana仪表板: $GRAFANA_URL/dashboards"
    echo "2. 确保DCGM-Exporter正在运行 (--use-hygon-mode)"
    echo "3. 验证Prometheus正在抓取指标"
    echo "4. 检查仪表板是否显示数据"
    echo "5. 根据需要配置告警规则"
}

# 执行主函数
main "$@"
