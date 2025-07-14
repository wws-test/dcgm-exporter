package main

import (
	"flag"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/sirupsen/logrus"
)

// 版本信息，通过编译时注入
var (
	Version   = "dev"
	BuildTime = "unknown"
	GoVersion = "unknown"
)

// HygonDevice 海光设备信息
type HygonDevice struct {
	CardID       int
	SerialNumber string
	UniqueID     string
	ProductName  string
	VBIOSVersion string
	SysfsPath    string
	HwmonPath    string
}

// HygonSysfsCollector 基于sysfs的海光卡收集器
type HygonSysfsCollector struct {
	devices []HygonDevice

	// Prometheus指标
	temperature *prometheus.GaugeVec
	avgPower    *prometheus.GaugeVec
	powerCap    *prometheus.GaugeVec
	vramUsage   *prometheus.GaugeVec
	vramTotal   *prometheus.GaugeVec
	dcuUsage    *prometheus.GaugeVec
	memUsage    *prometheus.GaugeVec
	fanSpeed    *prometheus.GaugeVec
	deviceInfo  *prometheus.GaugeVec
}

// NewHygonSysfsCollector 创建基于sysfs的海光卡收集器
func NewHygonSysfsCollector() *HygonSysfsCollector {
	collector := &HygonSysfsCollector{
		temperature: prometheus.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "hygon_temperature_celsius",
				Help: "DCU temperature in Celsius.",
			},
			[]string{"gpu", "uuid", "device", "serial", "hostname", "sensor"},
		),
		avgPower: prometheus.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "hygon_power_watts",
				Help: "Average power consumption in Watts.",
			},
			[]string{"gpu", "uuid", "device", "serial", "hostname"},
		),
		powerCap: prometheus.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "hygon_power_cap_watts",
				Help: "Power cap limit in Watts.",
			},
			[]string{"gpu", "uuid", "device", "serial", "hostname"},
		),
		vramUsage: prometheus.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "hygon_vram_usage_bytes",
				Help: "VRAM usage in bytes.",
			},
			[]string{"gpu", "uuid", "device", "serial", "hostname"},
		),
		vramTotal: prometheus.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "hygon_vram_total_bytes",
				Help: "Total VRAM in bytes.",
			},
			[]string{"gpu", "uuid", "device", "serial", "hostname"},
		),
		dcuUsage: prometheus.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "hygon_dcu_utilization_percent",
				Help: "DCU utilization percentage.",
			},
			[]string{"gpu", "uuid", "device", "serial", "hostname"},
		),
		memUsage: prometheus.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "hygon_memory_utilization_percent",
				Help: "Memory utilization percentage.",
			},
			[]string{"gpu", "uuid", "device", "serial", "hostname"},
		),
		fanSpeed: prometheus.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "hygon_fan_speed_rpm",
				Help: "Fan speed in RPM.",
			},
			[]string{"gpu", "uuid", "device", "serial", "hostname"},
		),
		deviceInfo: prometheus.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "hygon_device_info",
				Help: "Device information (always 1).",
			},
			[]string{"gpu", "uuid", "device", "serial", "hostname", "vbios_version"},
		),
	}

	// 发现设备
	collector.discoverDevices()
	return collector
}

// discoverDevices 发现海光DCU设备
func (c *HygonSysfsCollector) discoverDevices() {
	drmPath := "/sys/class/drm"
	entries, err := os.ReadDir(drmPath)
	if err != nil {
		logrus.Errorf("Failed to read DRM directory: %v", err)
		return
	}

	for _, entry := range entries {
		if !strings.HasPrefix(entry.Name(), "card") || strings.Contains(entry.Name(), "-") {
			continue
		}

		cardPath := filepath.Join(drmPath, entry.Name(), "device")
		if _, err := os.Stat(cardPath); os.IsNotExist(err) {
			continue
		}

		// 检查是否是海光设备
		vendorPath := filepath.Join(cardPath, "vendor")
		if vendor := c.readSysfsFile(vendorPath); vendor != "0x1e83" {
			continue // 不是海光设备
		}

		cardID, _ := strconv.Atoi(strings.TrimPrefix(entry.Name(), "card"))
		device := HygonDevice{
			CardID:       cardID,
			SerialNumber: c.readSysfsFile(filepath.Join(cardPath, "serial_number")),
			UniqueID:     c.readSysfsFile(filepath.Join(cardPath, "unique_id")),
			ProductName:  c.readSysfsFile(filepath.Join(cardPath, "product_name")),
			VBIOSVersion: c.readSysfsFile(filepath.Join(cardPath, "vbios_version")),
			SysfsPath:    cardPath,
		}

		// 查找hwmon路径
		hwmonDir := filepath.Join(cardPath, "hwmon")
		if hwmonEntries, err := os.ReadDir(hwmonDir); err == nil && len(hwmonEntries) > 0 {
			device.HwmonPath = filepath.Join(hwmonDir, hwmonEntries[0].Name())
		}

		c.devices = append(c.devices, device)
		logrus.Infof("Discovered Hygon DCU: card%d, serial=%s", cardID, device.SerialNumber)
	}
}

// readSysfsFile 读取sysfs文件内容
func (c *HygonSysfsCollector) readSysfsFile(path string) string {
	data, err := os.ReadFile(path)
	if err != nil {
		logrus.Warnf("Failed to read %s: %v", path, err)
		return ""
	}
	return strings.TrimSpace(string(data))
}

// readSysfsFloat 读取sysfs文件并转换为float64
func (c *HygonSysfsCollector) readSysfsFloat(path string) float64 {
	str := c.readSysfsFile(path)
	if str == "" {
		return 0
	}
	val, err := strconv.ParseFloat(str, 64)
	if err != nil {
		logrus.Warnf("Failed to parse float from %s (value: %s): %v", path, str, err)
		return 0
	}
	return val
}

// Describe 实现prometheus.Collector接口
func (c *HygonSysfsCollector) Describe(ch chan<- *prometheus.Desc) {
	c.temperature.Describe(ch)
	c.avgPower.Describe(ch)
	c.powerCap.Describe(ch)
	c.vramUsage.Describe(ch)
	c.vramTotal.Describe(ch)
	c.dcuUsage.Describe(ch)
	c.memUsage.Describe(ch)
	c.fanSpeed.Describe(ch)
	c.deviceInfo.Describe(ch)
}

// Collect 实现prometheus.Collector接口
func (c *HygonSysfsCollector) Collect(ch chan<- prometheus.Metric) {
	hostname, _ := os.Hostname()
	if hostname == "" {
		hostname = "localhost"
	}

	for _, device := range c.devices {
		labels := []string{
			fmt.Sprintf("%d", device.CardID),
			device.UniqueID,
			fmt.Sprintf("hygon%d", device.CardID),
			device.SerialNumber,
			hostname,
		}

		// DCU使用率
		dcuUsage := c.readSysfsFloat(filepath.Join(device.SysfsPath, "gpu_busy_percent"))
		c.dcuUsage.WithLabelValues(labels...).Set(dcuUsage)

		// 内存使用率
		memUsage := c.readSysfsFloat(filepath.Join(device.SysfsPath, "mem_busy_percent"))
		c.memUsage.WithLabelValues(labels...).Set(memUsage)

		// VRAM信息
		vramTotal := c.readSysfsFloat(filepath.Join(device.SysfsPath, "mem_info_vram_total"))
		vramUsed := c.readSysfsFloat(filepath.Join(device.SysfsPath, "mem_info_vram_used"))
		c.vramTotal.WithLabelValues(labels...).Set(vramTotal)
		c.vramUsage.WithLabelValues(labels...).Set(vramUsed)

		// 功耗信息（从chip_power_average，单位是mW）
		chipPower := c.readSysfsFloat(filepath.Join(device.SysfsPath, "chip_power_average"))
		c.avgPower.WithLabelValues(labels...).Set(chipPower / 1000) // 转换为W

		// hwmon信息
		if device.HwmonPath != "" {
			// 温度信息
			tempSensors := []string{"temp1_input", "temp2_input", "temp3_input"}
			tempLabels := []string{"edge", "junction", "memory"}

			for i, tempFile := range tempSensors {
				tempPath := filepath.Join(device.HwmonPath, tempFile)
				if temp := c.readSysfsFloat(tempPath); temp > 0 {
					tempLabelsWithSensor := append(labels, tempLabels[i])
					c.temperature.WithLabelValues(tempLabelsWithSensor...).Set(temp / 1000) // 转换为摄氏度
				}
			}

			// 功耗上限（微瓦转瓦特）
			powerCap := c.readSysfsFloat(filepath.Join(device.HwmonPath, "power1_cap"))
			if powerCap > 0 {
				c.powerCap.WithLabelValues(labels...).Set(powerCap / 1000000)
			}

			// 风扇转速
			fanSpeed := c.readSysfsFloat(filepath.Join(device.HwmonPath, "fan1_input"))
			c.fanSpeed.WithLabelValues(labels...).Set(fanSpeed)
		}

		// 设备信息
		deviceInfoLabels := append(labels, device.VBIOSVersion)
		c.deviceInfo.WithLabelValues(deviceInfoLabels...).Set(1.0)
	}

	// 收集所有指标
	c.temperature.Collect(ch)
	c.avgPower.Collect(ch)
	c.powerCap.Collect(ch)
	c.vramUsage.Collect(ch)
	c.vramTotal.Collect(ch)
	c.dcuUsage.Collect(ch)
	c.memUsage.Collect(ch)
	c.fanSpeed.Collect(ch)
	c.deviceInfo.Collect(ch)
}

func main() {
	var (
		listenAddress = flag.String("web.listen-address", ":9400", "Address to listen on for web interface and telemetry.")
		showVersion   = flag.Bool("version", false, "Show version information and exit.")
	)
	flag.Parse()

	// 显示版本信息
	if *showVersion {
		fmt.Printf("Hygon DCU Exporter\n")
		fmt.Printf("Version: %s\n", Version)
		fmt.Printf("Build Time: %s\n", BuildTime)
		fmt.Printf("Go Version: %s\n", GoVersion)
		return
	}

	// 创建海光卡收集器
	collector := NewHygonSysfsCollector()

	// 注册收集器
	prometheus.MustRegister(collector)

	// 设置HTTP路由
	router := mux.NewRouter()
	router.Handle("/metrics", promhttp.Handler())
	router.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		w.Write([]byte(`<html>
<head><title>Hygon DCU Sysfs Exporter</title></head>
<body>
<h1>Hygon DCU Sysfs Exporter</h1>
<p><a href="/metrics">Metrics</a></p>
<p>Discovered devices: ` + fmt.Sprintf("%d", len(collector.devices)) + `</p>
<hr>
<p>Version: ` + Version + `</p>
<p>Build Time: ` + BuildTime + `</p>
<p>Go Version: ` + GoVersion + `</p>
</body>
</html>`))
	})

	// 启动HTTP服务器
	logrus.Infof("Starting Hygon DCU Sysfs Exporter on %s", *listenAddress)
	logrus.Infof("Discovered %d Hygon DCU devices", len(collector.devices))

	server := &http.Server{
		Addr:         *listenAddress,
		Handler:      router,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}

	logrus.Fatal(server.ListenAndServe())
}
