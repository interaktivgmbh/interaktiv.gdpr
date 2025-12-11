from datetime import datetime, timedelta

from plone import api
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from interaktiv.gdpr.deletion_log import DeletionLog
from interaktiv.gdpr.registry.deletion_log import IGDPRSettingsSchema, TDeletionLogEntry


class ControlpanelView(BrowserView):
    template = ViewPageTemplateFile("templates/controlpanel.pt")

    def __call__(self) -> str:
        return self.template(self)

    def format_datetime(self, iso_datetime: str | None) -> str:
        if not iso_datetime:
            return ""

        try:
            dt = datetime.fromisoformat(iso_datetime)
            lang = self.request.get("LANGUAGE", "de")

            if lang == "de":
                return dt.strftime("%d.%m.%Y %H:%M")
            else:
                return dt.strftime("%Y-%m-%d %H:%M")

        except (ValueError, TypeError):
            return iso_datetime

    def get_scheduled_deletion_date(self, iso_datetime: str | None) -> str:
        if not iso_datetime:
            return ""

        try:
            dt = datetime.fromisoformat(iso_datetime)
            scheduled_date = dt + timedelta(days=self.get_retention_days())
            lang = self.request.get("LANGUAGE", "de")

            if lang == "de":
                return scheduled_date.strftime("%d.%m.%Y")
            else:
                return scheduled_date.strftime("%Y-%m-%d")

        except (ValueError, TypeError):
            return ""

    @staticmethod
    def get_retention_days() -> int:
        return DeletionLog.get_retention_days()

    @staticmethod
    def is_feature_enabled() -> bool:
        # noinspection PyUnresolvedReferences
        try:
            return api.portal.get_registry_record(
                name="marked_deletion_enabled", interface=IGDPRSettingsSchema
            )
        except (KeyError, api.exc.InvalidParameterError):
            return True

    @staticmethod
    def is_deletion_log_enabled() -> bool:
        return DeletionLog.is_deletion_log_enabled()

    @staticmethod
    def get_display_days() -> int:
        return DeletionLog.get_display_days()

    @staticmethod
    def get_pending_entries() -> list[TDeletionLogEntry]:
        return DeletionLog.get_entries_by_status("pending")

    @staticmethod
    def get_deletion_log_for_display() -> list[TDeletionLogEntry]:
        return DeletionLog.get_deletion_log_for_display()

    def get_pending_count(self) -> int:
        return len(self.get_pending_entries())

    @staticmethod
    def get_datatables_language_url() -> str:
        current_language = api.portal.get_current_language()

        if current_language == "de":
            return "https://cdn.datatables.net/plug-ins/1.10.21/i18n/German.json"

        return ""

    def can_view_deletion_info_settings(self) -> bool:
        return api.user.has_permission(
            "interaktiv.gdpr: View Deletion Info Settings", obj=self.context
        )
