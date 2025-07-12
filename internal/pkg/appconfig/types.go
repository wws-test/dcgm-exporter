/*
 * Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
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

package appconfig

import (
	"github.com/NVIDIA/go-dcgm/pkg/dcgm"
)

type KubernetesGPUIDType string

// DeviceType 定义设备类型
type DeviceType string

const (
	DeviceTypeNVIDIA DeviceType = "nvidia"
	DeviceTypeHygon  DeviceType = "hygon"
)

type DeviceOptions struct {
	Flex       bool  // If true, then monitor all GPUs if MIG mode is disabled or all GPU instances if MIG is enabled.
	MajorRange []int // The indices of each GPU/NvSwitch to monitor, or -1 to monitor all
	MinorRange []int // The indices of each GPUInstance/NvLink to monitor, or -1 to monitor all
}

// DumpConfig controls file-based debugging dumps
type DumpConfig struct {
	Enabled     bool   `yaml:"enabled" json:"enabled"`         // Enable file-based dumps
	Directory   string `yaml:"directory" json:"directory"`     // Directory to store dump files
	Retention   int    `yaml:"retention" json:"retention"`     // Retention period in hours (0 = no cleanup)
	Compression bool   `yaml:"compression" json:"compression"` // Use gzip compression for dump files
}

type Config struct {
	CollectorsFile             string
	Address                    string
	CollectInterval            int
	Kubernetes                 bool
	KubernetesEnablePodLabels  bool
	KubernetesGPUIdType        KubernetesGPUIDType
	CollectDCP                 bool
	UseOldNamespace            bool
	UseRemoteHE                bool
	RemoteHEInfo               string
	GPUDeviceOptions           DeviceOptions
	SwitchDeviceOptions        DeviceOptions
	CPUDeviceOptions           DeviceOptions
	NoHostname                 bool
	UseFakeGPUs                bool
	ConfigMapData              string
	MetricGroups               []dcgm.MetricGroup
	WebSystemdSocket           bool
	WebConfigFile              string
	XIDCountWindowSize         int
	ReplaceBlanksInModelName   bool
	Debug                      bool
	ClockEventsCountWindowSize int
	EnableDCGMLog              bool
	DCGMLogLevel               string
	PodResourcesKubeletSocket  string
	HPCJobMappingDir           string
	NvidiaResourceNames        []string
	KubernetesVirtualGPUs      bool
	DumpConfig                 DumpConfig // Configuration for file-based dumps

	// 海光卡相关配置
	DeviceType                 DeviceType // 设备类型：nvidia 或 hygon
	HygonDeviceOptions         DeviceOptions // 海光卡设备选项
	UseHygonMode               bool       // 是否启用海光卡模式
	HySmiPath                  string     // hy-smi 命令路径
}
