import plone.api as api
from zExceptions import Unauthorized

from interaktiv.gdpr.testing import (
    INTERAKTIV_GDPR_INTEGRATION_TESTING,
    InteraktivGDPRTestCase,
)
from interaktiv.gdpr.views.traverser import MarkedDeletionContainerTraverser


class TestMarkedDeletionContainerTraverser(InteraktivGDPRTestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

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
