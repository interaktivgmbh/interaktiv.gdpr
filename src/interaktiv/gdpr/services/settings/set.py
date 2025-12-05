import json

import plone.protect.interfaces
from plone import api
from plone.restapi.services import Service
from zope.interface import alsoProvides

from interaktiv.gdpr import logger
from interaktiv.gdpr.deletion_info_helper import DeletionLogHelper
from interaktiv.gdpr.registry.deletion_log import IGDPRSettingsSchema
from interaktiv.gdpr.setuphandlers import create_marked_deletion_container


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

        if "marked_deletion_enabled" not in data:
            self.request.response.setStatus(400)
            return {
                "error": {
                    "type": "BadRequest",
                    "message": "marked_deletion_enabled is required",
                }
            }

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

        return {"status": "success", "marked_deletion_enabled": new_value}
