from plone import api
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from interaktiv.gdpr.config import DASHBOARD_DISPLAY_DAYS
from interaktiv.gdpr.deletion_info_helper import DeletionLogHelper
from interaktiv.gdpr.registry.deletion_log import IGDPRSettingsSchema, TDeletionLogEntry


class DashboardView(BrowserView):
    template = ViewPageTemplateFile("templates/dashboard.pt")

    def __call__(self) -> str:
        return self.template(self)

    @staticmethod
    def is_feature_enabled() -> bool:
        try:
            return api.portal.get_registry_record(
                name="marked_deletion_enabled", interface=IGDPRSettingsSchema
            )
        except (KeyError, api.exc.InvalidParameterError):
            return True

    @staticmethod
    def get_display_days() -> int:
        return DASHBOARD_DISPLAY_DAYS

    @staticmethod
    def get_pending_entries() -> list[TDeletionLogEntry]:
        return DeletionLogHelper.get_entries_by_status("pending")

    @staticmethod
    def get_deletion_log_for_display() -> list[TDeletionLogEntry]:
        return DeletionLogHelper.get_deletion_log_for_display()

    def get_pending_count(self) -> int:
        return len(self.get_pending_entries())
