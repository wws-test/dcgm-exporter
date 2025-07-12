#!/bin/bash

# 批量部署海光DCU Exporter到多台服务器
# 用法: ./deploy_to_servers.sh server1 server2 server3

PACKAGE_FILE="hygon-dcgm-exporter-release.tar.gz"
REMOTE_TMP="/tmp/hygon-dcgm-exporter-install"

if [ ! -f "$PACKAGE_FILE" ]; then
    echo "❌ 错误: 找不到分发包 $PACKAGE_FILE"
    echo "请先从构建服务器下载分发包"
    exit 1
fi

if [ $# -eq 0 ]; then
    echo "用法: $0 server1 [server2] [server3] ..."
    echo "示例: $0 user@192.168.1.10 user@192.168.1.11"
    exit 1
fi

SERVERS=("$@")
TOTAL_SERVERS=${#SERVERS[@]}

echo "🚀 批量部署海光DCU Exporter"
echo "================================"
echo "分发包: $PACKAGE_FILE"
echo "目标服务器数量: $TOTAL_SERVERS"
echo "服务器列表: ${SERVERS[*]}"
echo ""

# 确认部署
read -p "确认开始部署? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消部署"
    exit 1
fi

SUCCESS_COUNT=0
FAILED_SERVERS=()

for i in "${!SERVERS[@]}"; do
    SERVER="${SERVERS[$i]}"
    CURRENT=$((i + 1))
    
    echo ""
    echo "[$CURRENT/$TOTAL_SERVERS] 部署到服务器: $SERVER"
    echo "----------------------------------------"
    
    # 1. 上传分发包
    echo "1. 上传分发包..."
    if scp "$PACKAGE_FILE" "$SERVER:$REMOTE_TMP.tar.gz"; then
        echo "✅ 上传成功"
    else
        echo "❌ 上传失败"
        FAILED_SERVERS+=("$SERVER")
        continue
    fi
    
    # 2. 远程安装
    echo "2. 远程安装..."
    if ssh "$SERVER" << 'REMOTE_INSTALL'
set -e
cd /tmp
rm -rf hygon-dcgm-exporter-install
mkdir hygon-dcgm-exporter-install
cd hygon-dcgm-exporter-install
tar -xzf ../hygon-dcgm-exporter-install.tar.gz
cd hygon-dcgm-exporter-*

echo "开始安装..."
sudo ./install.sh

echo "启动服务..."
sudo systemctl start hygon-dcgm-exporter
sudo systemctl enable hygon-dcgm-exporter

echo "验证服务..."
sleep 3
if curl -s http://localhost:9400/health | grep -q "HEALTHY"; then
    echo "✅ 服务验证成功"
else
    echo "❌ 服务验证失败"
    exit 1
fi
REMOTE_INSTALL
    then
        echo "✅ 安装成功"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo "❌ 安装失败"
        FAILED_SERVERS+=("$SERVER")
    fi
done

echo ""
echo "🎉 部署完成！"
echo "=============="
echo "成功: $SUCCESS_COUNT/$TOTAL_SERVERS"

if [ ${#FAILED_SERVERS[@]} -gt 0 ]; then
    echo "失败的服务器:"
    for server in "${FAILED_SERVERS[@]}"; do
        echo "  ❌ $server"
    done
fi

echo ""
echo "验证命令:"
echo "for server in ${SERVERS[*]}; do"
echo "  echo \"检查 \$server:\""
echo "  ssh \$server 'curl -s http://localhost:9400/health'"
echo "done"
