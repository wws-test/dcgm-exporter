#!/bin/bash

# 海光DCU Exporter 调试脚本
# 功能：快速调试和测试exporter的各项指标

set -e

# 配置参数
EXPORTER_HOST="localhost"
EXPORTER_PORT="9400"
EXPORTER_URL="http://$EXPORTER_HOST:$EXPORTER_PORT"
HY_SMI_PATH="/usr/local/hyhal/bin/hy-smi"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
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

print_title() {
    echo -e "${PURPLE}=== $1 ===${NC}"
}

print_metric() {
    echo -e "${CYAN}$1${NC}"
}

# 显示菜单
show_menu() {
    clear
    echo -e "${PURPLE}"
    echo "🔧 海光DCU Exporter 调试工具"
    echo "=============================="
    echo -e "${NC}"
    echo "Exporter地址: $EXPORTER_URL"
    echo "hy-smi路径: $HY_SMI_PATH"
    echo ""
    echo "请选择调试选项："
    echo ""
    echo "📊 基础检查"
    echo "  1) 检查环境和依赖"
    echo "  2) 测试hy-smi工具"
    echo "  3) 检查exporter服务状态"
    echo ""
    echo "🔍 指标测试"
    echo "  4) 查看所有指标"
    echo "  5) 查看温度指标"
    echo "  6) 查看功耗指标"
    echo "  7) 查看使用率指标"
    echo "  8) 查看设备状态指标"
    echo ""
    echo "📈 实时监控"
    echo "  9) 实时监控温度变化"
    echo " 10) 实时监控使用率变化"
    echo " 11) 实时监控功耗变化"
    echo ""
    echo "🛠️ 高级功能"
    echo " 12) 对比hy-smi和exporter数据"
    echo " 13) 性能压力测试"
    echo " 14) 生成监控报告"
    echo " 15) 自定义查询"
    echo ""
    echo "⚙️ 配置管理"
    echo " 16) 修改exporter地址"
    echo " 17) 修改hy-smi路径"
    echo " 18) 重启exporter服务"
    echo ""
    echo "  0) 退出"
    echo ""
    echo -n "请输入选项 (0-18): "
}

# 检查环境和依赖
check_environment() {
    print_title "环境检查"

    # 检查curl
    if command -v curl &> /dev/null; then
        print_info "✅ curl 可用"
    else
        print_error "❌ curl 不可用，请安装curl"
        return 1
    fi

    # 检查hy-smi
    if [ -f "$HY_SMI_PATH" ]; then
        print_info "✅ hy-smi 找到: $HY_SMI_PATH"
        if $HY_SMI_PATH --help &> /dev/null; then
            print_info "✅ hy-smi 可执行"
        else
            print_warning "⚠️  hy-smi 无法执行，请检查权限"
        fi
    else
        print_error "❌ hy-smi 未找到: $HY_SMI_PATH"
        echo "常见位置："
        find /usr -name "hy-smi" 2>/dev/null || echo "  未找到hy-smi"
    fi

    # 检查网络连接
    if ping -c 1 $EXPORTER_HOST &> /dev/null; then
        print_info "✅ 网络连接正常"
    else
        print_warning "⚠️  网络连接异常"
    fi

    # 检查端口
    if netstat -tlnp 2>/dev/null | grep ":$EXPORTER_PORT " &> /dev/null; then
        print_info "✅ 端口 $EXPORTER_PORT 正在监听"
    else
        print_warning "⚠️  端口 $EXPORTER_PORT 未监听"
    fi

    echo ""
    read -p "按回车键继续..."
}

# 测试hy-smi工具
test_hy_smi() {
    print_title "hy-smi 工具测试"

    if [ ! -f "$HY_SMI_PATH" ]; then
        print_error "hy-smi 未找到: $HY_SMI_PATH"
        echo ""
        read -p "按回车键继续..."
        return 1
    fi

    print_step "执行 hy-smi 命令..."
    echo ""

    if $HY_SMI_PATH; then
        print_info "✅ hy-smi 执行成功"
    else
        print_error "❌ hy-smi 执行失败"
    fi

    echo ""
    read -p "按回车键继续..."
}

# 检查exporter服务状态
check_exporter_status() {
    print_title "Exporter 服务状态检查"

    # 健康检查
    print_step "健康检查..."
    if curl -s "$EXPORTER_URL/health" | grep -q "HEALTHY"; then
        print_info "✅ 服务健康状态: HEALTHY"
    else
        print_error "❌ 服务健康检查失败"
        echo "响应内容:"
        curl -s "$EXPORTER_URL/health" || echo "无法连接到服务"
    fi

    echo ""

    # 检查指标端点
    print_step "检查指标端点..."
    METRICS_COUNT=$(curl -s "$EXPORTER_URL/metrics" | grep "^hygon_" | wc -l)
    if [ "$METRICS_COUNT" -gt 0 ]; then
        print_info "✅ 指标端点正常，发现 $METRICS_COUNT 个海光DCU指标"
    else
        print_error "❌ 指标端点异常或无海光DCU指标"
    fi

    echo ""

    # 检查设备数量
    print_step "检查设备数量..."
    DEVICE_COUNT=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_exporter_device_count" | awk '{print $2}')
    if [ -n "$DEVICE_COUNT" ] && [ "$DEVICE_COUNT" -gt 0 ]; then
        print_info "✅ 检测到 $DEVICE_COUNT 个海光DCU设备"
    else
        print_warning "⚠️  未检测到海光DCU设备"
    fi

    echo ""
    read -p "按回车键继续..."
}

# 查看所有指标
view_all_metrics() {
    print_title "所有海光DCU指标"

    print_step "获取指标数据..."
    METRICS=$(curl -s "$EXPORTER_URL/metrics" | grep "^hygon_")

    if [ -z "$METRICS" ]; then
        print_error "❌ 未获取到海光DCU指标"
        echo ""
        read -p "按回车键继续..."
        return 1
    fi

    echo ""
    print_metric "$METRICS"

    echo ""
    METRIC_COUNT=$(echo "$METRICS" | wc -l)
    print_info "总计 $METRIC_COUNT 个指标"

    echo ""
    read -p "按回车键继续..."
}

# 查看温度指标
view_temperature_metrics() {
    print_title "温度指标"

    print_step "获取温度数据..."
    TEMP_METRICS=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_temperature")

    if [ -z "$TEMP_METRICS" ]; then
        print_error "❌ 未获取到温度指标"
    else
        echo ""
        print_metric "$TEMP_METRICS"

        echo ""
        # 统计温度信息
        MAX_TEMP=$(echo "$TEMP_METRICS" | awk '{print $2}' | sort -n | tail -1)
        MIN_TEMP=$(echo "$TEMP_METRICS" | awk '{print $2}' | sort -n | head -1)
        AVG_TEMP=$(echo "$TEMP_METRICS" | awk '{sum+=$2; count++} END {printf "%.1f", sum/count}')

        print_info "温度统计: 最高=${MAX_TEMP}°C, 最低=${MIN_TEMP}°C, 平均=${AVG_TEMP}°C"
    fi

    echo ""
    read -p "按回车键继续..."
}

# 查看功耗指标
view_power_metrics() {
    print_title "功耗指标"

    print_step "获取功耗数据..."
    POWER_METRICS=$(curl -s "$EXPORTER_URL/metrics" | grep -E "hygon_(avg_power|power_cap)")

    if [ -z "$POWER_METRICS" ]; then
        print_error "❌ 未获取到功耗指标"
    else
        echo ""
        print_metric "$POWER_METRICS"

        echo ""
        # 统计功耗信息
        AVG_POWER_TOTAL=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_avg_power" | awk '{sum+=$2} END {printf "%.1f", sum}')
        POWER_CAP_TOTAL=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_power_cap" | awk '{sum+=$2} END {printf "%.1f", sum}')

        print_info "功耗统计: 当前总功耗=${AVG_POWER_TOTAL}W, 总功耗上限=${POWER_CAP_TOTAL}W"
    fi

    echo ""
    read -p "按回车键继续..."
}

# 查看使用率指标
view_usage_metrics() {
    print_title "使用率指标"

    print_step "获取使用率数据..."
    USAGE_METRICS=$(curl -s "$EXPORTER_URL/metrics" | grep -E "hygon_(dcu_usage|vram_usage)")

    if [ -z "$USAGE_METRICS" ]; then
        print_error "❌ 未获取到使用率指标"
    else
        echo ""
        print_metric "$USAGE_METRICS"

        echo ""
        # 统计使用率信息
        DCU_USAGE_AVG=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_dcu_usage" | awk '{sum+=$2; count++} END {printf "%.1f", sum/count}')
        VRAM_USAGE_AVG=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_vram_usage" | awk '{sum+=$2; count++} END {printf "%.1f", sum/count}')

        print_info "使用率统计: DCU平均使用率=${DCU_USAGE_AVG}%, 显存平均使用率=${VRAM_USAGE_AVG}%"
    fi

    echo ""
    read -p "按回车键继续..."
}

# 查看设备状态指标
view_status_metrics() {
    print_title "设备状态指标"

    print_step "获取设备状态数据..."
    STATUS_METRICS=$(curl -s "$EXPORTER_URL/metrics" | grep -E "hygon_(performance_mode|device_mode)")

    if [ -z "$STATUS_METRICS" ]; then
        print_error "❌ 未获取到设备状态指标"
    else
        echo ""
        print_metric "$STATUS_METRICS"

        echo ""
        # 统计状态信息
        AUTO_MODE_COUNT=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_performance_mode" | awk '$2==1' | wc -l)
        NORMAL_MODE_COUNT=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_device_mode" | awk '$2==1' | wc -l)
        TOTAL_DEVICES=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_performance_mode" | wc -l)

        print_info "状态统计: ${AUTO_MODE_COUNT}/${TOTAL_DEVICES} 设备为自动性能模式, ${NORMAL_MODE_COUNT}/${TOTAL_DEVICES} 设备为正常运行模式"
    fi

    echo ""
    read -p "按回车键继续..."
}

# 实时监控温度变化
monitor_temperature() {
    print_title "实时温度监控"
    echo "按 Ctrl+C 停止监控"
    echo ""

    while true; do
        clear
        print_title "实时温度监控 - $(date '+%Y-%m-%d %H:%M:%S')"

        TEMP_DATA=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_temperature")
        if [ -n "$TEMP_DATA" ]; then
            echo "$TEMP_DATA" | while read line; do
                DEVICE=$(echo "$line" | grep -o 'device="[^"]*"' | cut -d'"' -f2)
                TEMP=$(echo "$line" | awk '{print $2}')
                printf "设备 %-2s: %5.1f°C\n" "$DEVICE" "$TEMP"
            done
        else
            print_error "无法获取温度数据"
        fi

        sleep 2
    done
}

# 实时监控使用率变化
monitor_usage() {
    print_title "实时使用率监控"
    echo "按 Ctrl+C 停止监控"
    echo ""

    while true; do
        clear
        print_title "实时使用率监控 - $(date '+%Y-%m-%d %H:%M:%S')"

        DCU_DATA=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_dcu_usage")
        VRAM_DATA=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_vram_usage")

        if [ -n "$DCU_DATA" ] && [ -n "$VRAM_DATA" ]; then
            echo "设备  DCU使用率  显存使用率"
            echo "----  --------  ----------"

            echo "$DCU_DATA" | while read dcu_line; do
                DEVICE=$(echo "$dcu_line" | grep -o 'device="[^"]*"' | cut -d'"' -f2)
                DCU_USAGE=$(echo "$dcu_line" | awk '{print $2}')
                VRAM_USAGE=$(echo "$VRAM_DATA" | grep "device=\"$DEVICE\"" | awk '{print $2}')

                printf "%-4s  %7.1f%%    %8.1f%%\n" "$DEVICE" "$DCU_USAGE" "$VRAM_USAGE"
            done
        else
            print_error "无法获取使用率数据"
        fi

        sleep 2
    done
}

# 实时监控功耗变化
monitor_power() {
    print_title "实时功耗监控"
    echo "按 Ctrl+C 停止监控"
    echo ""

    while true; do
        clear
        print_title "实时功耗监控 - $(date '+%Y-%m-%d %H:%M:%S')"

        POWER_DATA=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_avg_power")
        CAP_DATA=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_power_cap")

        if [ -n "$POWER_DATA" ] && [ -n "$CAP_DATA" ]; then
            echo "设备  当前功耗  功耗上限  使用率"
            echo "----  --------  --------  ------"

            echo "$POWER_DATA" | while read power_line; do
                DEVICE=$(echo "$power_line" | grep -o 'device="[^"]*"' | cut -d'"' -f2)
                CURRENT_POWER=$(echo "$power_line" | awk '{print $2}')
                POWER_CAP=$(echo "$CAP_DATA" | grep "device=\"$DEVICE\"" | awk '{print $2}')

                if [ -n "$POWER_CAP" ] && [ "$POWER_CAP" != "0" ]; then
                    POWER_USAGE=$(echo "scale=1; $CURRENT_POWER * 100 / $POWER_CAP" | bc)
                    printf "%-4s  %7.1fW   %7.1fW   %5.1f%%\n" "$DEVICE" "$CURRENT_POWER" "$POWER_CAP" "$POWER_USAGE"
                else
                    printf "%-4s  %7.1fW   %7s   %5s\n" "$DEVICE" "$CURRENT_POWER" "N/A" "N/A"
                fi
            done
        else
            print_error "无法获取功耗数据"
        fi

        sleep 2
    done
}

# 对比hy-smi和exporter数据
compare_data() {
    print_title "hy-smi vs Exporter 数据对比"

    if [ ! -f "$HY_SMI_PATH" ]; then
        print_error "hy-smi 未找到，无法进行对比"
        echo ""
        read -p "按回车键继续..."
        return 1
    fi

    print_step "获取 hy-smi 数据..."
    HY_SMI_OUTPUT=$($HY_SMI_PATH 2>/dev/null)

    print_step "获取 exporter 数据..."
    EXPORTER_DATA=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_")

    echo ""
    echo "=== hy-smi 原始输出 ==="
    echo "$HY_SMI_OUTPUT"

    echo ""
    echo "=== Exporter 指标输出 ==="
    echo "$EXPORTER_DATA" | head -20

    echo ""
    print_info "数据对比完成，请手动验证数值是否一致"

    echo ""
    read -p "按回车键继续..."
}

# 性能压力测试
performance_test() {
    print_title "性能压力测试"

    echo "测试参数："
    echo "- 并发请求数: 10"
    echo "- 测试时长: 30秒"
    echo "- 请求间隔: 1秒"
    echo ""

    read -p "确认开始压力测试? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        return 0
    fi

    print_step "开始压力测试..."

    START_TIME=$(date +%s)
    SUCCESS_COUNT=0
    ERROR_COUNT=0
    TOTAL_TIME=0

    for i in {1..30}; do
        echo -n "测试进度: $i/30 "

        # 并发请求
        for j in {1..10}; do
            REQUEST_START=$(date +%s.%3N)
            if curl -s "$EXPORTER_URL/metrics" > /dev/null 2>&1; then
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            else
                ERROR_COUNT=$((ERROR_COUNT + 1))
            fi
            REQUEST_END=$(date +%s.%3N)
            REQUEST_TIME=$(echo "$REQUEST_END - $REQUEST_START" | bc)
            TOTAL_TIME=$(echo "$TOTAL_TIME + $REQUEST_TIME" | bc)
        done

        echo "✓"
        sleep 1
    done

    END_TIME=$(date +%s)
    TOTAL_REQUESTS=$((SUCCESS_COUNT + ERROR_COUNT))
    AVG_RESPONSE_TIME=$(echo "scale=3; $TOTAL_TIME / $TOTAL_REQUESTS" | bc)
    QPS=$(echo "scale=2; $TOTAL_REQUESTS / ($END_TIME - $START_TIME)" | bc)

    echo ""
    print_title "压力测试结果"
    print_info "总请求数: $TOTAL_REQUESTS"
    print_info "成功请求: $SUCCESS_COUNT"
    print_info "失败请求: $ERROR_COUNT"
    print_info "成功率: $(echo "scale=2; $SUCCESS_COUNT * 100 / $TOTAL_REQUESTS" | bc)%"
    print_info "平均响应时间: ${AVG_RESPONSE_TIME}s"
    print_info "QPS: $QPS"

    echo ""
    read -p "按回车键继续..."
}

# 生成监控报告
generate_report() {
    print_title "生成监控报告"

    REPORT_FILE="hygon_exporter_report_$(date +%Y%m%d_%H%M%S).txt"

    print_step "生成报告: $REPORT_FILE"

    {
        echo "海光DCU Exporter 监控报告"
        echo "=========================="
        echo "生成时间: $(date)"
        echo "Exporter地址: $EXPORTER_URL"
        echo ""

        echo "=== 服务状态 ==="
        if curl -s "$EXPORTER_URL/health" | grep -q "HEALTHY"; then
            echo "健康状态: ✅ HEALTHY"
        else
            echo "健康状态: ❌ UNHEALTHY"
        fi

        DEVICE_COUNT=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_exporter_device_count" | awk '{print $2}')
        echo "设备数量: $DEVICE_COUNT"

        echo ""
        echo "=== 温度统计 ==="
        TEMP_DATA=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_temperature")
        if [ -n "$TEMP_DATA" ]; then
            MAX_TEMP=$(echo "$TEMP_DATA" | awk '{print $2}' | sort -n | tail -1)
            MIN_TEMP=$(echo "$TEMP_DATA" | awk '{print $2}' | sort -n | head -1)
            AVG_TEMP=$(echo "$TEMP_DATA" | awk '{sum+=$2; count++} END {printf "%.1f", sum/count}')
            echo "最高温度: ${MAX_TEMP}°C"
            echo "最低温度: ${MIN_TEMP}°C"
            echo "平均温度: ${AVG_TEMP}°C"
        fi

        echo ""
        echo "=== 功耗统计 ==="
        AVG_POWER_TOTAL=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_avg_power" | awk '{sum+=$2} END {printf "%.1f", sum}')
        POWER_CAP_TOTAL=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_power_cap" | awk '{sum+=$2} END {printf "%.1f", sum}')
        echo "当前总功耗: ${AVG_POWER_TOTAL}W"
        echo "总功耗上限: ${POWER_CAP_TOTAL}W"

        echo ""
        echo "=== 使用率统计 ==="
        DCU_USAGE_AVG=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_dcu_usage" | awk '{sum+=$2; count++} END {printf "%.1f", sum/count}')
        VRAM_USAGE_AVG=$(curl -s "$EXPORTER_URL/metrics" | grep "hygon_vram_usage" | awk '{sum+=$2; count++} END {printf "%.1f", sum/count}')
        echo "DCU平均使用率: ${DCU_USAGE_AVG}%"
        echo "显存平均使用率: ${VRAM_USAGE_AVG}%"

        echo ""
        echo "=== 详细指标数据 ==="
        curl -s "$EXPORTER_URL/metrics" | grep "hygon_"

    } > "$REPORT_FILE"

    print_info "报告已生成: $REPORT_FILE"

    echo ""
    read -p "是否查看报告内容? (y/N): " view_report
    if [[ $view_report =~ ^[Yy]$ ]]; then
        echo ""
        cat "$REPORT_FILE"
    fi

    echo ""
    read -p "按回车键继续..."
}

# 自定义查询
custom_query() {
    print_title "自定义查询"

    echo "请输入查询条件 (支持grep正则表达式):"
    echo "示例:"
    echo "  hygon_temperature     - 查询温度指标"
    echo "  device=\"0\"           - 查询设备0的所有指标"
    echo "  .*usage.*             - 查询所有使用率相关指标"
    echo ""

    read -p "查询条件: " query_pattern

    if [ -z "$query_pattern" ]; then
        print_warning "查询条件不能为空"
        echo ""
        read -p "按回车键继续..."
        return 0
    fi

    print_step "执行查询: $query_pattern"

    RESULT=$(curl -s "$EXPORTER_URL/metrics" | grep "$query_pattern")

    if [ -z "$RESULT" ]; then
        print_warning "未找到匹配的指标"
    else
        echo ""
        print_metric "$RESULT"
        echo ""
        RESULT_COUNT=$(echo "$RESULT" | wc -l)
        print_info "找到 $RESULT_COUNT 个匹配的指标"
    fi

    echo ""
    read -p "按回车键继续..."
}

# 修改exporter地址
modify_exporter_address() {
    print_title "修改Exporter地址"

    echo "当前地址: $EXPORTER_URL"
    echo ""

    read -p "请输入新的主机地址 (默认: $EXPORTER_HOST): " new_host
    read -p "请输入新的端口 (默认: $EXPORTER_PORT): " new_port

    if [ -n "$new_host" ]; then
        EXPORTER_HOST="$new_host"
    fi

    if [ -n "$new_port" ]; then
        EXPORTER_PORT="$new_port"
    fi

    EXPORTER_URL="http://$EXPORTER_HOST:$EXPORTER_PORT"

    print_info "新地址: $EXPORTER_URL"

    # 测试新地址
    print_step "测试新地址连接..."
    if curl -s "$EXPORTER_URL/health" &> /dev/null; then
        print_info "✅ 连接成功"
    else
        print_warning "⚠️  连接失败，请检查地址是否正确"
    fi

    echo ""
    read -p "按回车键继续..."
}

# 修改hy-smi路径
modify_hy_smi_path() {
    print_title "修改hy-smi路径"

    echo "当前路径: $HY_SMI_PATH"
    echo ""

    # 搜索可能的hy-smi位置
    print_step "搜索hy-smi可能的位置..."
    FOUND_PATHS=$(find /usr -name "hy-smi" 2>/dev/null)

    if [ -n "$FOUND_PATHS" ]; then
        echo "找到以下hy-smi:"
        echo "$FOUND_PATHS"
        echo ""
    fi

    read -p "请输入新的hy-smi路径: " new_path

    if [ -n "$new_path" ]; then
        if [ -f "$new_path" ]; then
            HY_SMI_PATH="$new_path"
            print_info "✅ 路径已更新: $HY_SMI_PATH"

            # 测试新路径
            print_step "测试hy-smi..."
            if $HY_SMI_PATH --help &> /dev/null; then
                print_info "✅ hy-smi 可执行"
            else
                print_warning "⚠️  hy-smi 无法执行，请检查权限"
            fi
        else
            print_error "❌ 文件不存在: $new_path"
        fi
    else
        print_warning "路径未更改"
    fi

    echo ""
    read -p "按回车键继续..."
}

# 重启exporter服务
restart_exporter() {
    print_title "重启Exporter服务"

    echo "尝试重启海光DCU Exporter服务..."
    echo ""

    # 尝试不同的服务名称
    SERVICE_NAMES=("hygon-dcgm-exporter" "dcgm-exporter" "hygon-exporter")

    for service in "${SERVICE_NAMES[@]}"; do
        if systemctl is-active "$service" &> /dev/null; then
            print_info "找到服务: $service"

            read -p "确认重启服务 $service? (y/N): " confirm
            if [[ $confirm =~ ^[Yy]$ ]]; then
                print_step "重启服务..."
                if sudo systemctl restart "$service"; then
                    print_info "✅ 服务重启成功"

                    # 等待服务启动
                    sleep 3

                    # 检查服务状态
                    if systemctl is-active "$service" &> /dev/null; then
                        print_info "✅ 服务运行正常"
                    else
                        print_error "❌ 服务启动失败"
                        echo "查看服务状态:"
                        systemctl status "$service" --no-pager
                    fi
                else
                    print_error "❌ 服务重启失败"
                fi
            fi

            echo ""
            read -p "按回车键继续..."
            return 0
        fi
    done

    print_warning "未找到运行中的exporter服务"
    echo "可以尝试手动启动:"
    echo "  sudo systemctl start hygon-dcgm-exporter"
    echo "  或直接运行二进制文件"

    echo ""
    read -p "按回车键继续..."
}

# 主程序
main() {
    # 检查依赖
    if ! command -v curl &> /dev/null; then
        print_error "curl 未安装，请先安装curl"
        exit 1
    fi

    if ! command -v bc &> /dev/null; then
        print_warning "bc 未安装，某些计算功能可能不可用"
    fi

    while true; do
        show_menu
        read choice

        case $choice in
            1) check_environment ;;
            2) test_hy_smi ;;
            3) check_exporter_status ;;
            4) view_all_metrics ;;
            5) view_temperature_metrics ;;
            6) view_power_metrics ;;
            7) view_usage_metrics ;;
            8) view_status_metrics ;;
            9) monitor_temperature ;;
            10) monitor_usage ;;
            11) monitor_power ;;
            12) compare_data ;;
            13) performance_test ;;
            14) generate_report ;;
            15) custom_query ;;
            16) modify_exporter_address ;;
            17) modify_hy_smi_path ;;
            18) restart_exporter ;;
            0)
                echo ""
                print_info "感谢使用海光DCU Exporter调试工具！"
                exit 0
                ;;
            *)
                print_error "无效选项，请重新选择"
                sleep 1
                ;;
        esac
    done
}

# 执行主程序
main "$@"