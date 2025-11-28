from datetime import datetime, timedelta

from plone import api
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from interaktiv.gdpr.deletion_info_helper import DeletionLogHelper
from interaktiv.gdpr.registry.deletion_log import IGDPRSettingsSchema, TDeletionLogEntry


class DashboardView(BrowserView):
    template = ViewPageTemplateFile("templates/dashboard.pt")

    def __call__(self) -> str:
        return self.template(self)

    def format_datetime(self, iso_datetime: str | None) -> str:
        """Format an ISO datetime string according to the current locale."""
        if not iso_datetime:
            return ""

        try:
            dt = datetime.fromisoformat(iso_datetime)
            # Get current language
            lang = self.request.get("LANGUAGE", "de")

            # Format based on locale
            if lang == "de":
                return dt.strftime("%d.%m.%Y %H:%M")
            else:
                return dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return iso_datetime

    def get_scheduled_deletion_date(self, iso_datetime: str | None) -> str:
        """Calculate the scheduled deletion date based on the entry datetime and retention days."""
        if not iso_datetime:
            return ""

        try:
            dt = datetime.fromisoformat(iso_datetime)
            scheduled_date = dt + timedelta(days=self.get_retention_days())
            # Get current language
            lang = self.request.get("LANGUAGE", "de")

            # Format based on locale
            if lang == "de":
                return scheduled_date.strftime("%d.%m.%Y")
            else:
                return scheduled_date.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return ""

    @staticmethod
    def get_retention_days() -> int:
        return DeletionLogHelper.get_retention_days()

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
        return DeletionLogHelper.get_dashboard_display_days()

    @staticmethod
    def get_pending_entries() -> list[TDeletionLogEntry]:
        return DeletionLogHelper.get_entries_by_status("pending")

    @staticmethod
    def get_deletion_log_for_display() -> list[TDeletionLogEntry]:
        return DeletionLogHelper.get_deletion_log_for_display()

    def get_pending_count(self) -> int:
        return len(self.get_pending_entries())
