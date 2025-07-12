#!/bin/bash

# 验证海光DCU Exporter部署状态
# 用法: ./verify_deployment.sh server1 server2 server3

if [ $# -eq 0 ]; then
    echo "用法: $0 server1 [server2] [server3] ..."
    echo "示例: $0 user@192.168.1.10 user@192.168.1.11"
    exit 1
fi

SERVERS=("$@")
TOTAL_SERVERS=${#SERVERS[@]}

echo "🔍 验证海光DCU Exporter部署状态"
echo "================================"
echo "服务器数量: $TOTAL_SERVERS"
echo ""

HEALTHY_COUNT=0
UNHEALTHY_SERVERS=()

for i in "${!SERVERS[@]}"; do
    SERVER="${SERVERS[$i]}"
    CURRENT=$((i + 1))
    
    echo "[$CURRENT/$TOTAL_SERVERS] 检查服务器: $SERVER"
    echo "----------------------------------------"
    
    # 检查服务状态
    echo -n "服务状态: "
    if ssh "$SERVER" 'systemctl is-active hygon-dcgm-exporter' 2>/dev/null | grep -q "active"; then
        echo "✅ 运行中"
    else
        echo "❌ 未运行"
        UNHEALTHY_SERVERS+=("$SERVER")
        continue
    fi
    
    # 检查健康状态
    echo -n "健康检查: "
    if ssh "$SERVER" 'curl -s http://localhost:9400/health 2>/dev/null' | grep -q "HEALTHY"; then
        echo "✅ 健康"
    else
        echo "❌ 不健康"
        UNHEALTHY_SERVERS+=("$SERVER")
        continue
    fi
    
    # 检查指标数量
    echo -n "指标数量: "
    METRIC_COUNT=$(ssh "$SERVER" 'curl -s http://localhost:9400/metrics 2>/dev/null | grep "^hygon_" | wc -l')
    if [ "$METRIC_COUNT" -gt 0 ]; then
        echo "✅ $METRIC_COUNT 个指标"
    else
        echo "❌ 无指标"
        UNHEALTHY_SERVERS+=("$SERVER")
        continue
    fi
    
    # 检查设备数量
    echo -n "设备数量: "
    DEVICE_COUNT=$(ssh "$SERVER" 'curl -s http://localhost:9400/metrics 2>/dev/null | grep "hygon_exporter_device_count" | awk "{print \$2}"')
    if [ -n "$DEVICE_COUNT" ] && [ "$DEVICE_COUNT" -gt 0 ]; then
        echo "✅ $DEVICE_COUNT 个设备"
        HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
    else
        echo "❌ 无设备"
        UNHEALTHY_SERVERS+=("$SERVER")
    fi
    
    echo ""
done

echo "🎉 验证完成！"
echo "=============="
echo "健康服务器: $HEALTHY_COUNT/$TOTAL_SERVERS"

if [ ${#UNHEALTHY_SERVERS[@]} -gt 0 ]; then
    echo ""
    echo "需要检查的服务器:"
    for server in "${UNHEALTHY_SERVERS[@]}"; do
        echo "  ❌ $server"
        echo "     调试命令: ssh $server 'journalctl -u hygon-dcgm-exporter -f'"
    done
fi

echo ""
echo "Prometheus配置示例:"
echo "scrape_configs:"
echo "  - job_name: 'hygon-dcu'"
echo "    static_configs:"
echo "      - targets:"
for server in "${SERVERS[@]}"; do
    # 提取IP地址（去掉用户名部分）
    IP=$(echo "$server" | sed 's/.*@//')
    echo "        - '$IP:9400'"
done
echo "    scrape_interval: 30s"
