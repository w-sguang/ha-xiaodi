"""小嘀(德施曼) 门锁集成常量。"""
from __future__ import annotations

DOMAIN = "xiaodi"

CONF_SESSION_ID = "session_id"
CONF_LOCK_MAC = "lock_mac"

HOST = "https://nyuwa-wx.dsmxp.com"

# 每次新开锁时触发的 HA 事件（自动化触发用）
EVENT_UNLOCK = "xiaodi_unlock"

DEFAULT_SCAN_INTERVAL = 120  # 秒
