from typing import List

from plone import api
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from interaktiv.gdpr.deletion_info_helper import (
    DASHBOARD_DISPLAY_DAYS,
    DeletionLogHelper,
)
from interaktiv.gdpr.registry.deletion_log import IGDPRSettingsSchema, TDeletionLogEntry


class DeletionInfoDashboard(BrowserView):
    template = ViewPageTemplateFile("templates/deletion_info_dashboard.pt")

    def __call__(self) -> str:
        return self.template(self)

    @staticmethod
    def is_feature_enabled() -> bool:
        """Check if the marked deletion feature is enabled."""
        try:
            return api.portal.get_registry_record(
                name='marked_deletion_enabled',
                interface=IGDPRSettingsSchema
            )
        except (KeyError, api.exc.InvalidParameterError):
            return True

    @staticmethod
    def get_display_days() -> int:
        """Get the number of days for which entries are displayed."""
        return DASHBOARD_DISPLAY_DAYS

    @staticmethod
    def get_pending_entries() -> List[TDeletionLogEntry]:
        """Get all pending deletion entries."""
        return DeletionLogHelper.get_entries_by_status('pending')

    @staticmethod
    def get_deletion_log_for_display() -> List[TDeletionLogEntry]:
        """Get deletion log entries filtered by display days (90 days)."""
        return DeletionLogHelper.get_deletion_log_for_display()

    def get_pending_count(self) -> int:
        """Get count of pending entries."""
        return len(self.get_pending_entries())
