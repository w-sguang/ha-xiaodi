"""小嘀(德施曼) 门锁 API 封装。

只读接口：
  GET  /lock/list        设备列表
  GET  /lock/detail      设备详情
  POST /lock/log/listLog 开锁记录 (type=2)

鉴权：请求头 sessionId（微信小程序登录后由服务端响应头下发，会过期）。
"""
from __future__ import annotations

import logging
import time
from typing import Any, Mapping

import aiohttp

from .const import HOST

_LOGGER = logging.getLogger(__name__)

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 MicroMessenger miniProgram"
)

# 表示 sessionId 失效的业务码
_AUTH_CODES = {"400015", "400016"}


class XiaodiAuthError(Exception):
    """sessionId 失效，需要重新抓取。"""


class XiaodiApiError(Exception):
    """其它接口错误。"""


class XiaodiApi:
    def __init__(self, session: aiohttp.ClientSession, session_id: str) -> None:
        self._session = session
        self._session_id = session_id

    @property
    def session_id(self) -> str:
        return self._session_id

    def _headers(self, form: bool = False) -> dict[str, str]:
        headers = {
            "User-Agent": _UA,
            "sessionId": self._session_id,
            "xweb_xhr": "1",
            "Accept": "*/*",
            "Referer": "https://servicewechat.com/wx6b536f31a4363818/90/page-frame.html",
        }
        if form:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        form: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        url = f"{HOST}{path}"
        try:
            async with self._session.request(
                method,
                url,
                headers=self._headers(form is not None),
                data=form,
                params=params,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise XiaodiApiError(f"网络错误: {err}") from err
        except ValueError as err:  # 非 JSON
            raise XiaodiApiError(f"响应解析失败: {err}") from err

        code = str(data.get("code", ""))
        if code == "000000":
            return data.get("data")
        if code in _AUTH_CODES:
            raise XiaodiAuthError(f"sessionId 失效 (code={code})，请重新抓取")
        raise XiaodiApiError(f"接口错误 code={code} message={data.get('message')}")

    async def async_get_locks(self) -> list[dict[str, Any]]:
        """设备列表。"""
        data = await self._request(
            "GET", "/lock/list", params={"_t": int(time.time() * 1000)}
        )
        return list(data or [])

    async def async_get_detail(
        self, lock_id: str, device_type: int = 11
    ) -> dict[str, Any] | None:
        """设备详情。"""
        return await self._request(
            "GET",
            "/lock/detail",
            params={"lockId": lock_id, "deviceType": device_type},
        )

    async def async_get_logs(
        self,
        lock_mac: str,
        page: int = 1,
        size: int = 50,
        log_type: int = 2,
    ) -> list[dict[str, Any]]:
        """开锁记录（按天分组）。"""
        data = await self._request(
            "POST",
            "/lock/log/listLog",
            form={
                "lockMac": lock_mac,
                "pageNumber": page,
                "pageSize": size,
                "type": log_type,
            },
        )
        return list(data or [])
