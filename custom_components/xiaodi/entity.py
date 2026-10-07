"""基础实体。"""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XiaodiCoordinator


class XiaodiEntity(CoordinatorEntity[XiaodiCoordinator]):
    """所有实体的基类。"""

    _attr_has_entity_name = True

    def __init__(self, coordinator: XiaodiCoordinator, lock_mac: str) -> None:
        super().__init__(coordinator)
        self._lock_mac = lock_mac

    @property
    def _lock(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._lock_mac, {})

    @property
    def _lock_info(self) -> dict[str, Any]:
        return self._lock.get("info", {})

    @property
    def device_info(self) -> DeviceInfo:
        info = self._lock_info
        return DeviceInfo(
            identifiers={(DOMAIN, self._lock_mac)},
            name=info.get("lockname") or f"小嘀门锁 {self._lock_mac}",
            manufacturer="德施曼 DESSMANN",
            model=info.get("lockname"),
            configuration_url="https://nyuwa-wx.dsmxp.com",
        )
