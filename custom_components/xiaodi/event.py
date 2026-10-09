"""事件实体：每次检测到新开锁时触发（用于自动化触发）。

做成实体后，可在自动化可视化编辑器里直接选：
  触发器 → 「事件收到 (event.received)」→ 目标选本实体 → 事件类型选「开锁」。
"""
from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, EVENT_UNLOCK
from .coordinator import XiaodiCoordinator
from .entity import XiaodiEntity

# 事件类型（下拉里显示的名字）
EVENT_TYPE_UNLOCK = "开锁"


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: XiaodiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(XiaodiUnlockEvent(coordinator, mac) for mac in coordinator.data)


class XiaodiUnlockEvent(XiaodiEntity, EventEntity):
    """开锁事件实体：每次新开锁触发一次。

    触发后：
      - state = 触发时间（UTC 时间戳）
      - 属性  = event_type / person / finger / method / date / time / content
    """

    _attr_name = "开锁"
    _attr_icon = "mdi:lock-open-variant"
    _attr_event_types = [EVENT_TYPE_UNLOCK]

    def __init__(self, coordinator: XiaodiCoordinator, lock_mac: str) -> None:
        super().__init__(coordinator, lock_mac)
        self._attr_unique_id = f"{lock_mac}_unlock_event"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # 复用协调器抛出的 xiaodi_unlock 总线事件，避免重复一份「新开锁」判断逻辑
        self.async_on_remove(
            self.hass.bus.async_listen(EVENT_UNLOCK, self._handle_unlock_event)
        )

    @callback
    def _handle_unlock_event(self, event: Event) -> None:
        if event.data.get("lock_mac") != self._lock_mac:
            return
        self._trigger_event(
            EVENT_TYPE_UNLOCK,
            {
                "person": event.data.get("person"),
                "finger": event.data.get("finger"),
                "method": event.data.get("method"),
                "date": event.data.get("date"),
                "time": event.data.get("time"),
                "content": event.data.get("content"),
            },
        )
