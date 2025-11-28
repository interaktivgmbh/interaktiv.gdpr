from plone.restapi.services.content.delete import ContentDelete

from interaktiv.gdpr.config import MARKED_FOR_DELETION_REQUEST_PARAM_NAME


class GDPRContentDelete(ContentDelete):
    """GDPR-aware content delete service.

    Sets the mark_for_deletion parameter so the patched manage_delObjects
    moves content to the deletion container instead of permanently deleting it.
    """

    def reply(self):
        self.request.set(MARKED_FOR_DELETION_REQUEST_PARAM_NAME, True)
        return super().reply()
