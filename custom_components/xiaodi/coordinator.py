"""数据协调器。"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntryAuthFailed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import XiaodiApi, XiaodiApiError, XiaodiAuthError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, EVENT_UNLOCK

_LOGGER = logging.getLogger(__name__)

_PERSON_RE = re.compile(r"【(.*?)】")
_FINGER_RE = re.compile(r"(左手|右手)?(拇指|食指|中指|无名指|小指)")


def parse_unlock(content: str | None, log_type: str | None) -> dict[str, str | None]:
    """从开锁记录文案里解析出 人 / 指纹 / 方式。"""
    content = content or ""
    person = None
    finger = None
    method = log_type
    m = _PERSON_RE.search(content)
    if m:
        person = m.group(1)
    m = _FINGER_RE.search(content)
    if m:
        finger = m.group(0)
    return {"person": person, "finger": finger, "method": method}


class XiaodiCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """轮询设备列表 + 开锁记录。"""

    def __init__(self, hass: HomeAssistant, api: XiaodiApi, lock_mac: str | None) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api
        self._lock_mac = lock_mac
        self._last_key: dict[str, str] = {}
        self._primed = False

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            locks = await self.api.async_get_locks()
        except XiaodiAuthError as err:
            # 交给 HA 触发重新认证流程
            raise ConfigEntryAuthFailed(str(err)) from err
        except XiaodiApiError as err:
            raise UpdateFailed(str(err)) from err

        if self._lock_mac:
            locks = [lk for lk in locks if lk.get("lockmac") == self._lock_mac]

        today = datetime.now().date().isoformat()
        result: dict[str, dict[str, Any]] = {}
        for lock in locks:
            mac = lock.get("lockmac")
            if not mac:
                continue
            info: dict[str, Any] = {
                "info": lock,
                "today_count": 0,
                "last": None,
            }
            try:
                days = await self.api.async_get_logs(mac)
            except XiaodiAuthError as err:
                raise ConfigEntryAuthFailed(str(err)) from err
            except XiaodiApiError as err:
                _LOGGER.warning("获取开锁记录失败(%s): %s", mac, err)
                days = []

            for day in days:
                if day.get("logDate") == today:
                    info["today_count"] = len(day.get("logDetails") or [])

            # 最近一次开锁：取第一条有明细的天
            for day in days:
                details = day.get("logDetails") or []
                if details:
                    d = details[0]
                    parsed = parse_unlock(d.get("content"), d.get("logType"))
                    info["last"] = {
                        "date": day.get("logDate"),
                        "time": d.get("logTime"),
                        "content": d.get("content"),
                        "log_type": d.get("logType"),
                        "log_type_int": d.get("logTypeInt"),
                        **parsed,
                    }
                    break

            # 检测「新的一次开锁」→ 发事件（用于自动化）
            last = info.get("last")
            if last:
                key = f"{last.get('date')} {last.get('time')} {last.get('content')}"
                if (
                    self._primed
                    and mac in self._last_key
                    and self._last_key[mac] != key
                ):
                    self.hass.bus.async_fire(
                        EVENT_UNLOCK,
                        {
                            "lock_mac": mac,
                            "lock_name": lock.get("lockname"),
                            "person": last.get("person"),
                            "finger": last.get("finger"),
                            "method": last.get("method"),
                            "date": last.get("date"),
                            "time": last.get("time"),
                            "content": last.get("content"),
                        },
                    )
                self._last_key[mac] = key
            result[mac] = info

        self._primed = True
        return result
