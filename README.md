# 小嘀 智能门锁 (德施曼) · Home Assistant 集成

把 **小嘀 / 德施曼** 智能门锁的**开锁记录**同步进 Home Assistant，并支持按
**谁、用什么指纹/方式**开锁来做自动化联动。

> ⚠️ **本集成是只读的，不能开锁。**
> 逆向确认：小嘀门锁的「开锁」走的是**蓝牙 (BLE)** —— 服务端只下发加密指令，
> 真正开门靠手机蓝牙连锁，**没有云端远程开锁接口**。

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

## 功能

- 设备列表 / 详情
- **开锁记录**（最近开锁、今日次数）
- 每次开锁触发 HA 事件 `xiaodi_unlock`（带 `person` / `finger` / `method`）
- sessionId 失效时自动提示「重新认证」

## 实体

| 实体 | 说明 |
|---|---|
| `sensor.<锁>_最近开锁` | 最近一次开锁完整文案（属性：`person`/`finger`/`method`/`time`）|
| `sensor.<锁>_最近开锁人` | 最近开锁的人（属性：`finger`/`method`）|
| `sensor.<锁>_今日开锁次数` | 今日开锁次数 |
| `binary_sensor.<锁>_今日有开锁` | 今日是否有人开锁 |

## 事件 `xiaodi_unlock`

每次检测到新开锁触发一次，`event_data`：

```json
{
  "lock_mac": "F8:AA:B3:48:CD:31",
  "lock_name": "小嘀Q2P",
  "person": "聪",
  "finger": "右手食指",
  "method": "指纹开门",
  "date": "2026-10-07",
  "time": "18:14",
  "content": "【聪】使用指纹 右手食指开锁"
}
```

### 自动化示例：按人联动

```yaml
alias: 有人开锁
trigger:
  - platform: event
    event_type: xiaodi_unlock
action:
  - choose:
      - conditions: "{{ trigger.event.data.person == '聪' }}"
        sequence:
          - service: light.turn_on
            target: { entity_id: light.keting }
      - conditions: "{{ trigger.event.data.person == '妈妈' }}"
        sequence:
          - service: notify.mobile_app_phone
            data:
              message: "妈妈用{{ trigger.event.data.method }}开门了（{{ trigger.event.data.time }}）"
mode: queued
```

按指纹分支：`condition: "{{ trigger.event.data.finger == '左手拇指' }}"`

## 安装（HACS 自定义仓库）

1. HACS → 右上角 ⋮ → **自定义仓库（Custom repositories）**
2. 仓库填 `w-sguang/ha-xiaodi`，类别选 **Integration**
3. 搜索「小嘀」安装 → **重启 Home Assistant**
4. 设置 → 设备与服务 → 添加集成 → 搜「小嘀」

> 或手动把 `custom_components/xiaodi/` 拷进 HA 的 `config/custom_components/`。

## 获取 sessionId（重要）

sessionId **只能在微信小程序登录后从抓包里拿**（登录强绑微信，无法自动登录）：

1. 用 Reqable / Charles / Proxyman 抓 `nyuwa-wx.dsmxp.com` 的流量
2. 在「小嘀」（德施曼）微信小程序里翻几下（列表 / 记录页）
3. 找任意请求，复制请求头里的 **`sessionId`**

> sessionId 会过期；失效后集成会弹出「重新认证」，重抓一次贴上即可。

## 限制

- ❌ **开锁**：BLE，未实现
- ❌ **电量 / 门磁状态**：接口未提供
- ⚠️ **登录自动化**：不可能（微信环境绑定），只能手动填 sessionId
- ⚠️ 轮询间隔默认 120 秒 → 开锁事件最坏有 ~2 分钟延迟（可在 `const.py` 调小）
- ⚠️ 开锁记录只有分钟精度，同一人同方式同一分钟内的两次开锁会被去重

## 免责声明

仅供个人学习与自用。使用者需自行确保遵守相关服务条款。

## License

MIT
