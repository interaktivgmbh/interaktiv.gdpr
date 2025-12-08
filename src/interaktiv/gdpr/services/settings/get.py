from plone import api
from plone.restapi.services import Service

from interaktiv.gdpr.deletion_log import DeletionLog
from interaktiv.gdpr.registry.deletion_log import IGDPRSettingsSchema


class GDPRSettingsGet(Service):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def reply(self):
        try:
            enabled = api.portal.get_registry_record(
                name="marked_deletion_enabled", interface=IGDPRSettingsSchema
            )
        except (KeyError, api.exc.InvalidParameterError):
            enabled = True

        # Count pending deletions
        pending_count = len(DeletionLog.get_entries_by_status("pending"))

        return {
            "marked_deletion_enabled": enabled,
            "pending_deletions_count": pending_count,
            "retention_days": DeletionLog.get_retention_days(),
            "display_days": DeletionLog.get_display_days(),
        }
