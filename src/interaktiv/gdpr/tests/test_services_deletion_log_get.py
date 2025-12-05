import plone.api as api
from interaktiv.framework.test import TestCase

from interaktiv.gdpr.deletion_info_helper import DeletionLogHelper
from interaktiv.gdpr.services.log.get import DeletionLogGet
from interaktiv.gdpr.testing import INTERAKTIV_GDPR_INTEGRATION_TESTING


class TestDeletionLogGet(TestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def test_reply__empty_log(self):
        # setup
        DeletionLogHelper.set_deletion_log([])
        service = DeletionLogGet(self.portal, self.request)

        # do it
        result = service.reply()

        # postcondition
        self.assertEqual(result["items"], [])
        self.assertEqual(result["total"], 0)

    def test_reply__with_entries(self):
        # setup
        document = api.content.create(
            container=self.portal, type="Document", id="test-doc", title="Test Document"
        )
        DeletionLogHelper.add_entry(document, status="pending")

        service = DeletionLogGet(self.portal, self.request)

        # do it
        result = service.reply()

        # postcondition
        self.assertGreater(result["total"], 0)
        self.assertEqual(len(result["items"]), result["total"])
