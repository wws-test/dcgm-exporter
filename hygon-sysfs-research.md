# 海光DCU原始数据源研究报告

## 研究背景
在开发海光DCU exporter的过程中，发现hy-smi工具输出的JSON格式存在问题（混合了非JSON文本），导致解析困难。因此决定研究hy-smi的原始数据来源，寻找更直接的数据获取方式。

## 发现的原始数据源

### 1. 设备文件系统
海光DCU在Linux系统中通过标准的DRM（Direct Rendering Manager）子系统暴露设备信息：

```bash
# DRI设备文件
/dev/dri/card0-7     # 8张海光DCU卡
/dev/dri/renderD128-135  # 对应的render节点

# KFD设备（Kernel Fusion Driver）
/dev/kfd             # 海光计算设备接口
```

### 2. sysfs文件系统路径
每张卡的详细信息都可以通过sysfs获取：

```bash
/sys/class/drm/card{N}/device/
```

### 3. 关键监控指标的sysfs路径

#### 基本设备信息
- **设备ID**: `/sys/class/drm/card{N}/device/device`
- **序列号**: `/sys/class/drm/card{N}/device/serial_number`
- **唯一ID**: `/sys/class/drm/card{N}/device/unique_id`
- **产品名称**: `/sys/class/drm/card{N}/device/product_name`
- **VBIOS版本**: `/sys/class/drm/card{N}/device/vbios_version`

#### 性能指标
- **GPU使用率**: `/sys/class/drm/card{N}/device/gpu_busy_percent` (%)
- **内存使用率**: `/sys/class/drm/card{N}/device/mem_busy_percent` (%)
- **平均功耗**: `/sys/class/drm/card{N}/device/chip_power_average` (mW)

#### 内存信息
- **VRAM总量**: `/sys/class/drm/card{N}/device/mem_info_vram_total` (bytes)
- **VRAM已用**: `/sys/class/drm/card{N}/device/mem_info_vram_used` (bytes)
- **可见VRAM总量**: `/sys/class/drm/card{N}/device/mem_info_vis_vram_total` (bytes)
- **可见VRAM已用**: `/sys/class/drm/card{N}/device/mem_info_vis_vram_used` (bytes)

#### 温度和功耗（通过hwmon子系统）
路径：`/sys/class/drm/card{N}/device/hwmon/hwmon{X}/`

- **温度传感器**:
  - `temp1_input`: edge温度 (毫摄氏度)
  - `temp2_input`: junction温度 (毫摄氏度)  
  - `temp3_input`: memory温度 (毫摄氏度)
  - `temp{N}_label`: 温度传感器标签

- **功耗信息**:
  - `power1_average`: 平均功耗 (微瓦)
  - `power1_cap`: 功耗上限 (微瓦)
  - `power1_cap_max`: 最大功耗上限 (微瓦)

- **风扇信息**:
  - `fan1_input`: 风扇转速 (RPM)
  - `pwm1`: PWM控制值

#### 性能模式
- **性能级别**: `/sys/class/drm/card{N}/device/power_dpm_force_performance_level`

### 4. 数据格式说明

#### 温度数据
- sysfs中的温度以毫摄氏度为单位 (例如: 57000 = 57°C)
- 需要除以1000转换为摄氏度

#### 功耗数据
- hwmon中的功耗以微瓦为单位 (例如: 356000000 = 356W)
- 需要除以1000000转换为瓦特

#### 内存数据
- 内存大小以字节为单位
- 使用率需要计算: (已用/总量) * 100

### 5. 实际测试数据示例

```bash
# card1的实时数据
$ cat /sys/class/drm/card1/device/gpu_busy_percent
100

$ cat /sys/class/drm/card1/device/mem_busy_percent  
39

$ cat /sys/class/drm/card1/device/chip_power_average
183

$ cat /sys/class/drm/card1/device/hwmon/hwmon3/temp1_input
57000

$ cat /sys/class/drm/card1/device/serial_number
TRFU340004050701
```

## 优势分析

### 使用sysfs的优势
1. **数据格式标准**: 每个文件包含单一数值，无需复杂解析
2. **实时性好**: 直接从内核获取，延迟最低
3. **稳定可靠**: 标准Linux接口，不依赖第三方工具
4. **性能高效**: 避免了调用外部命令的开销
5. **权限简单**: 大部分文件只需读权限

### 相比hy-smi的优势
1. **避免JSON解析问题**: hy-smi输出混合格式，解析困难
2. **减少依赖**: 不需要依赖hy-smi工具
3. **更好的错误处理**: 单个指标失败不影响其他指标
4. **更高的性能**: 直接文件读取比执行外部命令快

## 实现建议

基于以上发现，建议创建一个纯sysfs的海光DCU exporter：

1. 扫描`/sys/class/drm/card*`目录发现设备
2. 读取各个sysfs文件获取指标数据
3. 处理数据格式转换（温度、功耗单位转换）
4. 生成Prometheus格式的metrics

这种方式将大大简化代码复杂度，提高稳定性和性能。
