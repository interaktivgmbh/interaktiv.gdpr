from interaktiv.gdpr.services.settings.get import GDPRSettingsGet
from interaktiv.gdpr.testing import (
    INTERAKTIV_GDPR_INTEGRATION_TESTING,
    InteraktivGDPRTestCase,
)


class TestGDPRSettingsGet(InteraktivGDPRTestCase):
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

    def test_reply__returns_retention_days(self):
        # setup
        service = GDPRSettingsGet(self.portal, self.request)

        # do it
        result = service.reply()

        # postcondition
        self.assertIn("retention_days", result)
        self.assertIsInstance(result["retention_days"], int)
        self.assertGreater(result["retention_days"], 0)

    def test_reply__returns_display_days(self):
        # setup
        service = GDPRSettingsGet(self.portal, self.request)

        # do it
        result = service.reply()

        # postcondition
        self.assertIn("display_days", result)
        self.assertIsInstance(result["display_days"], int)
        self.assertGreater(result["display_days"], 0)
