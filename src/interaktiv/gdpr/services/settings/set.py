import json

import plone.protect.interfaces
from plone import api
from plone.restapi.services import Service
from zope.interface import alsoProvides

from interaktiv.gdpr import logger
from interaktiv.gdpr.deletion_info_helper import (
    DeletionLogHelper,
    create_marked_deletion_container,
)
from interaktiv.gdpr.registry.deletion_log import IGDPRSettingsSchema


class GDPRSettingsSet(Service):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def reply(self):
        # Disable CSRF protection
        if "IDisableCSRFProtection" in dir(plone.protect.interfaces):
            alsoProvides(self.request, plone.protect.interfaces.IDisableCSRFProtection)

        data = self.request.get("BODY", {})
        if isinstance(data, bytes):
            data = json.loads(data)

        # Check if at least one valid setting is provided
        valid_settings = [
            "marked_deletion_enabled",
            "retention_days",
            "dashboard_display_days",
        ]
        if not any(setting in data for setting in valid_settings):
            self.request.response.setStatus(400)
            return {
                "error": {
                    "type": "BadRequest",
                    "message": "At least one setting is required: "
                    "marked_deletion_enabled, retention_days, or dashboard_display_days",
                }
            }

        result = {"status": "success"}

        # Handle marked_deletion_enabled
        if "marked_deletion_enabled" in data:
            new_value = bool(data["marked_deletion_enabled"])

            # If trying to disable, check for pending deletions
            if not new_value:
                pending_entries = DeletionLogHelper.get_entries_by_status("pending")
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

            # Update registry
            api.portal.set_registry_record(
                name="marked_deletion_enabled",
                interface=IGDPRSettingsSchema,
                value=new_value,
            )

            # If enabling, ensure container exists
            if new_value:
                create_marked_deletion_container()

            logger.info(
                f"GDPR marked deletion feature {'enabled' if new_value else 'disabled'}"
            )
            result["marked_deletion_enabled"] = new_value

        # Handle retention_days
        if "retention_days" in data:
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

        # Handle dashboard_display_days
        if "dashboard_display_days" in data:
            try:
                display_days = int(data["dashboard_display_days"])
                if display_days < 1:
                    raise ValueError("Must be at least 1")
            except (ValueError, TypeError):
                self.request.response.setStatus(400)
                return {
                    "error": {
                        "type": "BadRequest",
                        "message": "dashboard_display_days must be a positive integer (minimum 1)",
                    }
                }

            api.portal.set_registry_record(
                name="dashboard_display_days",
                interface=IGDPRSettingsSchema,
                value=display_days,
            )
            logger.info(f"GDPR dashboard_display_days set to {display_days}")
            result["dashboard_display_days"] = display_days

        return result
