import plone.api as api

from interaktiv.gdpr.testing import (
    INTERAKTIV_GDPR_INTEGRATION_TESTING,
    InteraktivGDPRTestCase,
)
from interaktiv.gdpr.views.delete_confirmation import GDPRDeleteConfirmationForm


class TestGDPRDeleteConfirmationForm(InteraktivGDPRTestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def test_handle_delete__sets_mark_for_deletion_param(self):
        # setup
        document = api.content.create(
            container=self.portal,
            type="Document",
            id="test-document",
            title="Test Document",
        )
        form = GDPRDeleteConfirmationForm(document, self.request)

        # precondition
        self.assertIsNone(self.request.get("mark_for_deletion"))

        # do it
        try:
            form.handle_delete(form, None)
        except Exception:
            # May raise redirect or other exceptions
            pass

        # postcondition
        self.assertTrue(self.request.get("mark_for_deletion"))
