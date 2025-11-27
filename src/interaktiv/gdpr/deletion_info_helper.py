from datetime import datetime, timedelta
from typing import List, Optional

from plone import api
from plone.dexterity.content import DexterityContent

from interaktiv.gdpr import logger
from interaktiv.gdpr.config import MARKED_FOR_DELETION_CONTAINER_ID
from interaktiv.gdpr.registry.deletion_log import IDeletionLogSchema, TDeletionLogEntry

# Number of days to display entries on the dashboard
DASHBOARD_DISPLAY_DAYS = 90


class DeletionLogHelper:
    """Helper class for managing the deletion log in the registry."""

    @staticmethod
    def get_deletion_log() -> List[TDeletionLogEntry]:
        """Get the complete deletion log from registry."""
        return api.portal.get_registry_record(
            name='deletion_log',
            interface=IDeletionLogSchema
        ) or []

    @staticmethod
    def set_deletion_log(log: List[TDeletionLogEntry]) -> None:
        """Set the deletion log in registry."""
        api.portal.set_registry_record(
            name='deletion_log',
            interface=IDeletionLogSchema,
            value=log
        )

    @classmethod
    def get_deletion_log_for_display(cls, days: int = DASHBOARD_DISPLAY_DAYS) -> List[TDeletionLogEntry]:
        """Get deletion log entries from the last N days for dashboard display."""
        log = cls.get_deletion_log()
        cutoff_date = datetime.now() - timedelta(days=days)

        filtered_entries = []
        for entry in log:
            try:
                # Parse the datetime string
                entry_date = datetime.fromisoformat(entry.get('datetime', ''))
                if entry_date >= cutoff_date:
                    filtered_entries.append(entry)
            except (ValueError, TypeError):
                # If date parsing fails, include the entry anyway
                filtered_entries.append(entry)

        return filtered_entries

    @classmethod
    def add_entry(cls, obj: DexterityContent, status: str = 'pending') -> TDeletionLogEntry:
        """Add a new entry to the deletion log."""
        log = cls.get_deletion_log()
        now = datetime.now().isoformat()
        current_user = api.user.get_current()
        user_id = current_user.getId() if current_user else 'system'

        # Get review state
        try:
            review_state = api.content.get_state(obj)
        except Exception:
            review_state = ''

        # Count subobjects
        try:
            subobject_count = len(obj.objectIds()) if hasattr(obj, 'objectIds') else 0
        except Exception:
            subobject_count = 0

        entry: TDeletionLogEntry = {
            'uid': obj.UID(),
            'datetime': now,
            'title': obj.title_or_id(),
            'portal_type': obj.portal_type,
            'original_path': '/'.join(obj.getPhysicalPath()),
            'user_id': user_id,
            'subobject_count': subobject_count,
            'review_state': review_state,
            'status': status,
            'status_changed': now,
            'status_changed_by': user_id
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
    def update_entry_status(cls, uid: str, new_status: str) -> Optional[TDeletionLogEntry]:
        """Update the status of an existing log entry."""
        log = cls.get_deletion_log()
        now = datetime.now().isoformat()
        current_user = api.user.get_current()
        user_id = current_user.getId() if current_user else 'system'

        for entry in log:
            if entry['uid'] == uid:
                old_status = entry['status']
                entry['status'] = new_status
                entry['status_changed'] = now
                entry['status_changed_by'] = user_id
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
    def get_entry_by_uid(cls, uid: str) -> Optional[TDeletionLogEntry]:
        """Get a specific log entry by UID."""
        log = cls.get_deletion_log()
        for entry in log:
            if entry['uid'] == uid:
                return entry
        return None

    @classmethod
    def get_entries_by_status(cls, status: str) -> List[TDeletionLogEntry]:
        """Get all log entries with a specific status."""
        log = cls.get_deletion_log()
        return [entry for entry in log if entry['status'] == status]

    @classmethod
    def get_pending_objects(cls) -> List[DexterityContent]:
        """Get all objects that are pending deletion from the container."""
        pending_entries = cls.get_entries_by_status('pending')
        objects = []

        for entry in pending_entries:
            obj = api.content.get(UID=entry['uid'])
            if obj is not None:
                objects.append(obj)

        return objects

    @classmethod
    def run_scheduled_deletion(cls) -> None:
        """
        Run scheduled deletion for all pending items.
        This should be called by a cron job or scheduled task.
        """
        portal = api.portal.get()
        container = portal.get(MARKED_FOR_DELETION_CONTAINER_ID)

        if not container:
            logger.warning("MarkedDeletionContainer not found, cannot run scheduled deletion")
            return

        pending_entries = cls.get_entries_by_status('pending')

        for entry in pending_entries:
            uid = entry['uid']
            obj = api.content.get(UID=uid)

            if obj is None:
                # Object no longer exists, mark as deleted
                logger.warning(f"Object with UID {uid} not found, marking as deleted")
                cls.update_entry_status(uid, 'deleted')
                continue

            # Check if object is in the deletion container
            obj_path = '/'.join(obj.getPhysicalPath())
            container_path = '/'.join(container.getPhysicalPath())

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

                cls.update_entry_status(uid, 'deleted')

            except Exception as e:
                logger.error(f"Error deleting object {uid}: {e}")
