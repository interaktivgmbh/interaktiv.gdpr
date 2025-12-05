from interaktiv.framework.test import TestCase

from interaktiv.gdpr.services.settings.get import GDPRSettingsGet
from interaktiv.gdpr.testing import INTERAKTIV_GDPR_INTEGRATION_TESTING


class TestGDPRSettingsGet(TestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def test_reply__returns_settings(self):
        # setup
        service = GDPRSettingsGet(self.portal, self.request)

        # do it
        result = service.reply()

        # postcondition
        self.assertIn("marked_deletion_enabled", result)
        self.assertIn("pending_deletions_count", result)
        self.assertIsInstance(result["marked_deletion_enabled"], bool)
        self.assertIsInstance(result["pending_deletions_count"], int)
