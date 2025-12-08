from datetime import datetime, timedelta

import plone.api as api

from interaktiv.gdpr.deletion_log import DeletionLog
from interaktiv.gdpr.testing import (
    INTERAKTIV_GDPR_INTEGRATION_TESTING,
    InteraktivGDPRTestCase,
)


class TestDeletionLog(InteraktivGDPRTestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def setUp(self):
        super().setUp()
        # Clear the deletion log before each test
        DeletionLog.set_deletion_log([])

    def test_get_deletion_log__empty(self):
        # do it
        result = DeletionLog.get_deletion_log()

        # postcondition
        self.assertEqual(result, [])

    def test_set_deletion_log(self):
        # setup
        test_log = [
            {
                "uid": "test-uid",
                "datetime": datetime.now().isoformat(),
                "title": "Test Document",
                "portal_type": "Document",
                "original_path": "/plone/test-doc",
                "user_id": "admin",
                "status": "pending",
            }
        ]

        # do it
        DeletionLog.set_deletion_log(test_log)

        # postcondition
        result = DeletionLog.get_deletion_log()
        self.assertEqual(result, test_log)

    def test_get_display_days(self):
        # do it
        result = DeletionLog.get_display_days()

        # postcondition
        self.assertIsInstance(result, int)
        self.assertGreater(result, 0)

    def test_get_retention_days(self):
        # do it
        result = DeletionLog.get_retention_days()

        # postcondition
        self.assertIsInstance(result, int)
        self.assertGreater(result, 0)

    def test_get_deletion_log_for_display__filters_old_entries(self):
        # setup
        old_entry = {
            "uid": "old-uid",
            "datetime": (datetime.now() - timedelta(days=200)).isoformat(),
            "title": "Old Entry",
            "portal_type": "Document",
            "original_path": "/plone/old",
            "user_id": "admin",
            "status": "deleted",
        }
        recent_entry = {
            "uid": "recent-uid",
            "datetime": datetime.now().isoformat(),
            "title": "Recent Entry",
            "portal_type": "Document",
            "original_path": "/plone/recent",
            "user_id": "admin",
            "status": "pending",
        }
        DeletionLog.set_deletion_log([old_entry, recent_entry])

        # do it
        result = DeletionLog.get_deletion_log_for_display()

        # postcondition
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["uid"], "recent-uid")

    def test_add_entry__creates_entry(self):
        # setup
        document = api.content.create(
            container=self.portal, type="Document", id="test-doc", title="Test Document"
        )

        # do it
        result = DeletionLog.add_entry(document, status="pending")

        # postcondition
        self.assertIsNotNone(result)
        self.assertEqual(result["uid"], document.UID())
        self.assertEqual(result["title"], "Test Document")
        self.assertEqual(result["portal_type"], "Document")
        self.assertEqual(result["status"], "pending")

    def test_update_entry_status(self):
        # setup
        document = api.content.create(
            container=self.portal, type="Document", id="test-doc", title="Test Document"
        )
        doc_uid = document.UID()
        DeletionLog.add_entry(document, status="pending")

        # do it
        result = DeletionLog.update_entry_status(doc_uid, "withdrawn")

        # postcondition
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "withdrawn")

    def test_update_entry_status__non_existent(self):
        # do it
        result = DeletionLog.update_entry_status("non-existent-uid", "deleted")

        # postcondition
        self.assertIsNone(result)

    def test_get_entry_by_uid__found(self):
        # setup
        document = api.content.create(
            container=self.portal, type="Document", id="test-doc", title="Test Document"
        )
        doc_uid = document.UID()
        DeletionLog.add_entry(document, status="pending")

        # do it
        result = DeletionLog.get_entry_by_uid(doc_uid)

        # postcondition
        self.assertIsNotNone(result)
        self.assertEqual(result["uid"], doc_uid)

    def test_get_entry_by_uid__not_found(self):
        # do it
        result = DeletionLog.get_entry_by_uid("non-existent-uid")

        # postcondition
        self.assertIsNone(result)

    def test_get_pending_entry_by_uid__found(self):
        # setup
        document = api.content.create(
            container=self.portal, type="Document", id="test-doc", title="Test Document"
        )
        doc_uid = document.UID()
        DeletionLog.add_entry(document, status="pending")

        # do it
        result = DeletionLog.get_pending_entry_by_uid(doc_uid)

        # postcondition
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "pending")

    def test_get_pending_entry_by_uid__not_pending(self):
        # setup
        document = api.content.create(
            container=self.portal, type="Document", id="test-doc", title="Test Document"
        )
        doc_uid = document.UID()
        DeletionLog.add_entry(document, status="deleted")

        # do it
        result = DeletionLog.get_pending_entry_by_uid(doc_uid)

        # postcondition
        self.assertIsNone(result)

    def test_get_entries_by_status(self):
        # setup
        doc1 = api.content.create(
            container=self.portal,
            type="Document",
            id="test-doc-1",
            title="Test Document 1",
        )
        doc2 = api.content.create(
            container=self.portal,
            type="Document",
            id="test-doc-2",
            title="Test Document 2",
        )
        DeletionLog.add_entry(doc1, status="pending")
        DeletionLog.add_entry(doc2, status="deleted")

        # do it
        result = DeletionLog.get_entries_by_status("pending")

        # postcondition
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Test Document 1")

    def test_get_pending_objects(self):
        # setup
        document = api.content.create(
            container=self.portal, type="Document", id="test-doc", title="Test Document"
        )
        DeletionLog.add_entry(document, status="pending")

        # do it
        result = DeletionLog.get_pending_objects()

        # postcondition
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].UID(), document.UID())

    def test_run_scheduled_deletion__deletes_pending_in_container(self):
        # setup
        document = api.content.create(
            container=self.container,
            type="Document",
            id="test-doc",
            title="Test Document",
        )
        doc_uid = document.UID()
        DeletionLog.add_entry(document, status="pending")

        # precondition
        self.assertIn("test-doc", self.container.objectIds())

        # do it
        DeletionLog.run_scheduled_deletion()

        # postcondition
        self.assertNotIn("test-doc", self.container.objectIds())
        entry = DeletionLog.get_entry_by_uid(doc_uid)
        self.assertEqual(entry["status"], "deleted")

    def test_run_scheduled_deletion__skips_objects_outside_container(self):
        # setup
        document = api.content.create(
            container=self.portal, type="Document", id="test-doc", title="Test Document"
        )
        doc_uid = document.UID()
        DeletionLog.add_entry(document, status="pending")

        # precondition
        self.assertIn("test-doc", self.portal.objectIds())

        # do it
        DeletionLog.run_scheduled_deletion()

        # postcondition
        self.assertIn("test-doc", self.portal.objectIds())
        entry = DeletionLog.get_entry_by_uid(doc_uid)
        self.assertEqual(entry["status"], "pending")
