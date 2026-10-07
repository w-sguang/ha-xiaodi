"""传感器：最近开锁 / 最近开锁人 / 今日开锁次数。"""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
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
    for mac in coordinator.data:
        async_add_entities(
            [
                XiaodiLastUnlockSensor(coordinator, mac),
                XiaodiLastPersonSensor(coordinator, mac),
                XiaodiTodayCountSensor(coordinator, mac),
            ]
        )


class XiaodiLastUnlockSensor(XiaodiEntity, SensorEntity):
    """最近一次开锁（完整文案）。"""

    _attr_icon = "mdi:lock-clock"
    _attr_name = "最近开锁"

    def __init__(self, coordinator: XiaodiCoordinator, lock_mac: str) -> None:
        super().__init__(coordinator, lock_mac)
        self._attr_unique_id = f"{lock_mac}_last_unlock"

    @property
    def native_value(self) -> str | None:
        last = self._lock.get("last")
        return last.get("content") if last else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        last = self._lock.get("last") or {}
        return {
            "person": last.get("person"),
            "finger": last.get("finger"),
            "method": last.get("method"),
            "date": last.get("date"),
            "time": last.get("time"),
            "log_type": last.get("log_type"),
            "log_type_int": last.get("log_type_int"),
        }

    @property
    def available(self) -> bool:
        return super().available and self._lock.get("last") is not None


class XiaodiLastPersonSensor(XiaodiEntity, SensorEntity):
    """最近一次开锁的人（便于直接做触发条件）。"""

    _attr_icon = "mdi:account-key"
    _attr_name = "最近开锁人"

    def __init__(self, coordinator: XiaodiCoordinator, lock_mac: str) -> None:
        super().__init__(coordinator, lock_mac)
        self._attr_unique_id = f"{lock_mac}_last_person"

    @property
    def native_value(self) -> str | None:
        last = self._lock.get("last") or {}
        return last.get("person")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        last = self._lock.get("last") or {}
        return {"finger": last.get("finger"), "method": last.get("method")}


class XiaodiTodayCountSensor(XiaodiEntity, SensorEntity):
    """今日开锁次数。"""

    _attr_icon = "mdi:counter"
    _attr_name = "今日开锁次数"
    _attr_native_unit_of_measurement = "次"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: XiaodiCoordinator, lock_mac: str) -> None:
        super().__init__(coordinator, lock_mac)
        self._attr_unique_id = f"{lock_mac}_today_count"

    @property
    def native_value(self) -> int:
        return int(self._lock.get("today_count", 0))
