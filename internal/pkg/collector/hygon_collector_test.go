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
	"testing"
	"time"

	"github.com/NVIDIA/dcgm-exporter/internal/pkg/appconfig"
	"github.com/NVIDIA/dcgm-exporter/internal/pkg/counters"
	"github.com/NVIDIA/dcgm-exporter/internal/pkg/hygonprovider"
)

// mockHygonProvider 用于测试的模拟海光卡提供者
type mockHygonProvider struct {
	devices []hygonprovider.HygonDevice
}

func (m *mockHygonProvider) IsAvailable() bool {
	return true
}

func (m *mockHygonProvider) GetDeviceCount() (uint, error) {
	return uint(len(m.devices)), nil
}

func (m *mockHygonProvider) GetDevices() ([]hygonprovider.HygonDevice, error) {
	return m.devices, nil
}

func (m *mockHygonProvider) GetDeviceInfo(deviceID uint) (hygonprovider.HygonDevice, error) {
	for _, device := range m.devices {
		if device.ID == deviceID {
			return device, nil
		}
	}
	return hygonprovider.HygonDevice{}, nil
}

func (m *mockHygonProvider) GetMetrics() (hygonprovider.HygonMetrics, error) {
	return hygonprovider.HygonMetrics{
		Devices:   m.devices,
		Timestamp: time.Now(),
	}, nil
}

func (m *mockHygonProvider) Cleanup() {
	// Mock cleanup
}

func TestNewHygonCollector(t *testing.T) {
	counters := []counters.Counter{
		{FieldName: "hygon_temperature", PromType: "gauge"},
		{FieldName: "hygon_avg_power", PromType: "gauge"},
	}
	
	config := &appconfig.Config{
		UseOldNamespace:          false,
		ReplaceBlanksInModelName: false,
	}
	
	collector, err := NewHygonCollector(counters, "test-host", config)
	if err != nil {
		t.Fatalf("Failed to create Hygon collector: %v", err)
	}
	
	if collector == nil {
		t.Fatal("Expected non-nil collector")
	}
	
	if collector.hostname != "test-host" {
		t.Errorf("Expected hostname 'test-host', got '%s'", collector.hostname)
	}
	
	if len(collector.counters) != 2 {
		t.Errorf("Expected 2 counters, got %d", len(collector.counters))
	}
}

func TestHygonCollectorGetMetrics(t *testing.T) {
	// 设置模拟数据
	mockDevices := []hygonprovider.HygonDevice{
		{
			ID:          0,
			Temperature: 58.0,
			AvgPower:    259.0,
			Performance: "auto",
			PowerCap:    400.0,
			VRAMUsage:   97.0,
			DCUUsage:    34.2,
			Mode:        "Normal",
			ModelName:   "Hygon DCU",
			UUID:        "DCU-0",
		},
		{
			ID:          1,
			Temperature: 60.0,
			AvgPower:    280.0,
			Performance: "auto",
			PowerCap:    400.0,
			VRAMUsage:   85.0,
			DCUUsage:    45.5,
			Mode:        "Normal",
			ModelName:   "Hygon DCU",
			UUID:        "DCU-1",
		},
	}
	
	// 设置模拟提供者
	mockProvider := &mockHygonProvider{devices: mockDevices}
	hygonprovider.SetClient(mockProvider)
	
	counters := []counters.Counter{
		{FieldName: "hygon_temperature", PromType: "gauge"},
		{FieldName: "hygon_avg_power", PromType: "gauge"},
		{FieldName: "hygon_dcu_usage", PromType: "gauge"},
	}
	
	config := &appconfig.Config{
		UseOldNamespace:          false,
		ReplaceBlanksInModelName: false,
	}
	
	collector, err := NewHygonCollector(counters, "test-host", config)
	if err != nil {
		t.Fatalf("Failed to create Hygon collector: %v", err)
	}
	
	metrics, err := collector.GetMetrics()
	if err != nil {
		t.Fatalf("Failed to get metrics: %v", err)
	}
	
	// 验证指标数量
	expectedCounters := 3
	if len(metrics) != expectedCounters {
		t.Errorf("Expected %d counter types, got %d", expectedCounters, len(metrics))
	}
	
	// 验证每个计数器都有2个设备的指标
	for counter, metricList := range metrics {
		expectedMetrics := 2 // 2个设备
		if len(metricList) != expectedMetrics {
			t.Errorf("Counter %s: expected %d metrics, got %d", 
				counter.FieldName, expectedMetrics, len(metricList))
		}
		
		// 验证指标标签
		for _, metric := range metricList {
			if metric.Labels["hostname"] != "test-host" {
				t.Errorf("Expected hostname 'test-host', got '%s'", metric.Labels["hostname"])
			}
			
			if metric.Labels["modelName"] != "Hygon DCU" {
				t.Errorf("Expected modelName 'Hygon DCU', got '%s'", metric.Labels["modelName"])
			}
			
			// 验证设备特定标签
			if metric.Labels["mode"] != "Normal" {
				t.Errorf("Expected mode 'Normal', got '%s'", metric.Labels["mode"])
			}
			
			if metric.Labels["performance"] != "auto" {
				t.Errorf("Expected performance 'auto', got '%s'", metric.Labels["performance"])
			}
		}
	}
}

func TestBuildMetricName(t *testing.T) {
	collector := &HygonCollector{
		useOldNamespace: false,
	}
	
	counter := counters.Counter{FieldName: "hygon_temperature"}
	metricName := collector.buildMetricName(counter)
	
	expectedName := "DCGM_hygon_temperature"
	if metricName != expectedName {
		t.Errorf("Expected metric name '%s', got '%s'", expectedName, metricName)
	}
	
	// 测试旧命名空间
	collector.useOldNamespace = true
	metricName = collector.buildMetricName(counter)
	
	expectedName = "dcgm_hygon_temperature"
	if metricName != expectedName {
		t.Errorf("Expected metric name '%s', got '%s'", expectedName, metricName)
	}
}

func TestGetDeviceMetricValue(t *testing.T) {
	collector := &HygonCollector{}
	
	device := hygonprovider.HygonDevice{
		ID:          0,
		Temperature: 58.5,
		AvgPower:    259.3,
		Performance: "auto",
		Mode:        "Normal",
		DCUUsage:    34.2,
		VRAMUsage:   97.1,
		PowerCap:    400.0,
	}
	
	testCases := []struct {
		fieldName     string
		expectedValue string
	}{
		{"hygon_temperature", "58.5"},
		{"hygon_avg_power", "259.3"},
		{"hygon_dcu_usage", "34.2"},
		{"hygon_vram_usage", "97.1"},
		{"hygon_power_cap", "400.0"},
		{"hygon_performance_mode", "1"}, // auto = 1
		{"hygon_device_mode", "1"},      // Normal = 1
	}
	
	for _, tc := range testCases {
		counter := counters.Counter{FieldName: tc.fieldName}
		value, err := collector.getDeviceMetricValue(device, counter)
		if err != nil {
			t.Errorf("Failed to get metric value for %s: %v", tc.fieldName, err)
			continue
		}
		
		if value != tc.expectedValue {
			t.Errorf("Field %s: expected value '%s', got '%s'", 
				tc.fieldName, tc.expectedValue, value)
		}
	}
}

func TestGetDeviceMetricValueUnknownField(t *testing.T) {
	collector := &HygonCollector{}
	device := hygonprovider.HygonDevice{}
	counter := counters.Counter{FieldName: "unknown_field"}
	
	_, err := collector.getDeviceMetricValue(device, counter)
	if err == nil {
		t.Error("Expected error for unknown field, got nil")
	}
}

func TestHygonCollectorCleanup(t *testing.T) {
	collector := &HygonCollector{}
	
	// 这应该不会panic或出错
	collector.Cleanup()
}

func TestGetName(t *testing.T) {
	collector := &HygonCollector{}
	name := collector.GetName()
	
	expectedName := "HygonCollector"
	if name != expectedName {
		t.Errorf("Expected name '%s', got '%s'", expectedName, name)
	}
}
