/*
 * Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
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

package counters

import "fmt"

type ExporterCounter uint16

const (
	DCGMFIUnknown        ExporterCounter = 0
	DCGMXIDErrorsCount   ExporterCounter = iota + 9000
	DCGMClockEventsCount ExporterCounter = iota + 9000
	DCGMGPUHealthStatus  ExporterCounter = iota + 9000

	// 海光卡相关计数器
	HygonTemperature     ExporterCounter = iota + 10000
	HygonAvgPower        ExporterCounter = iota + 10000
	HygonPowerCap        ExporterCounter = iota + 10000
	HygonVRAMUsage       ExporterCounter = iota + 10000
	HygonDCUUsage        ExporterCounter = iota + 10000
	HygonPerformanceMode ExporterCounter = iota + 10000
	HygonDeviceMode      ExporterCounter = iota + 10000
	HygonDeviceInfo      ExporterCounter = iota + 10000
)

// String method to convert the enum value to a string
func (enm ExporterCounter) String() string {
	switch enm {
	case DCGMXIDErrorsCount:
		return DCGMExpXIDErrorsCount
	case DCGMClockEventsCount:
		return DCGMExpClockEventsCount
	case DCGMGPUHealthStatus:
		return DCGMExpGPUHealthStatus
	case HygonTemperature:
		return "hygon_temperature"
	case HygonAvgPower:
		return "hygon_avg_power"
	case HygonPowerCap:
		return "hygon_power_cap"
	case HygonVRAMUsage:
		return "hygon_vram_usage"
	case HygonDCUUsage:
		return "hygon_dcu_usage"
	case HygonPerformanceMode:
		return "hygon_performance_mode"
	case HygonDeviceMode:
		return "hygon_device_mode"
	case HygonDeviceInfo:
		return "hygon_device_info"
	default:
		return "DCGM_FI_UNKNOWN"
	}
}

// DCGMFields maps DCGMExporterMetric String to enum
var DCGMFields = map[string]ExporterCounter{
	DCGMXIDErrorsCount.String():   DCGMXIDErrorsCount,
	DCGMClockEventsCount.String(): DCGMClockEventsCount,
	DCGMGPUHealthStatus.String():  DCGMGPUHealthStatus,
	DCGMFIUnknown.String():        DCGMFIUnknown,

	// 海光卡字段映射
	HygonTemperature.String():     HygonTemperature,
	HygonAvgPower.String():        HygonAvgPower,
	HygonPowerCap.String():        HygonPowerCap,
	HygonVRAMUsage.String():       HygonVRAMUsage,
	HygonDCUUsage.String():        HygonDCUUsage,
	HygonPerformanceMode.String(): HygonPerformanceMode,
	HygonDeviceMode.String():      HygonDeviceMode,
	HygonDeviceInfo.String():      HygonDeviceInfo,
}

func IdentifyMetricType(s string) (ExporterCounter, error) {
	mv, ok := DCGMFields[s]
	if !ok {
		return mv, fmt.Errorf("unknown ExporterCounter field '%s'", s)
	}
	return mv, nil
}
