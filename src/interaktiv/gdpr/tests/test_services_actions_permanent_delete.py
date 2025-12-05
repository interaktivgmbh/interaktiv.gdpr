import plone.api as api
from interaktiv.framework.test import TestCase

from interaktiv.gdpr.config import MARKED_FOR_DELETION_CONTAINER_ID
from interaktiv.gdpr.deletion_info_helper import DeletionLogHelper
from interaktiv.gdpr.services.actions.permanent_delete import PermanentDeletion
from interaktiv.gdpr.testing import INTERAKTIV_GDPR_INTEGRATION_TESTING


class TestPermanentDeletion(TestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def setUp(self):
        super().setUp()
        self.container = self.portal[MARKED_FOR_DELETION_CONTAINER_ID]

    def test_publishTraverse__sets_uid(self):
        # setup
        service = PermanentDeletion(self.portal, self.request)
        test_uid = "test-uid-456"

        # precondition
        self.assertIsNone(service.uid)

        # do it
        result = service.publishTraverse(self.request, test_uid)

        # postcondition
        self.assertEqual(service.uid, test_uid)
        self.assertEqual(result, service)

    def test_reply__no_uid__returns_error(self):
        # setup
        service = PermanentDeletion(self.portal, self.request)

        # do it
        result = service.reply()

        # postcondition
        self.assertEqual(self.request.response.getStatus(), 400)
        self.assertEqual(result["error"]["type"], "BadRequest")

    def test_reply__no_pending_entry__returns_not_found(self):
        # setup
        service = PermanentDeletion(self.portal, self.request)
        service.uid = "non-existent-uid"

        # do it
        result = service.reply()

        # postcondition
        self.assertEqual(self.request.response.getStatus(), 404)
        self.assertEqual(result["error"]["type"], "NotFound")

    def test_reply__deletes_object_permanently(self):
        # setup
        document = api.content.create(
            container=self.container,
            type="Document",
            id="test-doc",
            title="Test Document",
        )
        doc_uid = document.UID()
        DeletionLogHelper.add_entry(document, status="pending")

        service = PermanentDeletion(self.portal, self.request)
        service.uid = doc_uid

        # precondition
        self.assertIn("test-doc", self.container.objectIds())

        # do it
        result = service.reply()

        # postcondition
        self.assertEqual(self.request.response.getStatus(), 200)
        self.assertEqual(result["status"], "success")
        self.assertNotIn("test-doc", self.container.objectIds())

        # Check log entry status updated
        entry = DeletionLogHelper.get_entry_by_uid(doc_uid)
        self.assertEqual(entry["status"], "deleted")
