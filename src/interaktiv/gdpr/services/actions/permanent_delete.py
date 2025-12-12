from typing import Any

import plone.protect.interfaces
from plone import api
from plone.dexterity.content import DexterityContent
from plone.restapi.services import Service
from zope.interface import alsoProvides, implementer
from zope.publisher.interfaces import IPublishTraverse

from interaktiv.gdpr import _, logger
from interaktiv.gdpr.deletion_log import DeletionLog
from interaktiv.gdpr.utils import create_error_response, create_success_response


@implementer(IPublishTraverse)
class PermanentDeletion(Service):

    def __init__(self, context: DexterityContent, request: Any) -> None:
        self.context = context
        self.request = request
        self.uid: str | None = None

    def publishTraverse(self, request: Any, name: str) -> "PermanentDeletion":
        self.uid = name
        return self

    def reply(self) -> dict[str, Any]:
        if "IDisableCSRFProtection" in dir(plone.protect.interfaces):
            alsoProvides(self.request, plone.protect.interfaces.IDisableCSRFProtection)

        if not self.uid:
            return create_error_response(
                self.request, 400, "BadRequest", _("UID is required")
            )

        log_entry = DeletionLog.get_pending_entry_by_uid(self.uid)
        if not log_entry:
            return create_error_response(
                self.request,
                404,
                "NotFound",
                _(
                    "No pending deletion log entry found for UID: ${uid}",
                    mapping={"uid": self.uid},
                ),
            )

        obj = api.content.get(UID=self.uid)
        if not obj:
            return create_error_response(
                self.request,
                404,
                "NotFound",
                _("Object with UID ${uid} not found", mapping={"uid": self.uid}),
            )

        title = log_entry["title"]

        try:
            api.content.delete(obj=obj, check_linkintegrity=False)
            DeletionLog.update_entry_status(self.uid, "deleted")

            logger.info(
                f"Permanent deletion successful:\n"
                f"  UID: {self.uid}\n"
                f"  Title: {title}"
            )

            return create_success_response(
                self.request,
                _(
                    'Object "${title}" has been permanently deleted',
                    mapping={"title": title},
                ),
                uid=self.uid,
            )

        except Exception as e:
            logger.error(f"Error during permanent deletion: {e}")
            return create_error_response(
                self.request,
                500,
                "InternalError",
                _("Error deleting object: ${error}", mapping={"error": str(e)}),
            )
