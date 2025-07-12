/*
 * Copyright (c) 2024, HYGON CORPORATION.  All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package collector

import (
	"fmt"
	"log/slog"
	"strconv"
	"strings"

	"github.com/NVIDIA/dcgm-exporter/internal/pkg/appconfig"
	"github.com/NVIDIA/dcgm-exporter/internal/pkg/counters"
	"github.com/NVIDIA/dcgm-exporter/internal/pkg/hygonprovider"
)

// HygonCollector 海光卡指标收集器
type HygonCollector struct {
	counters                 []counters.Counter
	hostname                 string
	useOldNamespace          bool
	replaceBlanksInModelName bool
}

// NewHygonCollector 创建新的海光卡收集器
func NewHygonCollector(
	c []counters.Counter,
	hostname string,
	config *appconfig.Config,
) (*HygonCollector, error) {
	collector := &HygonCollector{
		counters: c,
		hostname: hostname,
	}

	if config != nil {
		collector.useOldNamespace = config.UseOldNamespace
		collector.replaceBlanksInModelName = config.ReplaceBlanksInModelName
	}

	return collector, nil
}

// GetMetrics 获取海光卡指标数据
func (c *HygonCollector) GetMetrics() (MetricsByCounter, error) {
	metrics := make(MetricsByCounter)

	// 获取海光卡指标数据
	hygonMetrics, err := hygonprovider.Client().GetMetrics()
	if err != nil {
		return nil, fmt.Errorf("failed to get Hygon metrics: %w", err)
	}

	// 为每个设备生成指标
	for _, device := range hygonMetrics.Devices {
		deviceLabels := c.buildDeviceLabels(device)

		// 处理每个计数器
		for _, counter := range c.counters {
			metricName := c.buildMetricName(counter)
			
			// 根据计数器类型获取对应的设备指标值
			value, err := c.getDeviceMetricValue(device, counter)
			if err != nil {
				slog.Warn("Failed to get metric value", 
					slog.String("counter", counter.FieldName),
					slog.Uint64("device", uint64(device.ID)),
					slog.String("error", err.Error()))
				continue
			}

			// 创建指标
			metric := Metric{
				Name:   metricName,
				Labels: deviceLabels,
				Value:  value,
			}

			// 添加到指标集合
			if _, exists := metrics[counter]; !exists {
				metrics[counter] = []Metric{}
			}
			metrics[counter] = append(metrics[counter], metric)
		}
	}

	return metrics, nil
}

// buildDeviceLabels 构建设备标签
func (c *HygonCollector) buildDeviceLabels(device hygonprovider.HygonDevice) map[string]string {
	labels := make(map[string]string)

	// 基础标签
	labels["device"] = strconv.FormatUint(uint64(device.ID), 10)
	labels["uuid"] = device.UUID
	
	// 处理型号名称中的空格
	modelName := device.ModelName
	if c.replaceBlanksInModelName {
		modelName = replaceBlankInString(modelName)
	}
	labels["modelName"] = modelName
	
	// 添加主机名（如果不禁用）
	if c.hostname != "" {
		labels["hostname"] = c.hostname
	}

	// 添加设备特定标签
	labels["mode"] = device.Mode
	labels["performance"] = device.Performance

	return labels
}

// buildMetricName 构建指标名称
func (c *HygonCollector) buildMetricName(counter counters.Counter) string {
	var namespace string
	if c.useOldNamespace {
		namespace = "dcgm"
	} else {
		namespace = "DCGM"
	}
	
	return fmt.Sprintf("%s_%s", namespace, counter.FieldName)
}

// getDeviceMetricValue 根据计数器类型获取设备指标值
func (c *HygonCollector) getDeviceMetricValue(device hygonprovider.HygonDevice, counter counters.Counter) (string, error) {
	switch counter.FieldName {
	case "hygon_temperature":
		return fmt.Sprintf("%.1f", device.Temperature), nil
	case "hygon_avg_power":
		return fmt.Sprintf("%.1f", device.AvgPower), nil
	case "hygon_power_cap":
		return fmt.Sprintf("%.1f", device.PowerCap), nil
	case "hygon_vram_usage":
		return fmt.Sprintf("%.1f", device.VRAMUsage), nil
	case "hygon_dcu_usage":
		return fmt.Sprintf("%.1f", device.DCUUsage), nil
	case "hygon_performance_mode":
		// 将性能模式转换为数值（auto=1, manual=0）
		if device.Performance == "auto" {
			return "1", nil
		}
		return "0", nil
	case "hygon_device_mode":
		// 将设备模式转换为数值（Normal=1, 其他=0）
		if device.Mode == "Normal" {
			return "1", nil
		}
		return "0", nil
	default:
		return "", fmt.Errorf("unknown counter field: %s", counter.FieldName)
	}
}

// Cleanup 清理收集器资源
func (c *HygonCollector) Cleanup() {
	// 海光卡收集器目前不需要特殊的清理操作
	slog.Info("Hygon collector cleanup completed")
}

// replaceBlankInString 替换字符串中的空格为破折号
func replaceBlankInString(input string) string {
	return strings.ReplaceAll(input, " ", "-")
}

// GetName 返回收集器名称
func (c *HygonCollector) GetName() string {
	return "HygonCollector"
}
