from Acquisition import aq_inner, aq_parent
from plone.app.content.browser.actions import DeleteConfirmationForm
from plone.base import PloneMessageFactory as _
from plone.base.utils import safe_text
from plone.locking.interfaces import ILockable
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button

from interaktiv.gdpr.config import MARKED_FOR_DELETION_REQUEST_PARAM_NAME


class GDPRDeleteConfirmationForm(DeleteConfirmationForm):
    @button.buttonAndHandler(_("Delete"), name="Delete")
    def handle_delete(self, action):
        title = safe_text(self.context.Title())
        parent = aq_parent(aq_inner(self.context))

        # has the context object been acquired from a place it should not have
        # been?
        if self.context.aq_chain == self.context.aq_inner.aq_chain:
            try:
                lock_info = self.context.restrictedTraverse("@@plone_lock_info")
            except AttributeError:
                lock_info = None
            if lock_info is not None:
                if lock_info.is_locked() and not lock_info.is_locked_for_current_user():
                    # unlock object as it is locked by current user
                    ILockable(self.context).unlock()

            # Interaktiv Custom Code: Start
            # Set mark_for_deletion parameter before calling manage_delObjects
            self.request.set(MARKED_FOR_DELETION_REQUEST_PARAM_NAME, True)
            # Interaktiv Custom Code: End

            parent.manage_delObjects(self.context.getId())
            IStatusMessage(self.request).add(
                _("${title} has been deleted.", mapping={"title": title})
            )
        else:
            IStatusMessage(self.request).add(
                _('"${title}" has already been deleted', mapping={"title": title})
            )

        self.request.response.redirect(parent.absolute_url())
