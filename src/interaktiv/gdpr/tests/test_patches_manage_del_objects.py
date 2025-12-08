import plone.api as api

from interaktiv.gdpr.config import (
    MARKED_FOR_DELETION_CONTAINER_ID,
    MARKED_FOR_DELETION_REQUEST_PARAM_NAME,
)
from interaktiv.gdpr.deletion_log import DeletionLog
from interaktiv.gdpr.patches.manage_del_objects import (
    get_marked_deletion_container,
    is_feature_enabled,
    patched_manage_delObjects,
    should_move_to_container,
)
from interaktiv.gdpr.registry.deletion_log import IGDPRSettingsSchema
from interaktiv.gdpr.testing import (
    INTERAKTIV_GDPR_INTEGRATION_TESTING,
    InteraktivGDPRTestCase,
)


class TestIsFeatureEnabled(InteraktivGDPRTestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def test_is_feature_enabled__default_true(self):
        # do it
        result = is_feature_enabled()

        # postcondition
        self.assertFalse(result)

    def test_is_feature_enabled__set_false(self):
        # setup
        api.portal.set_registry_record(
            name="marked_deletion_enabled", value=False, interface=IGDPRSettingsSchema
        )

        # do it
        result = is_feature_enabled()

        # postcondition
        self.assertFalse(result)


class TestGetMarkedDeletionContainer(InteraktivGDPRTestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def test_get_marked_deletion_container__exists(self):
        # do it
        result = get_marked_deletion_container()

        # postcondition
        self.assertIsNotNone(result)
        self.assertEqual(result.getId(), MARKED_FOR_DELETION_CONTAINER_ID)

    def test_get_marked_deletion_container__not_exists(self):
        # setup
        api.content.delete(self.portal[MARKED_FOR_DELETION_CONTAINER_ID])

        # do it
        result = get_marked_deletion_container()

        # postcondition
        self.assertIsNone(result)


class TestShouldMoveToContainer(InteraktivGDPRTestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def test_should_move_to_container__false_by_default(self):
        # do it
        result = should_move_to_container()

        # postcondition
        self.assertFalse(result)

    def test_should_move_to_container__true_when_param_set(self):
        # setup
        self.request.set(MARKED_FOR_DELETION_REQUEST_PARAM_NAME, True)

        # do it
        result = should_move_to_container()

        # postcondition
        self.assertTrue(result)


class TestPatchedManageDelObjects(InteraktivGDPRTestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def setUp(self):
        super().setUp()
        DeletionLog.set_deletion_log([])
        self.container = self.portal[MARKED_FOR_DELETION_CONTAINER_ID]

    def test_patched_manage_delObjects__without_mark_for_deletion__deletes_directly(
        self,
    ):
        # setup
        document = api.content.create(
            container=self.portal, type="Document", id="test-doc", title="Test Document"
        )
        doc_uid = document.UID()

        # precondition
        self.assertIn("test-doc", self.portal.objectIds())

        # do it
        patched_manage_delObjects(self.portal, ids=["test-doc"])

        # postcondition
        self.assertNotIn("test-doc", self.portal.objectIds())
        # Entry should be logged as deleted
        entry = DeletionLog.get_entry_by_uid(doc_uid)
        self.assertIsNotNone(entry)
        self.assertEqual(entry["status"], "deleted")

    def test_patched_manage_delObjects__with_mark_for_deletion__moves_to_container(
        self,
    ):
        # setup
        api.portal.set_registry_record(
            name="marked_deletion_enabled", value=True, interface=IGDPRSettingsSchema
        )
        document = api.content.create(
            container=self.portal, type="Document", id="test-doc", title="Test Document"
        )
        doc_uid = document.UID()
        self.request.set(MARKED_FOR_DELETION_REQUEST_PARAM_NAME, True)

        # precondition
        self.assertIn("test-doc", self.portal.objectIds())
        self.assertNotIn("test-doc", self.container.objectIds())

        # do it
        patched_manage_delObjects(self.portal, ids=["test-doc"])

        # postcondition
        self.assertNotIn("test-doc", self.portal.objectIds())
        self.assertIn("test-doc", self.container.objectIds())
        # Entry should be logged as pending
        entry = DeletionLog.get_entry_by_uid(doc_uid)
        self.assertIsNotNone(entry)
        self.assertEqual(entry["status"], "pending")

    def test_patched_manage_delObjects__feature_disabled__deletes_directly(self):
        # setup
        api.portal.set_registry_record(
            name="marked_deletion_enabled", value=False, interface=IGDPRSettingsSchema
        )
        api.content.create(
            container=self.portal, type="Document", id="test-doc", title="Test Document"
        )
        self.request.set(MARKED_FOR_DELETION_REQUEST_PARAM_NAME, True)

        # precondition
        self.assertIn("test-doc", self.portal.objectIds())

        # do it
        patched_manage_delObjects(self.portal, ids=["test-doc"])

        # postcondition
        self.assertNotIn("test-doc", self.portal.objectIds())
        self.assertNotIn("test-doc", self.container.objectIds())

    def test_patched_manage_delObjects__single_string_id(self):
        # setup
        api.portal.set_registry_record(
            name="marked_deletion_enabled", value=True, interface=IGDPRSettingsSchema
        )
        api.content.create(
            container=self.portal, type="Document", id="test-doc", title="Test Document"
        )
        self.request.set(MARKED_FOR_DELETION_REQUEST_PARAM_NAME, True)

        # precondition
        self.assertIn("test-doc", self.portal.objectIds())

        # do it
        patched_manage_delObjects(self.portal, ids="test-doc")

        # postcondition
        self.assertNotIn("test-doc", self.portal.objectIds())
        self.assertIn("test-doc", self.container.objectIds())

    def test_patched_manage_delObjects__multiple_objects(self):
        # setup
        api.portal.set_registry_record(
            name="marked_deletion_enabled", value=True, interface=IGDPRSettingsSchema
        )
        api.content.create(
            container=self.portal,
            type="Document",
            id="test-doc-1",
            title="Test Document 1",
        )
        api.content.create(
            container=self.portal,
            type="Document",
            id="test-doc-2",
            title="Test Document 2",
        )
        self.request.set(MARKED_FOR_DELETION_REQUEST_PARAM_NAME, True)

        # precondition
        self.assertIn("test-doc-1", self.portal.objectIds())
        self.assertIn("test-doc-2", self.portal.objectIds())

        # do it
        patched_manage_delObjects(self.portal, ids=["test-doc-1", "test-doc-2"])

        # postcondition
        self.assertNotIn("test-doc-1", self.portal.objectIds())
        self.assertNotIn("test-doc-2", self.portal.objectIds())
        self.assertIn("test-doc-1", self.container.objectIds())
        self.assertIn("test-doc-2", self.container.objectIds())
