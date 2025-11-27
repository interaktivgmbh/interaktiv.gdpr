import plone.api as api
from interaktiv.framework.test import TestCase
from plone.browserlayer import utils

from interaktiv.gdpr.config import MARKED_FOR_DELETION_CONTAINER_ID
from interaktiv.gdpr.interfaces import IInteraktivGDPRLayer
from interaktiv.gdpr.setuphandlers import create_marked_deletion_container
from interaktiv.gdpr.testing import INTERAKTIV_GDPR_INTEGRATION_TESTING


class TestSetup(TestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING
    product_name = 'interaktiv.gdpr'

    def test_product_installed(self):
        # setup
        installer = self.get_installer()

        # do it
        result = installer.is_product_installed(self.product_name)

        # postcondition
        self.assertTrue(result)

    def test_browserlayer_registered(self):
        # postcondition
        self.assertIn(IInteraktivGDPRLayer, utils.registered_layers())

    # Setuphandler Tests

    def test_post_install__marked_deletion_container_created(self):
        # postcondition
        self.assertIn(MARKED_FOR_DELETION_CONTAINER_ID, self.portal.objectIds())
        container = self.portal[MARKED_FOR_DELETION_CONTAINER_ID]
        self.assertEqual(container.portal_type, 'MarkedDeletionContainer')
        self.assertEqual(container.title, 'Marked Deletion Container')

    def test_create_marked_deletion_container__creates_container(self):
        # setup
        api.content.delete(self.portal[MARKED_FOR_DELETION_CONTAINER_ID])

        # precondition
        self.assertNotIn(MARKED_FOR_DELETION_CONTAINER_ID, self.portal.objectIds())

        # do it
        create_marked_deletion_container()

        # postcondition
        self.assertIn(MARKED_FOR_DELETION_CONTAINER_ID, self.portal.objectIds())
        container = self.portal[MARKED_FOR_DELETION_CONTAINER_ID]
        self.assertEqual(container.portal_type, 'MarkedDeletionContainer')
        self.assertEqual(container.title, 'Marked Deletion Container')

    def test_create_marked_deletion_container__idempotent(self):
        # precondition
        self.assertIn(MARKED_FOR_DELETION_CONTAINER_ID, self.portal.objectIds())

        # do it
        create_marked_deletion_container()

        # postcondition
        self.assertIn(MARKED_FOR_DELETION_CONTAINER_ID, self.portal.objectIds())
        container = self.portal[MARKED_FOR_DELETION_CONTAINER_ID]
        self.assertEqual(container.portal_type, 'MarkedDeletionContainer')
