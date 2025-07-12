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

import "time"

// HygonDevice 表示海光DCU设备信息
type HygonDevice struct {
	ID          uint   // DCU ID
	Temperature float64 // 温度 (°C)
	AvgPower    float64 // 平均功耗 (W)
	Performance string  // 性能模式 (auto/manual)
	PowerCap    float64 // 功耗上限 (W)
	VRAMUsage   float64 // 显存使用率 (%)
	DCUUsage    float64 // DCU使用率 (%)
	Mode        string  // 运行模式 (Normal/...)
	ModelName   string  // 设备型号名称
	UUID        string  // 设备UUID (如果可用)
}

// HygonMetrics 表示从hy-smi获取的所有指标数据
type HygonMetrics struct {
	Devices   []HygonDevice
	Timestamp time.Time
}

// HygonProvider 接口定义了海光卡数据提供者的方法
type HygonProvider interface {
	// GetDevices 获取所有海光DCU设备列表
	GetDevices() ([]HygonDevice, error)
	
	// GetDeviceCount 获取设备数量
	GetDeviceCount() (uint, error)
	
	// GetDeviceInfo 获取指定设备的详细信息
	GetDeviceInfo(deviceID uint) (HygonDevice, error)
	
	// GetMetrics 获取所有设备的当前指标
	GetMetrics() (HygonMetrics, error)
	
	// IsAvailable 检查hy-smi工具是否可用
	IsAvailable() bool
	
	// Cleanup 清理资源
	Cleanup()
}

// HygonSMIOutput 表示hy-smi命令的原始输出解析结果
type HygonSMIOutput struct {
	Header  []string
	Devices []map[string]string
}

// FieldType 定义指标字段类型
type FieldType int

const (
	FieldTypeFloat FieldType = iota
	FieldTypeString
	FieldTypeInt
)

// HygonField 定义海光卡监控字段
type HygonField struct {
	ID          uint      // 字段ID
	Name        string    // 字段名称
	Description string    // 字段描述
	Unit        string    // 单位
	Type        FieldType // 数据类型
}

// 预定义的海光卡监控字段
var (
	HygonFieldTemperature = HygonField{
		ID:          1001,
		Name:        "temperature",
		Description: "DCU Temperature",
		Unit:        "C",
		Type:        FieldTypeFloat,
	}
	
	HygonFieldAvgPower = HygonField{
		ID:          1002,
		Name:        "avg_power",
		Description: "Average Power Consumption",
		Unit:        "W",
		Type:        FieldTypeFloat,
	}
	
	HygonFieldPowerCap = HygonField{
		ID:          1003,
		Name:        "power_cap",
		Description: "Power Cap Limit",
		Unit:        "W",
		Type:        FieldTypeFloat,
	}
	
	HygonFieldVRAMUsage = HygonField{
		ID:          1004,
		Name:        "vram_usage",
		Description: "VRAM Usage Percentage",
		Unit:        "%",
		Type:        FieldTypeFloat,
	}
	
	HygonFieldDCUUsage = HygonField{
		ID:          1005,
		Name:        "dcu_usage",
		Description: "DCU Usage Percentage",
		Unit:        "%",
		Type:        FieldTypeFloat,
	}
	
	HygonFieldPerformance = HygonField{
		ID:          1006,
		Name:        "performance",
		Description: "Performance Mode",
		Unit:        "",
		Type:        FieldTypeString,
	}
	
	HygonFieldMode = HygonField{
		ID:          1007,
		Name:        "mode",
		Description: "Operating Mode",
		Unit:        "",
		Type:        FieldTypeString,
	}
)

// GetAllHygonFields 返回所有预定义的海光卡字段
func GetAllHygonFields() []HygonField {
	return []HygonField{
		HygonFieldTemperature,
		HygonFieldAvgPower,
		HygonFieldPowerCap,
		HygonFieldVRAMUsage,
		HygonFieldDCUUsage,
		HygonFieldPerformance,
		HygonFieldMode,
	}
}
