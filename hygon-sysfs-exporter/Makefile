# 海光DCU Exporter Makefile

BINARY_NAME=hygon-dcu-exporter
VERSION=$(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
BUILD_TIME=$(shell date -u '+%Y-%m-%d_%H:%M:%S')
GO_VERSION=$(shell go version | cut -d' ' -f3)

# Go编译参数
LDFLAGS=-ldflags "-s -w -X main.Version=$(VERSION) -X main.BuildTime=$(BUILD_TIME) -X main.GoVersion=$(GO_VERSION)"
GOOS=linux
GOARCH=amd64
CGO_ENABLED=0

# 默认目标
.PHONY: all
all: clean build

# 编译
.PHONY: build
build:
	@echo "编译 $(BINARY_NAME)..."
	GOOS=$(GOOS) GOARCH=$(GOARCH) CGO_ENABLED=$(CGO_ENABLED) go build $(LDFLAGS) -o $(BINARY_NAME) .
	@echo "编译完成: $(BINARY_NAME)"

# 本地编译（用于开发测试）
.PHONY: build-local
build-local:
	@echo "本地编译 $(BINARY_NAME)..."
	go build $(LDFLAGS) -o $(BINARY_NAME) .
	@echo "本地编译完成: $(BINARY_NAME)"

# 清理
.PHONY: clean
clean:
	@echo "清理构建文件..."
	rm -f $(BINARY_NAME)
	rm -f $(BINARY_NAME).exe

# 测试
.PHONY: test
test:
	@echo "运行测试..."
	go test -v ./...

# 格式化代码
.PHONY: fmt
fmt:
	@echo "格式化代码..."
	go fmt ./...

# 代码检查
.PHONY: vet
vet:
	@echo "代码检查..."
	go vet ./...

# 依赖管理
.PHONY: mod-tidy
mod-tidy:
	@echo "整理依赖..."
	go mod tidy

# 本地安装
.PHONY: install-local
install-local: build
	@echo "本地安装..."
	sudo cp $(BINARY_NAME) /usr/local/bin/
	sudo chmod +x /usr/local/bin/$(BINARY_NAME)
	sudo cp $(BINARY_NAME).service /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable $(BINARY_NAME)
	@echo "安装完成，使用以下命令启动服务:"
	@echo "  sudo systemctl start $(BINARY_NAME)"

# 卸载
.PHONY: uninstall
uninstall:
	@echo "卸载服务..."
	-sudo systemctl stop $(BINARY_NAME)
	-sudo systemctl disable $(BINARY_NAME)
	-sudo rm -f /etc/systemd/system/$(BINARY_NAME).service
	-sudo rm -f /usr/local/bin/$(BINARY_NAME)
	sudo systemctl daemon-reload
	@echo "卸载完成"

# 启动服务
.PHONY: start
start:
	sudo systemctl start $(BINARY_NAME)

# 停止服务
.PHONY: stop
stop:
	sudo systemctl stop $(BINARY_NAME)

# 重启服务
.PHONY: restart
restart:
	sudo systemctl restart $(BINARY_NAME)

# 查看服务状态
.PHONY: status
status:
	sudo systemctl status $(BINARY_NAME)

# 查看日志
.PHONY: logs
logs:
	sudo journalctl -u $(BINARY_NAME) -f

# 测试指标
.PHONY: test-metrics
test-metrics:
	@echo "测试指标获取..."
	python3 test_exporter.py --test all

# 监控指标
.PHONY: monitor
monitor:
	@echo "监控指标变化..."
	python3 test_exporter.py --test monitor --duration 300 --interval 10

# 远程部署
.PHONY: deploy-remote
deploy-remote: build
	@if [ -z "$(HOST)" ]; then \
		echo "错误: 请指定HOST参数"; \
		echo "用法: make deploy-remote HOST=your-server"; \
		exit 1; \
	fi
	@echo "部署到远程主机: $(HOST)"
	python3 deploy.py --deploy-remote $(HOST) --user $(or $(USER),root)

# 打包发布
.PHONY: package
package: build
	@echo "打包发布..."
	mkdir -p dist
	cp $(BINARY_NAME) dist/
	cp $(BINARY_NAME).service dist/
	cp README.md dist/
	cp deploy.py dist/
	cp test_exporter.py dist/
	tar -czf dist/$(BINARY_NAME)-$(VERSION)-linux-amd64.tar.gz -C dist .
	@echo "打包完成: dist/$(BINARY_NAME)-$(VERSION)-linux-amd64.tar.gz"

# 显示帮助
.PHONY: help
help:
	@echo "海光DCU Exporter 构建工具"
	@echo ""
	@echo "可用目标:"
	@echo "  build          - 编译二进制文件"
	@echo "  build-local    - 本地编译（用于开发）"
	@echo "  clean          - 清理构建文件"
	@echo "  test           - 运行测试"
	@echo "  fmt            - 格式化代码"
	@echo "  vet            - 代码检查"
	@echo "  mod-tidy       - 整理依赖"
	@echo "  install-local  - 本地安装服务"
	@echo "  uninstall      - 卸载服务"
	@echo "  start          - 启动服务"
	@echo "  stop           - 停止服务"
	@echo "  restart        - 重启服务"
	@echo "  status         - 查看服务状态"
	@echo "  logs           - 查看服务日志"
	@echo "  test-metrics   - 测试指标获取"
	@echo "  monitor        - 监控指标变化"
	@echo "  deploy-remote  - 远程部署 (需要HOST参数)"
	@echo "  package        - 打包发布"
	@echo "  help           - 显示此帮助"
	@echo ""
	@echo "示例:"
	@echo "  make build"
	@echo "  make install-local"
	@echo "  make deploy-remote HOST=192.168.1.100"
