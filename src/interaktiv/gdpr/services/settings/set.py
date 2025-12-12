import json
from typing import Any

import plone.protect.interfaces
from plone import api
from plone.dexterity.content import DexterityContent
from plone.restapi.services import Service
from zope.interface import alsoProvides
from zope.publisher.interfaces.browser import IBrowserRequest

from interaktiv.gdpr import create_marked_deletion_container, logger
from interaktiv.gdpr.deletion_log import DeletionLog
from interaktiv.gdpr.registry.deletion_log import IGDPRSettingsSchema


class GDPRSettingsSet(Service):

    VALID_SETTINGS = [
        "marked_deletion_enabled",
        "deletion_log_enabled",
        "retention_days",
        "display_days",
    ]

    def __init__(self, context: DexterityContent, request: IBrowserRequest) -> None:
        self.context = context
        self.request = request

    def _parse_request_data(self) -> dict[str, Any]:
        data = self.request.get("BODY", {})
        if isinstance(data, bytes):
            data = json.loads(data)
        return data

    def _validate_settings(self, data: dict[str, Any]) -> dict[str, Any] | None:
        if not any(setting in data for setting in self.VALID_SETTINGS):
            self.request.response.setStatus(400)
            return {
                "error": {
                    "type": "BadRequest",
                    "message": "At least one setting is required: "
                    "marked_deletion_enabled, deletion_log_enabled, retention_days, or display_days",
                }
            }
        return None

    def _handle_marked_deletion_enabled(
        self, data: dict[str, Any], result: dict[str, Any]
    ) -> dict[str, Any] | None:
        if "marked_deletion_enabled" not in data:
            return None

        new_value = bool(data["marked_deletion_enabled"])

        if not new_value:
            pending_entries = DeletionLog.get_entries_by_status("pending")
            if pending_entries:
                self.request.response.setStatus(409)
                return {
                    "error": {
                        "type": "Conflict",
                        "message": "Es sind noch ausstehende Löschungen aktiv. "
                        "Lösen Sie diese auf, um das Feature zu deaktivieren.",
                        "pending_count": len(pending_entries),
                    }
                }

        api.portal.set_registry_record(
            name="marked_deletion_enabled",
            interface=IGDPRSettingsSchema,
            value=new_value,
        )

        if new_value:
            create_marked_deletion_container()

        logger.info(
            f"GDPR marked deletion feature {'enabled' if new_value else 'disabled'}"
        )
        result["marked_deletion_enabled"] = new_value
        return None

    def _handle_deletion_log_enabled(
        self, data: dict[str, Any], result: dict[str, Any]
    ) -> None:
        if "deletion_log_enabled" not in data:
            return

        new_value = bool(data["deletion_log_enabled"])

        api.portal.set_registry_record(
            name="deletion_log_enabled",
            interface=IGDPRSettingsSchema,
            value=new_value,
        )

        logger.info(
            f"GDPR deletion log feature {'enabled' if new_value else 'disabled'}"
        )
        result["deletion_log_enabled"] = new_value

    def _handle_retention_days(
        self, data: dict[str, Any], result: dict[str, Any]
    ) -> dict[str, Any] | None:
        if "retention_days" not in data:
            return None

        try:
            retention_days = int(data["retention_days"])
            if retention_days < 1:
                raise ValueError("Must be at least 1")
        except (ValueError, TypeError):
            self.request.response.setStatus(400)
            return {
                "error": {
                    "type": "BadRequest",
                    "message": "retention_days must be a positive integer (minimum 1)",
                }
            }

        api.portal.set_registry_record(
            name="retention_days",
            interface=IGDPRSettingsSchema,
            value=retention_days,
        )
        logger.info(f"GDPR retention_days set to {retention_days}")
        result["retention_days"] = retention_days
        return None

    def _handle_display_days(
        self, data: dict[str, Any], result: dict[str, Any]
    ) -> dict[str, Any] | None:
        if "display_days" not in data:
            return None

        try:
            display_days = int(data["display_days"])
            if display_days < 1:
                raise ValueError("Must be at least 1")

        except (ValueError, TypeError):
            self.request.response.setStatus(400)
            return {
                "error": {
                    "type": "BadRequest",
                    "message": "display_days must be a positive integer (minimum 1)",
                }
            }

        api.portal.set_registry_record(
            name="display_days", interface=IGDPRSettingsSchema, value=display_days
        )
        logger.info(f"GDPR display_days set to {display_days}")
        result["display_days"] = display_days
        return None

    def reply(self) -> dict[str, Any]:
        if "IDisableCSRFProtection" in dir(plone.protect.interfaces):
            alsoProvides(self.request, plone.protect.interfaces.IDisableCSRFProtection)

        data = self._parse_request_data()

        if error := self._validate_settings(data):
            return error

        result: dict[str, Any] = {"status": "success"}

        if error := self._handle_marked_deletion_enabled(data, result):
            return error

        self._handle_deletion_log_enabled(data, result)

        if error := self._handle_retention_days(data, result):
            return error

        if error := self._handle_display_days(data, result):
            return error

        return result
