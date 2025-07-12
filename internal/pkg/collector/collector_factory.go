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

package collector

import (
	"fmt"
	"log/slog"
	"os"

	"github.com/NVIDIA/go-dcgm/pkg/dcgm"

	"github.com/NVIDIA/dcgm-exporter/internal/pkg/appconfig"
	"github.com/NVIDIA/dcgm-exporter/internal/pkg/counters"
	"github.com/NVIDIA/dcgm-exporter/internal/pkg/devicewatchlistmanager"
	"github.com/NVIDIA/dcgm-exporter/internal/pkg/hygonprovider"
	"github.com/NVIDIA/dcgm-exporter/internal/pkg/logging"
)

type Factory interface {
	NewCollectors() []EntityCollectorTuple
}

type collectorFactory struct {
	counterSet             *counters.CounterSet
	deviceWatchListManager devicewatchlistmanager.Manager
	hostname               string
	config                 *appconfig.Config
}

func InitCollectorFactory(
	counterSet *counters.CounterSet,
	deviceWatchListManager devicewatchlistmanager.Manager,
	hostname string,
	config *appconfig.Config,
) Factory {
	return &collectorFactory{
		counterSet:             counterSet,
		deviceWatchListManager: deviceWatchListManager,
		hostname:               hostname,
		config:                 config,
	}
}

func (cf *collectorFactory) NewCollectors() []EntityCollectorTuple {
	slog.Debug("Counters are being initialized.",
		slog.String(logging.DumpKey, fmt.Sprintf("%+v", cf.counterSet.DCGMCounters)))

	entityCollectorTuples := make([]EntityCollectorTuple, 0)

	// 检查是否启用海光卡模式
	if cf.config != nil && cf.config.UseHygonMode {
		return cf.createHygonCollectors()
	}

	entityTypes := []dcgm.Field_Entity_Group{
		dcgm.FE_GPU,
		dcgm.FE_SWITCH,
		dcgm.FE_LINK,
		dcgm.FE_CPU,
		dcgm.FE_CPU_CORE,
	}

	for _, entityType := range entityTypes {
		if len(cf.counterSet.DCGMCounters) > 0 {
			entityWatchList, exists := cf.deviceWatchListManager.EntityWatchList(entityType)
			if !exists || len(entityWatchList.DeviceFields()) == 0 {
				continue
			}

			if dcgmCollector, err := cf.enableDCGMCollector(entityWatchList); err != nil {
				slog.Error(fmt.Sprintf("DCGM collector for entity type '%s' cannot be initialized; err: %v",
					entityType.String(), err))
				// Not a fatal error
			} else {
				entityCollectorTuples = append(entityCollectorTuples, EntityCollectorTuple{
					entity:    entityType,
					collector: dcgmCollector,
				})
			}
		}
	}

	if IsDCGMExpClockEventsCountEnabled(cf.counterSet.ExporterCounters) {
		if newCollector, err := cf.enableExpCollector(counters.DCGMExpClockEventsCount); err != nil {
			slog.Error(fmt.Sprintf("collector '%s' cannot be initialized; err: %v", counters.DCGMExpClockEventsCount, err))
			os.Exit(1)
		} else {
			entityCollectorTuples = append(entityCollectorTuples, EntityCollectorTuple{
				entity:    dcgm.FE_GPU,
				collector: newCollector,
			})
		}
	}

	if IsDCGMExpXIDErrorsCountEnabled(cf.counterSet.ExporterCounters) {
		if newCollector, err := cf.enableExpCollector(counters.DCGMExpXIDErrorsCount); err != nil {
			slog.Error(fmt.Sprintf("collector '%s' cannot be initialized; err: %v", counters.DCGMExpXIDErrorsCount, err))
			os.Exit(1)
		} else {
			entityCollectorTuples = append(entityCollectorTuples, EntityCollectorTuple{
				entity:    dcgm.FE_GPU,
				collector: newCollector,
			})
		}
	}

	if IsDCGMExpGPUHealthStatusEnabled(cf.counterSet.ExporterCounters) {
		if newCollector, err := cf.enableExpCollector(counters.DCGMExpGPUHealthStatus); err != nil {
			slog.Error(fmt.Sprintf("collector '%s' cannot be initialized; err: %v", counters.DCGMExpGPUHealthStatus, err))
			os.Exit(1)
		} else {
			entityCollectorTuples = append(entityCollectorTuples, EntityCollectorTuple{
				entity:    dcgm.FE_GPU,
				collector: newCollector,
			})
		}
	}

	return entityCollectorTuples
}

func (cf *collectorFactory) enableDCGMCollector(entityWatchList devicewatchlistmanager.WatchList) (Collector, error,
) {
	newCollector, err := NewDCGMCollector(cf.counterSet.DCGMCounters, cf.hostname, cf.config,
		entityWatchList)
	if err != nil {
		return nil, err
	}

	return newCollector, nil
}

func (cf *collectorFactory) enableExpCollector(expCollectorName string) (Collector, error) {
	entityType := dcgm.FE_GPU

	item, exists := cf.deviceWatchListManager.EntityWatchList(entityType)
	if !exists {
		return nil, fmt.Errorf("entity type '%s' does not exist", entityType.String())
	}

	var newCollector Collector
	var err error
	switch expCollectorName {
	case counters.DCGMExpClockEventsCount:
		newCollector, err = NewClockEventsCollector(cf.counterSet.ExporterCounters, cf.hostname, cf.config,
			item)
	case counters.DCGMExpXIDErrorsCount:
		newCollector, err = NewXIDCollector(cf.counterSet.ExporterCounters, cf.hostname, cf.config,
			item)
	case counters.DCGMExpGPUHealthStatus:
		newCollector, err = NewGPUHealthStatusCollector(cf.counterSet.ExporterCounters,
			cf.hostname,
			cf.config,
			item,
		)
	default:
		err = fmt.Errorf("invalid collector '%s'", expCollectorName)
	}

	if err != nil {
		return nil, err
	}

	slog.Info(fmt.Sprintf("collector '%s' initialized", expCollectorName))
	return newCollector, nil
}

// createHygonCollectors 创建海光卡收集器
func (cf *collectorFactory) createHygonCollectors() []EntityCollectorTuple {
	slog.Info("Creating Hygon DCU collectors")

	// 初始化海光卡提供者
	hygonprovider.Initialize()

	// 检查海光卡是否可用
	if !hygonprovider.Client().IsAvailable() {
		slog.Error("Hygon hy-smi tool is not available")
		os.Exit(1)
	}

	entityCollectorTuples := make([]EntityCollectorTuple, 0)

	// 创建海光卡收集器
	if len(cf.counterSet.DCGMCounters) > 0 {
		hygonCollector, err := cf.enableHygonCollector()
		if err != nil {
			slog.Error(fmt.Sprintf("Hygon collector cannot be initialized; err: %v", err))
			os.Exit(1)
		} else {
			entityCollectorTuples = append(entityCollectorTuples, EntityCollectorTuple{
				entity:    dcgm.FE_GPU, // 使用GPU实体类型作为海光DCU的映射
				collector: hygonCollector,
			})
		}
	}

	return entityCollectorTuples
}

// enableHygonCollector 启用海光卡收集器
func (cf *collectorFactory) enableHygonCollector() (Collector, error) {
	newCollector, err := NewHygonCollector(cf.counterSet.DCGMCounters, cf.hostname, cf.config)
	if err != nil {
		return nil, err
	}

	slog.Info("Hygon collector initialized")
	return newCollector, nil
}
