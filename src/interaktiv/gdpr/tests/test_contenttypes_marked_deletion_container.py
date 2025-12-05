import plone.api as api

from interaktiv.gdpr.config import MARKED_FOR_DELETION_CONTAINER_ID
from interaktiv.gdpr.contenttypes.marked_deletion_container import (
    IMarkedDeletionContainer,
)
from interaktiv.gdpr.testing import (
    INTERAKTIV_GDPR_INTEGRATION_TESTING,
    InteraktivGDPRTestCase,
)


class TestMarkedDeletionContainer(InteraktivGDPRTestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def test_container_exists(self):
        # postcondition
        self.assertIn(MARKED_FOR_DELETION_CONTAINER_ID, self.portal.objectIds())

    def test_container_portal_type(self):
        # postcondition
        self.assertEqual(self.container.portal_type, "MarkedDeletionContainer")

    def test_container_provides_interface(self):
        # postcondition
        self.assertTrue(IMarkedDeletionContainer.providedBy(self.container))

    def test_container_is_folderish(self):
        # postcondition
        self.assertTrue(hasattr(self.container, "objectIds"))

    def test_container_can_contain_content(self):
        # setup
        document = api.content.create(
            container=self.container,
            type="Document",
            id="test-doc",
            title="Test Document",
        )

        # postcondition
        self.assertIn("test-doc", self.container.objectIds())
        self.assertEqual(document.portal_type, "Document")

    def test_create_new_container(self):
        # setup
        api.content.delete(self.container)

        # precondition
        self.assertNotIn(MARKED_FOR_DELETION_CONTAINER_ID, self.portal.objectIds())

        # do it
        new_container = api.content.create(
            container=self.portal,
            type="MarkedDeletionContainer",
            id="new-deletion-container",
            title="New Deletion Container",
        )

        # postcondition
        self.assertIn("new-deletion-container", self.portal.objectIds())
        self.assertTrue(IMarkedDeletionContainer.providedBy(new_container))
