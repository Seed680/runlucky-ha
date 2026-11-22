# Changelog

All notable changes to this integration are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-11-22

首个可用版本，已在真实设备（`deviceModel=1` → F150，水量单位 m³）上完成端到端验证。

### 新增

- 完整的异步云端客户端：OpenIddict password grant 登录、令牌缓存、
  到期自动重新登录、HTTP 401 单次重试、ABP `{success, result}` 响应解包
- `DataUpdateCoordinator` 轮询账户下所有设备（默认 30 秒，可在集成选项中改为 10–3600 秒）
- 33 个传感器：运行状态、瞬时流量、剩余制水量、今日 / 近 7 天日均用水量、
  各阶段倒计时（换算为秒）、RO 与 PAC 滤芯寿命、累计制水时间、再生次数、
  进 / 出水 TDS、原水硬度、树脂量、工作模式、再生模式、设备型号、
  漏水检测 1–4、阀门状态与关阀原因
- 11 个二进制传感器：缺盐提醒 / 缺盐报警、需换树脂、需换滤料、漏水、
  时钟芯片故障、存储故障、多工位 / 无工位信号故障、智能巡检、度假模式
- 6 个按钮：立即再生、RO 立即冲洗、进入 / 退出度假模式、同步设备时钟、
  从设备拉取实时数据
- 1 个开关：度假模式
- 12 个数值实体：原水硬度、加盐量、连续用水时间、流量关阀阈值、周期产水量、
  反洗间隔、滤料工作天数、最大再生间隔、运行天数、再生报警次数、树脂量、
  冲洗次数增量（按水量单位自动切换上限）
- 6 个下拉实体：吸盐方式、12/24 小时制、设备语言、输出继电器模式、
  水量单位、工作模式
- 6 个时间文本实体：再生启动 / 触发时间、吸盐慢洗、反洗、盐箱补水、正洗时间
  （`HH:MM:SS`，带正则校验）
- 中文（zh-Hans）与英文（en）全量翻译，含 `brand/` 图标

### 说明

- 只读实体按设备实际上报的 `protocolData` 字段动态创建，不做型号硬编码；
  可写实体按 `get-device-model-setting?model=&regenerationPattern=` 的结果过滤
- 倒计时字段设备返回 `"HH:MM:SS"` 字符串，集成换算为秒并使用 `duration` 设备类
- 数值实体的上限不会低于设备当前值（例如 `resinVolume` 报 200 而 App 只允许 1–75）

### 已知限制

- 只读数据来自厂商云端缓存，可能滞后数分钟；按钮「从设备读取数据」可强制同步
- 厂商接口仅提供明文 HTTP（`api.admin-runxin.com` 未监听 443），
  账号密码与令牌以明文传输，集成会把密码保存在 `config/.storage/core.config_entries`
  中以便重新登录（`/connect/token` 不下发 `refresh_token`）
- 未接入 SignalR 实时推送
- 仅云端控制，无局域网直连协议

## [0.1.0] - 2026-11-22

- 内部开发版本：完成协议逆向、脚手架与离线测试，未对外发布
