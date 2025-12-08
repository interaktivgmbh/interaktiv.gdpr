from plone.app.content.browser.contents.delete import DeleteActionView

from interaktiv.gdpr.config import MARKED_FOR_DELETION_REQUEST_PARAM_NAME


class GDPRDeleteActionView(DeleteActionView):
    """Override of the folder contents delete action view.

    Sets the mark_for_deletion parameter before calling manage_delObjects
    so the GDPR patched method moves objects to the MarkedDeletionContainer
    instead of permanently deleting them.
    """

    def action(self, obj):
        # Interaktiv Custom Code: Start
        self.request.set(MARKED_FOR_DELETION_REQUEST_PARAM_NAME, True)
        # Interaktiv Custom Code: End

        super().action(obj)
