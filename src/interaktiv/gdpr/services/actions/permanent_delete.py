import plone.protect.interfaces
from plone import api
from plone.restapi.services import Service
from zope.interface import alsoProvides, implementer
from zope.publisher.interfaces import IPublishTraverse

from interaktiv.gdpr import logger
from interaktiv.gdpr.deletion_info_helper import DeletionLogHelper


@implementer(IPublishTraverse)
class PermanentDeletion(Service):
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
