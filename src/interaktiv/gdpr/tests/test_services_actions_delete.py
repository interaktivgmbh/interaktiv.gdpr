import plone.api as api
from interaktiv.framework.test import TestCase

from interaktiv.gdpr.services.actions.delete import GDPRContentDelete
from interaktiv.gdpr.testing import INTERAKTIV_GDPR_INTEGRATION_TESTING


class TestGDPRContentDelete(TestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def test_reply__sets_mark_for_deletion_param(self):
        # setup
        document = api.content.create(
            container=self.portal,
            type="Document",
            id="test-document",
            title="Test Document",
        )

        service = GDPRContentDelete(document, self.request)

        # precondition
        self.assertIsNone(self.request.get("mark_for_deletion"))

        # do it
        try:
            service.reply()
        except Exception:
            # The parent class may raise exceptions, we just want to check the param
            pass

        # postcondition
        self.assertTrue(self.request.get("mark_for_deletion"))
