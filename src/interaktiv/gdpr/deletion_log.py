from datetime import datetime, timedelta

from plone import api
from plone.dexterity.content import DexterityContent

from interaktiv.gdpr import logger
from interaktiv.gdpr.config import MARKED_FOR_DELETION_CONTAINER_ID
from interaktiv.gdpr.registry.deletion_log import (
    IDeletionLogSchema,
    IGDPRSettingsSchema,
    TDeletionLogEntry,
)


class DeletionLog:
    @staticmethod
    def get_deletion_log() -> list[TDeletionLogEntry]:
        """Get the complete deletion log from registry."""
        return (
            api.portal.get_registry_record(
                name="deletion_log", interface=IDeletionLogSchema
            )
            or []
        )

    @staticmethod
    def set_deletion_log(log: list[TDeletionLogEntry]) -> None:
        api.portal.set_registry_record(
            name="deletion_log", interface=IDeletionLogSchema, value=log
        )

    @staticmethod
    def get_display_days() -> int:
        # noinspection PyUnresolvedReferences
        try:
            return api.portal.get_registry_record(
                name="display_days", interface=IGDPRSettingsSchema
            )
        except (KeyError, api.exc.InvalidParameterError):
            return 90

    @staticmethod
    def get_retention_days() -> int:
        # noinspection PyUnresolvedReferences
        try:
            return api.portal.get_registry_record(
                name="retention_days", interface=IGDPRSettingsSchema
            )
        except (KeyError, api.exc.InvalidParameterError):
            return 30

    @classmethod
    def get_deletion_log_for_display(
        cls, days: int | None = None
    ) -> list[TDeletionLogEntry]:
        if days is None:
            days = cls.get_display_days()

        log = cls.get_deletion_log()
        cutoff_date = datetime.now() - timedelta(days=days)

        filtered_entries = []
        for entry in log:
            try:
                # Parse the datetime string
                entry_date = datetime.fromisoformat(entry.get("datetime", ""))
                if entry_date >= cutoff_date:
                    filtered_entries.append(entry)
            except (ValueError, TypeError):
                # If date parsing fails, include the entry anyway
                filtered_entries.append(entry)

        return filtered_entries

    @classmethod
    def add_entry(
        cls, obj: DexterityContent, status: str = "pending"
    ) -> TDeletionLogEntry | None:
        uid = obj.UID()
        log = cls.get_deletion_log()
        now = datetime.now().isoformat()
        current_user = api.user.get_current()
        user_id = current_user.getId() if current_user else "system"

        # Get review state
        try:
            review_state = api.content.get_state(obj)
        except Exception:
            review_state = ""

        # Count subobjects
        try:
            subobject_count = len(obj.objectIds()) if hasattr(obj, "objectIds") else 0
        except Exception:
            subobject_count = 0

        entry: TDeletionLogEntry = {
            "uid": uid,
            "datetime": now,
            "title": obj.title_or_id(),
            "portal_type": obj.portal_type,
            "original_path": "/".join(obj.getPhysicalPath()),
            "user_id": user_id,
            "subobject_count": subobject_count,
            "review_state": review_state,
            "status": status,
            "status_changed": now,
            "status_changed_by": user_id,
        }

        log.append(entry)
        cls.set_deletion_log(log)

        logger.info(
            f"Deletion log entry added:\n"
            f"  UID: {entry['uid']}\n"
            f"  Title: {entry['title']}\n"
            f"  Portal Type: {entry['portal_type']}\n"
            f"  Original Path: {entry['original_path']}\n"
            f"  User: {entry['user_id']}\n"
            f"  Subobject Count: {entry['subobject_count']}\n"
            f"  Review State: {entry['review_state']}\n"
            f"  Status: {entry['status']}"
        )

        return entry

    @classmethod
    def update_entry_status(cls, uid: str, new_status: str) -> TDeletionLogEntry | None:
        """Update the status of the most recent pending log entry."""
        log = cls.get_deletion_log()
        now = datetime.now().isoformat()
        current_user = api.user.get_current()
        user_id = current_user.getId() if current_user else "system"

        for entry in reversed(log):
            if entry["uid"] == uid and entry["status"] == "pending":
                old_status = entry["status"]
                entry["status"] = new_status
                entry["status_changed"] = now
                entry["status_changed_by"] = user_id
                cls.set_deletion_log(log)

                logger.info(
                    f"Deletion log entry status updated:\n"
                    f"  UID: {uid}\n"
                    f"  Title: {entry['title']}\n"
                    f"  Old Status: {old_status}\n"
                    f"  New Status: {new_status}\n"
                    f"  Changed by: {user_id}"
                )
                return entry

        return None

    @classmethod
    def get_entry_by_uid(cls, uid: str) -> TDeletionLogEntry | None:
        """Get a specific log entry by UID."""
        log = cls.get_deletion_log()
        for entry in log:
            if entry["uid"] == uid:
                return entry
        return None

    @classmethod
    def get_pending_entry_by_uid(cls, uid: str) -> TDeletionLogEntry | None:
        """Get the most recent pending log entry for a UID."""
        log = cls.get_deletion_log()
        for entry in reversed(log):
            if entry["uid"] == uid and entry["status"] == "pending":
                return entry
        return None

    @classmethod
    def get_entries_by_status(cls, status: str) -> list[TDeletionLogEntry]:
        """Get all log entries with a specific status."""
        log = cls.get_deletion_log()
        return [entry for entry in log if entry["status"] == status]

    @classmethod
    def get_pending_objects(cls) -> list[DexterityContent]:
        """Get all objects that are pending deletion from the container."""
        pending_entries = cls.get_entries_by_status("pending")
        objects = []

        for entry in pending_entries:
            obj = api.content.get(UID=entry["uid"])
            if obj is not None:
                objects.append(obj)

        return objects

    @classmethod
    def get_expired_pending_entries(cls) -> list[TDeletionLogEntry]:
        """Get all pending entries that have exceeded the retention period."""
        retention_days = cls.get_retention_days()
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        pending_entries = cls.get_entries_by_status("pending")

        expired_entries = []
        for entry in pending_entries:
            try:
                entry_date = datetime.fromisoformat(entry.get("datetime", ""))
                if entry_date < cutoff_date:
                    expired_entries.append(entry)
            except (ValueError, TypeError):
                # If date parsing fails, skip this entry
                logger.warning(f"Could not parse datetime for entry {entry.get('uid')}")

        return expired_entries

    @classmethod
    def run_scheduled_deletion(cls) -> int:
        """
        Run scheduled deletion for all pending items that have exceeded
        the retention period.

        This should be called by a cron job or scheduled task.

        Returns the number of successfully deleted items.
        """
        portal = api.portal.get()
        container = portal.get(MARKED_FOR_DELETION_CONTAINER_ID)

        if not container:
            logger.warning(
                "MarkedDeletionContainer not found, cannot run scheduled deletion"
            )
            return 0

        expired_entries = cls.get_expired_pending_entries()
        retention_days = cls.get_retention_days()

        if not expired_entries:
            logger.debug(
                f"No expired pending deletions found (retention period: {retention_days} days)"
            )
            return 0

        logger.info(
            f"Found {len(expired_entries)} expired pending deletions (retention period: {retention_days} days)"
        )

        deleted_count = 0
        for entry in expired_entries:
            uid = entry["uid"]
            obj = api.content.get(UID=uid)

            if obj is None:
                logger.warning(f"Object with UID {uid} not found, marking as deleted")
                cls.update_entry_status(uid, "deleted")
                deleted_count += 1
                continue

            # Check if object is in the deletion container
            obj_path = "/".join(obj.getPhysicalPath())
            container_path = "/".join(container.getPhysicalPath())

            if not obj_path.startswith(container_path):
                logger.warning(f"Object {uid} is not in deletion container, skipping")
                continue

            # Perform actual deletion
            try:
                obj_id = obj.getId()
                container.manage_delObjects([obj_id])

                logger.info(
                    f"Object permanently deleted:\n"
                    f"  UID: {uid}\n"
                    f"  Title: {entry['title']}\n"
                    f"  Original Path: {entry['original_path']}"
                )

                cls.update_entry_status(uid, "deleted")
                deleted_count += 1

            except Exception as e:
                logger.error(f"Error deleting object {uid}: {e}")

        logger.info(f"Scheduled deletion completed: {deleted_count} items deleted")
        return deleted_count
