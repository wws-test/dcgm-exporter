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
	"testing"
)

// mockHygonProvider 用于测试的模拟海光卡提供者
type mockHygonProvider struct {
	mockOutput string
	available  bool
}

func (m *mockHygonProvider) IsAvailable() bool {
	return m.available
}

func (m *mockHygonProvider) GetDeviceCount() (uint, error) {
	devices, err := m.GetDevices()
	if err != nil {
		return 0, err
	}
	return uint(len(devices)), nil
}

func (m *mockHygonProvider) GetDevices() ([]HygonDevice, error) {
	return m.parseHySmiOutput(m.mockOutput)
}

func (m *mockHygonProvider) GetDeviceInfo(deviceID uint) (HygonDevice, error) {
	devices, err := m.GetDevices()
	if err != nil {
		return HygonDevice{}, err
	}
	
	for _, device := range devices {
		if device.ID == deviceID {
			return device, nil
		}
	}
	
	return HygonDevice{}, nil
}

func (m *mockHygonProvider) GetMetrics() (HygonMetrics, error) {
	devices, err := m.GetDevices()
	if err != nil {
		return HygonMetrics{}, err
	}
	
	return HygonMetrics{
		Devices: devices,
	}, nil
}

func (m *mockHygonProvider) Cleanup() {
	// Mock cleanup
}

func (m *mockHygonProvider) parseHySmiOutput(output string) ([]HygonDevice, error) {
	provider := &hygonProvider{}
	return provider.parseHySmiOutput(output)
}

func TestParseHySmiOutput(t *testing.T) {
	mockOutput := `============================ System Management Interface =============================
======================================================================================
DCU     Temp     AvgPwr     Perf     PwrCap     VRAM%      DCU%      Mode     
0       58.0C    259.0W     auto     400.0W     97%        34.2%     Normal   
1       58.0C    251.0W     auto     400.0W     97%        42.5%     Normal   
2       57.0C    245.0W     auto     400.0W     97%        73.3%     Normal   
3       58.0C    249.0W     auto     400.0W     96%        88.3%     Normal   
4       41.0C    104.0W     auto     400.0W     0%         0.0%      Normal   
5       41.0C    108.0W     auto     400.0W     0%         0.0%      Normal   
6       41.0C    103.0W     auto     400.0W     0%         0.0%      Normal   
7       41.0C    107.0W     auto     400.0W     0%         0.0%      Normal   
======================================================================================
=================================== End of SMI Log ===================================`

	mock := &mockHygonProvider{
		mockOutput: mockOutput,
		available:  true,
	}

	devices, err := mock.GetDevices()
	if err != nil {
		t.Fatalf("Failed to parse hy-smi output: %v", err)
	}

	expectedDeviceCount := 8
	if len(devices) != expectedDeviceCount {
		t.Errorf("Expected %d devices, got %d", expectedDeviceCount, len(devices))
	}

	// 测试第一个设备的数据
	if len(devices) > 0 {
		device := devices[0]
		if device.ID != 0 {
			t.Errorf("Expected device ID 0, got %d", device.ID)
		}
		if device.Temperature != 58.0 {
			t.Errorf("Expected temperature 58.0, got %f", device.Temperature)
		}
		if device.AvgPower != 259.0 {
			t.Errorf("Expected avg power 259.0, got %f", device.AvgPower)
		}
		if device.Performance != "auto" {
			t.Errorf("Expected performance 'auto', got '%s'", device.Performance)
		}
		if device.PowerCap != 400.0 {
			t.Errorf("Expected power cap 400.0, got %f", device.PowerCap)
		}
		if device.VRAMUsage != 97.0 {
			t.Errorf("Expected VRAM usage 97.0, got %f", device.VRAMUsage)
		}
		if device.DCUUsage != 34.2 {
			t.Errorf("Expected DCU usage 34.2, got %f", device.DCUUsage)
		}
		if device.Mode != "Normal" {
			t.Errorf("Expected mode 'Normal', got '%s'", device.Mode)
		}
	}
}

func TestGetDeviceCount(t *testing.T) {
	mockOutput := `============================ System Management Interface =============================
======================================================================================
DCU     Temp     AvgPwr     Perf     PwrCap     VRAM%      DCU%      Mode     
0       58.0C    259.0W     auto     400.0W     97%        34.2%     Normal   
1       58.0C    251.0W     auto     400.0W     97%        42.5%     Normal   
======================================================================================
=================================== End of SMI Log ===================================`

	mock := &mockHygonProvider{
		mockOutput: mockOutput,
		available:  true,
	}

	count, err := mock.GetDeviceCount()
	if err != nil {
		t.Fatalf("Failed to get device count: %v", err)
	}

	expectedCount := uint(2)
	if count != expectedCount {
		t.Errorf("Expected device count %d, got %d", expectedCount, count)
	}
}

func TestGetDeviceInfo(t *testing.T) {
	mockOutput := `============================ System Management Interface =============================
======================================================================================
DCU     Temp     AvgPwr     Perf     PwrCap     VRAM%      DCU%      Mode     
0       58.0C    259.0W     auto     400.0W     97%        34.2%     Normal   
1       58.0C    251.0W     auto     400.0W     97%        42.5%     Normal   
======================================================================================
=================================== End of SMI Log ===================================`

	mock := &mockHygonProvider{
		mockOutput: mockOutput,
		available:  true,
	}

	device, err := mock.GetDeviceInfo(1)
	if err != nil {
		t.Fatalf("Failed to get device info: %v", err)
	}

	if device.ID != 1 {
		t.Errorf("Expected device ID 1, got %d", device.ID)
	}
	if device.AvgPower != 251.0 {
		t.Errorf("Expected avg power 251.0, got %f", device.AvgPower)
	}
}

func TestIsAvailable(t *testing.T) {
	mock := &mockHygonProvider{
		available: true,
	}

	if !mock.IsAvailable() {
		t.Error("Expected IsAvailable to return true")
	}

	mock.available = false
	if mock.IsAvailable() {
		t.Error("Expected IsAvailable to return false")
	}
}

func TestGetAllHygonFields(t *testing.T) {
	fields := GetAllHygonFields()
	
	expectedFieldCount := 7
	if len(fields) != expectedFieldCount {
		t.Errorf("Expected %d fields, got %d", expectedFieldCount, len(fields))
	}
	
	// 检查是否包含预期的字段
	fieldNames := make(map[string]bool)
	for _, field := range fields {
		fieldNames[field.Name] = true
	}
	
	expectedFields := []string{
		"temperature", "avg_power", "power_cap", 
		"vram_usage", "dcu_usage", "performance", "mode",
	}
	
	for _, expectedField := range expectedFields {
		if !fieldNames[expectedField] {
			t.Errorf("Expected field '%s' not found", expectedField)
		}
	}
}
