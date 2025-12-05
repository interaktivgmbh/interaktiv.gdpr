import plone.api as api
from interaktiv.framework.test import TestCase

from interaktiv.gdpr.config import MARKED_FOR_DELETION_CONTAINER_ID
from interaktiv.gdpr.deletion_info_helper import DeletionLogHelper
from interaktiv.gdpr.services.actions.withdraw import WithdrawDeletion
from interaktiv.gdpr.testing import INTERAKTIV_GDPR_INTEGRATION_TESTING


class TestWithdrawDeletion(TestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def setUp(self):
        super().setUp()
        self.container = self.portal[MARKED_FOR_DELETION_CONTAINER_ID]

    def test_publishTraverse__sets_uid(self):
        # setup
        service = WithdrawDeletion(self.portal, self.request)
        test_uid = "test-uid-123"

        # precondition
        self.assertIsNone(service.uid)

        # do it
        result = service.publishTraverse(self.request, test_uid)

        # postcondition
        self.assertEqual(service.uid, test_uid)
        self.assertEqual(result, service)

    def test_reply__no_uid__returns_error(self):
        # setup
        service = WithdrawDeletion(self.portal, self.request)

        # do it
        result = service.reply()

        # postcondition
        self.assertEqual(self.request.response.getStatus(), 400)
        self.assertEqual(result["error"]["type"], "BadRequest")
        self.assertIn("UID is required", result["error"]["message"])

    def test_reply__no_pending_entry__returns_not_found(self):
        # setup
        service = WithdrawDeletion(self.portal, self.request)
        service.uid = "non-existent-uid"

        # do it
        result = service.reply()

        # postcondition
        self.assertEqual(self.request.response.getStatus(), 404)
        self.assertEqual(result["error"]["type"], "NotFound")

    def test_reply__object_restored_successfully(self):
        # setup
        document = api.content.create(
            container=self.portal, type="Document", id="test-doc", title="Test Document"
        )
        doc_uid = document.UID()

        # Add entry to deletion log
        DeletionLogHelper.add_entry(document, status="pending")

        # Move document to deletion container
        cookie = self.portal.manage_cutObjects(["test-doc"])
        self.container.manage_pasteObjects(cookie)

        service = WithdrawDeletion(self.portal, self.request)
        service.uid = doc_uid

        # precondition
        self.assertIn("test-doc", self.container.objectIds())
        self.assertNotIn("test-doc", self.portal.objectIds())

        # do it
        result = service.reply()

        # postcondition
        self.assertEqual(self.request.response.getStatus(), 200)
        self.assertEqual(result["status"], "success")
        self.assertIn("test-doc", self.portal.objectIds())

        # Check log entry status updated
        entry = DeletionLogHelper.get_entry_by_uid(doc_uid)
        self.assertEqual(entry["status"], "withdrawn")
