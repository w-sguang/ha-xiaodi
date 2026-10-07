"""配置流程。"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import XiaodiApi, XiaodiApiError, XiaodiAuthError
from .const import CONF_LOCK_MAC, CONF_SESSION_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)


class XiaodiConfigFlow(ConfigFlow, domain=DOMAIN):
    """处理 UI 配置。"""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            session_id = user_input[CONF_SESSION_ID].strip()
            lock_mac = (user_input.get(CONF_LOCK_MAC) or "").strip().upper()

            session = async_get_clientsession(self.hass)
            api = XiaodiApi(session, session_id)
            try:
                locks = await api.async_get_locks()
            except XiaodiAuthError:
                errors["base"] = "auth"
            except XiaodiApiError as err:
                _LOGGER.error("连接失败: %s", err)
                errors["base"] = "cannot_connect"
            else:
                if lock_mac and all(lk.get("lockmac") != lock_mac for lk in locks):
                    errors["base"] = "lock_not_found"
                else:
                    await self.async_set_unique_id(lock_mac or "all")
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title="小嘀 门锁" + (f" {lock_mac}" if lock_mac else ""),
                        data={
                            CONF_SESSION_ID: session_id,
                            CONF_LOCK_MAC: lock_mac,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SESSION_ID): str,
                    vol.Optional(CONF_LOCK_MAC, default=""): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if user_input is not None:
            session_id = user_input[CONF_SESSION_ID].strip()
            session = async_get_clientsession(self.hass)
            api = XiaodiApi(session, session_id)
            try:
                await api.async_get_locks()
            except XiaodiAuthError:
                errors["base"] = "auth"
            except XiaodiApiError:
                errors["base"] = "cannot_connect"
            else:
                self.hass.config_entries.async_update_entry(
                    entry, data={**entry.data, CONF_SESSION_ID: session_id}
                )
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_SESSION_ID): str}),
            errors=errors,
            description_placeholders={"lock": entry.title if entry else ""},
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return XiaodiOptionsFlow(entry)


class XiaodiOptionsFlow(OptionsFlow):
    """选项：更新 sessionId / lockMac。"""

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            session_id = user_input[CONF_SESSION_ID].strip()
            lock_mac = (user_input.get(CONF_LOCK_MAC) or "").strip().upper()
            session = async_get_clientsession(self.hass)
            api = XiaodiApi(session, session_id)
            try:
                locks = await api.async_get_locks()
            except XiaodiAuthError:
                errors["base"] = "auth"
            except XiaodiApiError:
                errors["base"] = "cannot_connect"
            else:
                if lock_mac and all(lk.get("lockmac") != lock_mac for lk in locks):
                    errors["base"] = "lock_not_found"
                else:
                    self.hass.config_entries.async_update_entry(
                        self._entry,
                        data={
                            CONF_SESSION_ID: session_id,
                            CONF_LOCK_MAC: lock_mac,
                        },
                    )
                    return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SESSION_ID,
                        default=self._entry.data.get(CONF_SESSION_ID, ""),
                    ): str,
                    vol.Optional(
                        CONF_LOCK_MAC,
                        default=self._entry.data.get(CONF_LOCK_MAC, ""),
                    ): str,
                }
            ),
            errors=errors,
        )
