import plone.api as api
from interaktiv.framework.test import TestCase

from interaktiv.gdpr.config import MARKED_FOR_DELETION_CONTAINER_ID
from interaktiv.gdpr.registry.deletion_log import IGDPRSettingsSchema
from interaktiv.gdpr.setuphandlers import (
    create_marked_deletion_container,
    is_marked_deletion_enabled,
)
from interaktiv.gdpr.testing import INTERAKTIV_GDPR_INTEGRATION_TESTING


class TestIsMarkedDeletionEnabled(TestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def test_is_marked_deletion_enabled__default_true(self):
        # do it
        result = is_marked_deletion_enabled()

        # postcondition
        self.assertTrue(result)

    def test_is_marked_deletion_enabled__set_false(self):
        # setup
        api.portal.set_registry_record(
            name="marked_deletion_enabled", value=False, interface=IGDPRSettingsSchema
        )

        # do it
        result = is_marked_deletion_enabled()

        # postcondition
        self.assertFalse(result)


class TestCreateMarkedDeletionContainer(TestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def test_create_marked_deletion_container__creates_when_not_exists(self):
        # setup
        api.content.delete(self.portal[MARKED_FOR_DELETION_CONTAINER_ID])

        # precondition
        self.assertNotIn(MARKED_FOR_DELETION_CONTAINER_ID, self.portal.objectIds())

        # do it
        create_marked_deletion_container()

        # postcondition
        self.assertIn(MARKED_FOR_DELETION_CONTAINER_ID, self.portal.objectIds())

    def test_create_marked_deletion_container__idempotent(self):
        # precondition
        self.assertIn(MARKED_FOR_DELETION_CONTAINER_ID, self.portal.objectIds())

        # do it
        create_marked_deletion_container()

        # postcondition
        self.assertIn(MARKED_FOR_DELETION_CONTAINER_ID, self.portal.objectIds())

    def test_create_marked_deletion_container__skips_when_feature_disabled(self):
        # setup
        api.portal.set_registry_record(
            name="marked_deletion_enabled", value=False, interface=IGDPRSettingsSchema
        )
        api.content.delete(self.portal[MARKED_FOR_DELETION_CONTAINER_ID])

        # precondition
        self.assertNotIn(MARKED_FOR_DELETION_CONTAINER_ID, self.portal.objectIds())

        # do it
        create_marked_deletion_container()

        # postcondition
        self.assertNotIn(MARKED_FOR_DELETION_CONTAINER_ID, self.portal.objectIds())
