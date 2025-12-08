import plone.protect.interfaces
from plone import api
from plone.restapi.services import Service
from zope.i18n import translate
from zope.interface import alsoProvides, implementer
from zope.publisher.interfaces import IPublishTraverse

from interaktiv.gdpr import _, logger
from interaktiv.gdpr.deletion_log import DeletionLog


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

        title = log_entry["title"]

        # Permanently delete the object
        try:
            api.content.delete(obj=obj, check_linkintegrity=False)

            # Update log entry status
            DeletionLog.update_entry_status(self.uid, "deleted")

            logger.info(
                f"Permanent deletion successful:\n"
                f"  UID: {self.uid}\n"
                f"  Title: {title}"
            )

            self.request.response.setStatus(200)
            return {
                "status": "success",
                "message": translate(
                    _('Object "${title}" has been permanently deleted', mapping={"title": title}),
                    context=self.request,
                ),
                "uid": self.uid,
            }

        except Exception as e:
            logger.error(f"Error during permanent deletion: {e}")
            self.request.response.setStatus(500)
            return {
                "error": {
                    "type": "InternalError",
                    "message": translate(
                        _("Error deleting object: ${error}", mapping={"error": str(e)}),
                        context=self.request,
                    ),
                }
            }
