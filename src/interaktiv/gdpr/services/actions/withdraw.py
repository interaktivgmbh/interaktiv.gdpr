import plone.protect.interfaces
from plone import api
from plone.restapi.services import Service
from zope.i18n import translate
from zope.interface import alsoProvides, implementer
from zope.publisher.interfaces import IPublishTraverse

from interaktiv.gdpr import _, logger
from interaktiv.gdpr.config import MARKED_FOR_DELETION_CONTAINER_ID
from interaktiv.gdpr.deletion_log import DeletionLog


@implementer(IPublishTraverse)
class WithdrawDeletion(Service):
    def __init__(self, context, request):
        self.context = context
        self.request = request
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
            return {"error": {"type": "BadRequest", "message": translate(_("UID is required"), context=self.request)}}

        # Get the pending log entry
        log_entry = DeletionLog.get_pending_entry_by_uid(self.uid)
        if not log_entry:
            self.request.response.setStatus(404)
            return {
                "error": {
                    "type": "NotFound",
                    "message": translate(
                        _("No pending deletion log entry found for UID: ${uid}", mapping={"uid": self.uid}),
                        context=self.request,
                    ),
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
                    "message": translate(_("Marked deletion container not found"), context=self.request),
                }
            }

        # Find the object by UID
        obj = api.content.get(UID=self.uid)
        if not obj:
            self.request.response.setStatus(404)
            return {
                "error": {
                    "type": "NotFound",
                    "message": translate(
                        _("Object with UID ${uid} not found", mapping={"uid": self.uid}),
                        context=self.request,
                    ),
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
                    "message": translate(
                        _("Invalid original path: ${path}", mapping={"path": original_path}),
                        context=self.request,
                    ),
                }
            }

        # The original parent path (without the object id at the end)
        original_parent_path = "/".join(path_parts[:-1])
        original_id = path_parts[-1]

        # Try to get the original parent container
        try:
            # Handle case when object was directly under portal (path like "/plone/test-doc")
            # In this case, path_parts is ['plone', 'test-doc'] and original_parent_path is 'plone'
            # which is the portal id itself
            if original_parent_path == portal.getId():
                target_container = portal
            else:
                # Strip the portal id from the path if it's the first part
                portal_id = portal.getId()
                if original_parent_path.startswith(portal_id + "/"):
                    _index = len(portal_id) + 1
                    relative_path = original_parent_path[_index:]
                    target_container = portal.restrictedTraverse(relative_path)
                elif original_parent_path == portal_id:
                    target_container = portal
                else:
                    target_container = portal.restrictedTraverse(original_parent_path)
        except (KeyError, AttributeError):
            self.request.response.setStatus(404)
            return {
                "error": {
                    "type": "NotFound",
                    "message": translate(
                        _("Original parent container not found: /${path}", mapping={"path": original_parent_path}),
                        context=self.request,
                    ),
                }
            }

        # Check for name conflict
        if original_id in target_container.objectIds():
            self.request.response.setStatus(409)
            return {
                "error": {
                    "type": "Conflict",
                    "message": translate(
                        _('Name conflict: An object with id "${id}" already exists at /${path}',
                          mapping={"id": original_id, "path": original_parent_path}),
                        context=self.request,
                    ),
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
            DeletionLog.update_entry_status(self.uid, "withdrawn")

            logger.info(
                f"Withdrawal successful:\n"
                f"  UID: {self.uid}\n"
                f"  Title: {log_entry['title']}\n"
                f"  Restored to: /{original_parent_path}/{original_id}"
            )

            self.request.response.setStatus(200)
            return {
                "status": "success",
                "message": translate(
                    _('Object "${title}" has been restored to its original location',
                      mapping={"title": log_entry["title"]}),
                    context=self.request,
                ),
                "restored_path": f"/{original_parent_path}/{original_id}",
                "uid": self.uid,
            }

        except Exception as e:
            logger.error(f"Error during withdrawal: {e}")
            self.request.response.setStatus(500)
            return {
                "error": {
                    "type": "InternalError",
                    "message": translate(
                        _("Error restoring object: ${error}", mapping={"error": str(e)}),
                        context=self.request,
                    ),
                }
            }
