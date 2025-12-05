import plone.api as api
from interaktiv.framework.test import TestCase
from zExceptions import Unauthorized

from interaktiv.gdpr.config import MARKED_FOR_DELETION_CONTAINER_ID
from interaktiv.gdpr.testing import INTERAKTIV_GDPR_INTEGRATION_TESTING
from interaktiv.gdpr.views import check_access_allowed, is_inside_deletion_container


class TestIsInsideDeletionContainer(TestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def setUp(self):
        super().setUp()
        self.container = self.portal[MARKED_FOR_DELETION_CONTAINER_ID]

    def test_is_inside_deletion_container__inside(self):
        # setup
        document = api.content.create(
            container=self.container,
            type="Document",
            id="test-doc",
            title="Test Document",
        )

        # do it
        result = is_inside_deletion_container(document)

        # postcondition
        self.assertTrue(result)

    def test_is_inside_deletion_container__outside(self):
        # setup
        document = api.content.create(
            container=self.portal, type="Document", id="test-doc", title="Test Document"
        )

        # do it
        result = is_inside_deletion_container(document)

        # postcondition
        self.assertFalse(result)


class TestCheckAccessAllowed(TestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def setUp(self):
        super().setUp()
        self.container = self.portal[MARKED_FOR_DELETION_CONTAINER_ID]

    def test_check_access_allowed__as_manager(self):
        # setup
        document = api.content.create(
            container=self.container,
            type="Document",
            id="test-doc",
            title="Test Document",
        )

        # do it (should not raise)
        check_access_allowed(document)

        # postcondition: no exception raised
        self.assertTrue(True)

    def test_check_access_allowed__as_anonymous__raises_unauthorized(self):
        # setup
        document = api.content.create(
            container=self.container,
            type="Document",
            id="test-doc",
            title="Test Document",
        )

        # Logout to be anonymous
        from plone.app.testing import logout

        logout()

        # do it & postcondition
        with self.assertRaises(Unauthorized):
            check_access_allowed(document)

    def test_check_access_allowed__as_member__raises_unauthorized(self):
        # setup
        document = api.content.create(
            container=self.container,
            type="Document",
            id="test-doc",
            title="Test Document",
        )

        # Create and login as a regular member
        api.user.create(
            email="member@example.com", username="testmember", password="secret123"
        )
        from plone.app.testing import login, logout

        logout()
        login(self.portal, "testmember")

        # do it & postcondition
        with self.assertRaises(Unauthorized):
            check_access_allowed(document)
