import plone.api as api
from interaktiv.framework.test import TestCase
from zExceptions import Unauthorized

from interaktiv.gdpr.config import MARKED_FOR_DELETION_CONTAINER_ID
from interaktiv.gdpr.testing import INTERAKTIV_GDPR_INTEGRATION_TESTING
from interaktiv.gdpr.views.traverser import (
    MarkedDeletionContainerRESTTraverser,
    MarkedDeletionContainerTraverser,
)


class TestMarkedDeletionContainerTraverser(TestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def setUp(self):
        super().setUp()
        self.container = self.portal[MARKED_FOR_DELETION_CONTAINER_ID]

    def test_publishTraverse__as_manager(self):
        # setup
        document = api.content.create(
            container=self.container,
            type="Document",
            id="test-doc",
            title="Test Document",
        )

        traverser = MarkedDeletionContainerTraverser(self.container, self.request)

        # do it (as manager - should work)
        result = traverser.publishTraverse(self.request, "test-doc")

        # postcondition
        self.assertEqual(result, document)

    def test_publishTraverse__as_anonymous__raises_unauthorized(self):
        # setup
        api.content.create(
            container=self.container,
            type="Document",
            id="test-doc",
            title="Test Document",
        )

        # Logout to be anonymous
        from plone.app.testing import logout

        logout()

        traverser = MarkedDeletionContainerTraverser(self.container, self.request)

        # do it & postcondition
        with self.assertRaises(Unauthorized):
            traverser.publishTraverse(self.request, "test-doc")


class TestMarkedDeletionContainerRESTTraverser(TestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def setUp(self):
        super().setUp()
        self.container = self.portal[MARKED_FOR_DELETION_CONTAINER_ID]

    def test_init(self):
        # do it
        traverser = MarkedDeletionContainerRESTTraverser(self.container, self.request)

        # postcondition
        self.assertEqual(traverser.context, self.container)
        self.assertEqual(traverser.request, self.request)

    def test_browserDefault(self):
        # setup
        self.request._rest_service_id = "@content"
        traverser = MarkedDeletionContainerRESTTraverser(self.container, self.request)

        # do it
        result = traverser.browserDefault(self.request)

        # postcondition
        self.assertEqual(result[0], self.container)
        self.assertEqual(result[1], ("@content",))
