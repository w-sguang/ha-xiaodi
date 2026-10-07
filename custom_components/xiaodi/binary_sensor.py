"""二进制传感器：今日是否有人开锁。"""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import XiaodiCoordinator
from .entity import XiaodiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: XiaodiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        XiaodiOpenedTodayBinarySensor(coordinator, mac) for mac in coordinator.data
    )


class XiaodiOpenedTodayBinarySensor(XiaodiEntity, BinarySensorEntity):
    """今日是否有开锁记录。"""

    _attr_name = "今日有开锁"
    _attr_device_class = BinarySensorDeviceClass.DOOR
    _attr_icon = "mdi:door-open"

    def __init__(self, coordinator: XiaodiCoordinator, lock_mac: str) -> None:
        super().__init__(coordinator, lock_mac)
        self._attr_unique_id = f"{lock_mac}_opened_today"

    @property
    def is_on(self) -> bool:
        return int(self._lock.get("today_count", 0)) > 0
