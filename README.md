# RunLucky 润莱软水机 · Home Assistant 集成

把润莱（润莱智联 / RunLucky）软水机接入 Home Assistant 的自定义集成。
通过官方云端 API 读取全部运行指标，并可执行再生、度假模式、压力设定以及写入全部设备参数。

> 本集成是根据官方 Android App（`com.runxin.runlucky`）逆向出的云端协议实现的，
> **非官方组件**，与润莱公司无关。

---

## 功能

| 类型 | 内容 |
|---|---|
| **传感器（按型号 14–33）** | 运行状态、瞬时流量、剩余制水量、今日/近7天日均用水量、剩余天数、各阶段倒计时（流程/暂停/溶盐/吸盐/反洗/盐箱补水）、再生次数、原水硬度、树脂量、工作模式、再生模式、设备型号、关闭原因；仅 RO 机型：RO 状态、RO/PAC 滤芯寿命、PAC/RO 累计制水时间；仅泳池机型：当前/设定水压；漏水检测 1–4（装了才建） |
| **二进制传感器（5–11）** | 缺盐提醒、缺盐报警、需换树脂、需换滤料、漏水报警、时钟芯片故障、存储器故障、多位置/无位置信号故障、智能巡检、度假模式 |
| **按钮（5–6）** | 立即再生、进入/退出度假模式、同步设备时钟、从设备拉取最新数据；仅 RO 机型多一个「RO 立即冲洗」 |
| **开关（1）** | 度假模式（开=进入，关=退出） |
| **数值（按型号 0–12）** | 原水硬度、加盐量、周期制水量、连续用水时间、流量关阀值、反洗间隔、滤料工作天数、最大再生间隔、运行天数、再生提醒次数、树脂量、冲洗次数增量 |
| **下拉选择（按型号 0–6）** | 吸盐模式（逆吸/顺吸）、12/24 小时制、设备语言、输出继电器模式、水量单位、工作模式 |
| **文本（按型号 0–6）** | 慢洗时间、吸盐慢洗时间、反洗时间、盐箱补水时间、快洗时间、再生触发时间（`HH:MM:SS`） |

### 实体按型号过滤（不会出现用不到的实体）

固件会在 `protocolData` 里报出**所有**子系统的字段，但字段存在不代表硬件存在——一台中央软水机
照样会报 `roStation`、`outletTds`。因此实体创建按官方 App 自己的判定逻辑过滤
（`chunk-12af5621` 里的 `isRo` / `isWaterPurifier` / `isSwimmingPool`）：

| 判定 | 型号 |
|---|---|
| `isRo`（RO 净水子系统） | `C600A`、`C800D` |
| `isWaterPurifier`（净水机） | `F67N`、`F67NA`、`F67D`、`F71D`、`F138`、`F139`、`F152` |
| `isSwimmingPool`（泳池阀） | `F138`、`F139`、`F152` |
| `F104HW` | 阀门机，只有 `f104Station` |

规则汇总：

- **RO / PAC 相关**（`roStation`、RO/PAC 滤芯寿命、PAC/RO 累计制水时间、RO 冲洗按钮）→ 仅 `isRo` 机型
- **水压**（`pressureValue`、`pressureSettingValue`）→ 仅 `isSwimmingPool` 机型
- **`f104Station`** → 仅 `F104HW`
- **TDS**（`inletTds`、`outletTds`）→ App 从不渲染，默认不建（实验性字段）
- **漏水检测 1–4** → 值为 `0`（未安装）时不建；装了传感器自动出现
- 可写实体（数值/下拉/文本）另按 `get-device-model-setting` 的 `true/false` 过滤——实测 F150 只允许写
  `rawWaterHardness / saltAddition / continuousWaterTime / flowRateOff / regeneratingTriggerTime / currentTime / vacationPattern`

如果想让这些实体重新出现（例如怀疑固件其实支持），在集成选项里打开
「显示本机用不到 / 未安装的实体」。该开关只恢复**设备确实上报**的字段，不会凭空造数据。

倒计时类字段设备返回 `"HH:MM:SS"` 字符串，集成会换算成秒（`duration` 设备类）。

---

## 安装

### HACS（推荐）

1. HACS → 集成 → 右上角 ⋮ → **自定义存储库**
2. 仓库地址填本仓库 URL，类别选 **Integration**
3. 安装后重启 Home Assistant

### 手动

把 `custom_components/runlucky/` 整个目录复制到 Home Assistant 的
`config/custom_components/runlucky/`，重启。

---

## 配置

设置 → 设备与服务 → 添加集成 → 搜索 **RunLucky Water Softener** → 输入
润莱智联 App 的账号（手机号或邮箱）与密码。

轮询间隔（默认 30 秒，最小 10 秒）在集成「配置」里的选项中调整。

### ⚠️ 安全提示

厂商接口 `api.admin-runxin.com` **只有 HTTP 明文**，443 端口未监听，
因此账号密码与令牌都以明文在网络上传输。集成会把密码保存在
`config/.storage/core.config_entries` 中以便自动续期。请自行评估风险；
如无法接受，可在首次登录后改用自带 token 的方式（见 `tools/runlucky_cli.py`）。

---

## 逆向出的云端接口（供参考/自行开发）

后端是 **ABP Framework + OpenIddict**，所有响应包裹为
`{"result": {...}, "success": true}`，列表为 `result.items`。

```
POST http://api.admin-runxin.com/connect/token
     grant_type=password & scope=RunLuckyIot & client_id=RunLuckyIot_App
     & username=<手机号/邮箱> & password=<密码>
  -> { access_token, expires_in, token_type, refresh_token? }

# 鉴权：Authorization: Bearer <access_token>

GET  /api/run-lucky/device/app/device-lookup/get-device-list
GET  /api/run-lucky/device/app/family/                          # 家庭列表
GET  /api/run-lucky/device/app/family-device/get-list-by-family-id?familyId=
GET  /api/run-lucky/device/app/device/get-device-with--data?id=<deviceId>
POST /api/run-lucky/device/app/device-control/query-device-info-return-result?id=<deviceId>
GET  /api/run-lucky/device/app/device-lookup/get-device-model-setting?deviceId=&model=&regenerationPattern=
POST /api/run-lucky/device/app/device-control/control-device?id=<deviceId>
     body: {"currentTime":"HH:mm:ss", "rawWaterHardness":300, ...}
POST /api/run-lucky/device/app/device-control/forced-regeneration?id=<deviceId>
POST /api/run-lucky/device/app/device-control/ro-forced-regeneration?id=<deviceId>
POST /api/run-lucky/device/app/device-control/change-vacation?id=<deviceId>
POST /api/run-lucky/device/app/device-control/exit-vacation?id=<deviceId>
POST /api/run-lucky/device/app/device-control/set-pressure-setting-value?id=<deviceId>
     body: {"pressureSettingValue": 0.3}
GET  /api/basic-data/app/profile
```

实时推送（SignalR，本集成未使用）：
`ws://api.admin-runxin.com/signalr-hubs/device-chang-content-type-message`

### 枚举字典

见 `custom_components/runlucky/const.py`，其中包含完整中文标签：

- `station` 运行状态 0–10（运行/反洗/吸盐/补水/正洗/关闭/溶盐/暂停1/暂停2/排空/循环）
- `deviceModel` 型号 0–23（F79/F150/F67N/…/C600A/C800D/F104HW/F149/F163/F151）
- `workPattern` 工作模式 0–9、`regenerationPattern` 0 流量型 / 1 时间型
- `waterVolumeUnit` 0 gal / 1 L / 2 m³
- `systemCloseReason` 0/1/257/513/769/1025

---

## 调试

```bash
export RUNLUCKY_USER=你的账号
export RUNLUCKY_PASS=你的密码
python tools/runlucky_cli.py login
python tools/runlucky_cli.py devices
python tools/runlucky_cli.py data <deviceId>
python tools/runlucky_cli.py control <deviceId> rawWaterHardness=300
python tools/runlucky_cli.py regen <deviceId>
python tools/runlucky_cli.py modelsetting <deviceId>     # 该型号可写项
python tools/runlucky_cli.py query <deviceId>            # 强制云端取实时数据
```

依赖：`pip install aiohttp`

其它开发脚本：

| 脚本 | 用途 |
|---|---|
| `tools/gen_translations.py` | 由 `const.py` 重新生成 `strings.json` 与三份翻译 |
| `tools/probe_live.py` | 探查 `get-device-model-setting` 参数差异、对比缓存与实时数据（需 `RUNLUCKY_DEVICE=<设备ID>`） |
| `tools/probe_entities.py` | 用真实云端数据实例化全部实体并打印值/单位/可写项 |
| `tests/test_api.py` | 离线 mock 云端，验证登录/刷新/解包/控制参数 |
| `tests/test_entities.py` | 用真实 HA 2026.2 API 实例化全部实体，验证单位/枚举/写入 payload |

测试运行方式：

```bash
python tests/test_api.py
HA_SRC=/path/to/homeassistant python tests/test_entities.py
```

---

## 实测记录

已在一台真实软水机（`deviceModel=1` → F150，`waterVolumeUnit=2` 即 m³）上验证：

- `/connect/token` 返回 `expires_in≈31535999`（一年），不下发 `refresh_token`，
  因此集成到期后会重新用账号密码登录
- `get-device-with--data` 返回 72 个 `protocolData` 字段，是**云端缓存**，
  设备约每 3 分钟上报一次，数据会有几分钟延迟；需要立刻同步请按「从设备读取数据」按钮
  （调用 `query-device-info-return-result`，会强制云端向设备取一次）
- 写入通路已验证：下发 `{"currentTime":"23:00:31"}` 后，设备实时查询返回
  `currentTime=23:00:00`，说明控制指令真实送达设备
- `get-device-model-setting` 的参数名是 `model`（不是 `deviceModel`），
  传错会得到 model 0 的配置（全部 false）

## 已知限制

- 仅云端轮询，没有局域网直连协议（设备通过厂商云中转，App 里也未开放局域网控制）
- 厂商接口为明文 HTTP
- 只读数据来自云端缓存，最长可能滞后几分钟
- 型号支持项差异：某些字段在你机器上可能不出现，属正常现象
- 未接入 SignalR 实时推送（`device-chang-content-type-message` / `message` 两个 hub 已定位，留作后续优化）

## License

MIT
