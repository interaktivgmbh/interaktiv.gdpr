import plone.protect.interfaces
from plone import api
from plone.restapi.services import Service
from zope.interface import alsoProvides, implementer
from zope.publisher.interfaces import IPublishTraverse

from interaktiv.gdpr import logger
from interaktiv.gdpr.config import MARKED_FOR_DELETION_CONTAINER_ID
from interaktiv.gdpr.deletion_info_helper import DeletionLogHelper


@implementer(IPublishTraverse)
class WithdrawDeletion(Service):
    """Service to withdraw a deletion request and restore the object to its original location."""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.uid = None

    def publishTraverse(self, request, name):
        self.uid = name
        return self

    def reply(self):
        # Disable CSRF protection
        if "IDisableCSRFProtection" in dir(plone.protect.interfaces):
            alsoProvides(self.request, plone.protect.interfaces.IDisableCSRFProtection)

        if not self.uid:
            self.request.response.setStatus(400)
            return {"error": {"type": "BadRequest", "message": "UID is required"}}

        # Get the pending log entry
        log_entry = DeletionLogHelper.get_pending_entry_by_uid(self.uid)
        if not log_entry:
            self.request.response.setStatus(404)
            return {
                "error": {
                    "type": "NotFound",
                    "message": f"No pending deletion log entry found for UID: {self.uid}",
                }
            }

        # Get the object from the marked deletion container
        portal = api.portal.get()
        container = portal.get(MARKED_FOR_DELETION_CONTAINER_ID)

        if not container:
            self.request.response.setStatus(500)
            return {
                "error": {
                    "type": "InternalError",
                    "message": "Marked deletion container not found",
                }
            }

        # Find the object by UID
        obj = api.content.get(UID=self.uid)
        if not obj:
            self.request.response.setStatus(404)
            return {
                "error": {
                    "type": "NotFound",
                    "message": f"Object with UID {self.uid} not found",
                }
            }

        # Get the original path and determine target location
        original_path = log_entry.get("original_path", "")
        path_parts = original_path.strip("/").split("/")

        if len(path_parts) < 2:
            self.request.response.setStatus(400)
            return {
                "error": {
                    "type": "BadRequest",
                    "message": f"Invalid original path: {original_path}",
                }
            }

        # The original parent path (without the object id at the end)
        original_parent_path = "/".join(path_parts[:-1])
        original_id = path_parts[-1]

        # Try to get the original parent container
        try:
            target_container = portal.restrictedTraverse(original_parent_path)
        except (KeyError, AttributeError):
            self.request.response.setStatus(404)
            return {
                "error": {
                    "type": "NotFound",
                    "message": f"Original parent container not found: /{original_parent_path}",
                }
            }

        # Check for name conflict
        if original_id in target_container.objectIds():
            self.request.response.setStatus(409)
            return {
                "error": {
                    "type": "Conflict",
                    "message": f'Name conflict: An object with id "{original_id}" '
                    f"already exists at /{original_parent_path}",
                }
            }

        # Move the object back to its original location
        try:
            # Cut from marked deletion container
            cookie = container.manage_cutObjects([obj.getId()])

            # Paste to original location
            target_container.manage_pasteObjects(cookie)

            # Rename if needed (in case the id changed)
            pasted_obj = target_container[obj.getId()]
            if pasted_obj.getId() != original_id:
                api.content.rename(obj=pasted_obj, new_id=original_id)

            # Update log entry status
            DeletionLogHelper.update_entry_status(self.uid, "withdrawn")

            logger.info(
                f"Withdrawal successful:\n"
                f"  UID: {self.uid}\n"
                f"  Title: {log_entry['title']}\n"
                f"  Restored to: /{original_parent_path}/{original_id}"
            )

            self.request.response.setStatus(200)
            return {
                "status": "success",
                "message": f'Object "{log_entry["title"]}" has been restored to its original location',
                "restored_path": f"/{original_parent_path}/{original_id}",
                "uid": self.uid,
            }

        except Exception as e:
            logger.error(f"Error during withdrawal: {e}")
            self.request.response.setStatus(500)
            return {
                "error": {
                    "type": "InternalError",
                    "message": f"Error restoring object: {str(e)}",
                }
            }


class DeletionLogGet(Service):
    """Service to get the deletion log."""

    def reply(self):
        log = DeletionLogHelper.get_deletion_log()

        # Add current location for pending items
        enriched_log = []
        for entry in log:
            enriched_entry = dict(entry)

            if entry["status"] == "pending":
                obj = api.content.get(UID=entry["uid"])
                if obj:
                    enriched_entry["current_path"] = "/".join(obj.getPhysicalPath())
                    enriched_entry["current_url"] = obj.absolute_url()

            enriched_log.append(enriched_entry)

        return {"items": enriched_log, "total": len(enriched_log)}


class GDPRSettingsGet(Service):
    """Service to get GDPR settings."""

    def reply(self):
        from interaktiv.gdpr.registry.deletion_log import IGDPRSettingsSchema

        try:
            enabled = api.portal.get_registry_record(
                name="marked_deletion_enabled", interface=IGDPRSettingsSchema
            )
        except (KeyError, api.exc.InvalidParameterError):
            enabled = True

        # Count pending deletions
        pending_count = len(DeletionLogHelper.get_entries_by_status("pending"))

        return {
            "marked_deletion_enabled": enabled,
            "pending_deletions_count": pending_count,
        }


@implementer(IPublishTraverse)
class PermanentDeletion(Service):
    """Service to permanently delete an object from the marked deletion container."""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.uid = None

    def publishTraverse(self, request, name):
        self.uid = name
        return self

    def reply(self):
        # Disable CSRF protection
        if "IDisableCSRFProtection" in dir(plone.protect.interfaces):
            alsoProvides(self.request, plone.protect.interfaces.IDisableCSRFProtection)

        if not self.uid:
            self.request.response.setStatus(400)
            return {"error": {"type": "BadRequest", "message": "UID is required"}}

        # Get the pending log entry
        log_entry = DeletionLogHelper.get_pending_entry_by_uid(self.uid)
        if not log_entry:
            self.request.response.setStatus(404)
            return {
                "error": {
                    "type": "NotFound",
                    "message": f"No pending deletion log entry found for UID: {self.uid}",
                }
            }

        # Find the object by UID
        obj = api.content.get(UID=self.uid)
        if not obj:
            self.request.response.setStatus(404)
            return {
                "error": {
                    "type": "NotFound",
                    "message": f"Object with UID {self.uid} not found",
                }
            }

        title = log_entry["title"]

        # Permanently delete the object
        try:
            api.content.delete(obj=obj, check_linkintegrity=False)

            # Update log entry status
            DeletionLogHelper.update_entry_status(self.uid, "deleted")

            logger.info(
                f"Permanent deletion successful:\n"
                f"  UID: {self.uid}\n"
                f"  Title: {title}"
            )

            self.request.response.setStatus(200)
            return {
                "status": "success",
                "message": f'Object "{title}" has been permanently deleted',
                "uid": self.uid,
            }

        except Exception as e:
            logger.error(f"Error during permanent deletion: {e}")
            self.request.response.setStatus(500)
            return {
                "error": {
                    "type": "InternalError",
                    "message": f"Error deleting object: {str(e)}",
                }
            }


class GDPRSettingsSet(Service):
    """Service to update GDPR settings."""

    def reply(self):
        # Disable CSRF protection
        if "IDisableCSRFProtection" in dir(plone.protect.interfaces):
            alsoProvides(self.request, plone.protect.interfaces.IDisableCSRFProtection)

        from interaktiv.gdpr.registry.deletion_log import IGDPRSettingsSchema
        from interaktiv.gdpr.setuphandlers import create_marked_deletion_container

        data = self.request.get("BODY", {})
        if isinstance(data, bytes):
            import json

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
