/*
 * Copyright (c) 2024, HYGON CORPORATION.  All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package hygonprovider

import (
	"bufio"
	"fmt"
	"log/slog"
	"os/exec"
	"regexp"
	"strconv"
	"strings"
	"time"
)

var hygonInterface HygonProvider

// Initialize 初始化海光卡数据提供者单例
func Initialize() {
	hygonInterface = newHygonProvider()
}

// Client 获取海光卡数据提供者实例
func Client() HygonProvider {
	return hygonInterface
}

// SetClient 设置海光卡数据提供者实例（主要用于测试）
func SetClient(h HygonProvider) {
	hygonInterface = h
}

// hygonProvider 实现 HygonProvider 接口
type hygonProvider struct {
	hySmiPath string
}

// newHygonProvider 创建新的海光卡数据提供者
func newHygonProvider() HygonProvider {
	provider := &hygonProvider{}
	
	// 查找hy-smi命令路径
	if path, err := exec.LookPath("hy-smi"); err == nil {
		provider.hySmiPath = path
		slog.Info("Found hy-smi command", slog.String("path", path))
	} else {
		slog.Warn("hy-smi command not found in PATH", slog.String("error", err.Error()))
		provider.hySmiPath = "hy-smi" // 仍然尝试使用默认名称
	}
	
	return provider
}

// IsAvailable 检查hy-smi工具是否可用
func (h *hygonProvider) IsAvailable() bool {
	cmd := exec.Command(h.hySmiPath, "--help")
	err := cmd.Run()
	return err == nil
}

// GetDeviceCount 获取设备数量
func (h *hygonProvider) GetDeviceCount() (uint, error) {
	devices, err := h.GetDevices()
	if err != nil {
		return 0, err
	}
	return uint(len(devices)), nil
}

// GetDevices 获取所有海光DCU设备列表
func (h *hygonProvider) GetDevices() ([]HygonDevice, error) {
	output, err := h.runHySmi()
	if err != nil {
		return nil, fmt.Errorf("failed to run hy-smi: %w", err)
	}
	
	return h.parseHySmiOutput(output)
}

// GetDeviceInfo 获取指定设备的详细信息
func (h *hygonProvider) GetDeviceInfo(deviceID uint) (HygonDevice, error) {
	devices, err := h.GetDevices()
	if err != nil {
		return HygonDevice{}, err
	}
	
	for _, device := range devices {
		if device.ID == deviceID {
			return device, nil
		}
	}
	
	return HygonDevice{}, fmt.Errorf("device with ID %d not found", deviceID)
}

// GetMetrics 获取所有设备的当前指标
func (h *hygonProvider) GetMetrics() (HygonMetrics, error) {
	devices, err := h.GetDevices()
	if err != nil {
		return HygonMetrics{}, err
	}
	
	return HygonMetrics{
		Devices:   devices,
		Timestamp: time.Now(),
	}, nil
}

// Cleanup 清理资源
func (h *hygonProvider) Cleanup() {
	// 海光卡提供者目前不需要特殊的清理操作
	slog.Info("Hygon provider cleanup completed")
}

// runHySmi 执行hy-smi命令并返回输出
func (h *hygonProvider) runHySmi() (string, error) {
	cmd := exec.Command(h.hySmiPath)
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("hy-smi command failed: %w", err)
	}
	
	return string(output), nil
}

// parseHySmiOutput 解析hy-smi命令的输出
func (h *hygonProvider) parseHySmiOutput(output string) ([]HygonDevice, error) {
	var devices []HygonDevice
	
	scanner := bufio.NewScanner(strings.NewReader(output))
	var inDataSection bool
	
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		
		// 跳过空行和分隔线
		if line == "" || strings.Contains(line, "=") {
			continue
		}
		
		// 检查是否到达数据部分
		if strings.Contains(line, "DCU") && strings.Contains(line, "Temp") {
			inDataSection = true
			continue
		}
		
		// 检查是否结束数据部分
		if strings.Contains(line, "End of SMI Log") {
			break
		}
		
		// 解析设备数据行
		if inDataSection && !strings.Contains(line, "DCU") {
			device, err := h.parseDeviceLine(line)
			if err != nil {
				slog.Warn("Failed to parse device line", slog.String("line", line), slog.String("error", err.Error()))
				continue
			}
			devices = append(devices, device)
		}
	}
	
	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("error reading hy-smi output: %w", err)
	}
	
	return devices, nil
}

// parseDeviceLine 解析单个设备数据行
func (h *hygonProvider) parseDeviceLine(line string) (HygonDevice, error) {
	// 使用正则表达式解析设备行
	// 示例: "0       58.0C    259.0W     auto     400.0W     97%        34.2%     Normal"
	re := regexp.MustCompile(`(\d+)\s+(\d+\.?\d*)C\s+(\d+\.?\d*)W\s+(\w+)\s+(\d+\.?\d*)W\s+(\d+)%\s+(\d+\.?\d*)%\s+(\w+)`)
	matches := re.FindStringSubmatch(line)
	
	if len(matches) != 9 {
		return HygonDevice{}, fmt.Errorf("invalid device line format: %s", line)
	}
	
	id, _ := strconv.ParseUint(matches[1], 10, 32)
	temp, _ := strconv.ParseFloat(matches[2], 64)
	avgPower, _ := strconv.ParseFloat(matches[3], 64)
	performance := matches[4]
	powerCap, _ := strconv.ParseFloat(matches[5], 64)
	vramUsage, _ := strconv.ParseFloat(matches[6], 64)
	dcuUsage, _ := strconv.ParseFloat(matches[7], 64)
	mode := matches[8]
	
	return HygonDevice{
		ID:          uint(id),
		Temperature: temp,
		AvgPower:    avgPower,
		Performance: performance,
		PowerCap:    powerCap,
		VRAMUsage:   vramUsage,
		DCUUsage:    dcuUsage,
		Mode:        mode,
		ModelName:   "Hygon DCU", // 默认型号名称，可以后续扩展
		UUID:        fmt.Sprintf("DCU-%d", id), // 生成简单的UUID
	}, nil
}
