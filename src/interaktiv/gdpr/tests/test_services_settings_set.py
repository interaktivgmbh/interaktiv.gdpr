import json

import plone.api as api

from interaktiv.gdpr.deletion_info_helper import DeletionLogHelper
from interaktiv.gdpr.registry.deletion_log import IGDPRSettingsSchema
from interaktiv.gdpr.services.settings.set import GDPRSettingsSet
from interaktiv.gdpr.testing import (
    INTERAKTIV_GDPR_INTEGRATION_TESTING,
    InteraktivGDPRTestCase,
)


class TestGDPRSettingsSet(InteraktivGDPRTestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def test_reply__missing_param__returns_error(self):
        # setup
        service = GDPRSettingsSet(self.portal, self.request)
        self.request["BODY"] = b"{}"

        # do it
        result = service.reply()

        # postcondition
        self.assertEqual(self.request.response.getStatus(), 400)
        self.assertEqual(result["error"]["type"], "BadRequest")

    def test_reply__sets_enabled_true(self):
        # setup
        service = GDPRSettingsSet(self.portal, self.request)
        self.request["BODY"] = json.dumps({"marked_deletion_enabled": True}).encode()

        # do it
        result = service.reply()

        # postcondition
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["marked_deletion_enabled"])

    def test_reply__disable_with_pending__returns_conflict(self):
        # setup
        document = api.content.create(
            container=self.portal, type="Document", id="test-doc", title="Test Document"
        )
        DeletionLogHelper.add_entry(document, status="pending")

        service = GDPRSettingsSet(self.portal, self.request)
        self.request["BODY"] = json.dumps({"marked_deletion_enabled": False}).encode()

        # do it
        result = service.reply()

        # postcondition
        self.assertEqual(self.request.response.getStatus(), 409)
        self.assertEqual(result["error"]["type"], "Conflict")

    def test_reply__sets_retention_days(self):
        # setup
        service = GDPRSettingsSet(self.portal, self.request)
        self.request["BODY"] = json.dumps({"retention_days": 60}).encode()

        # do it
        result = service.reply()

        # postcondition
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["retention_days"], 60)
        # Verify registry was updated
        registry_value = api.portal.get_registry_record(
            name="retention_days", interface=IGDPRSettingsSchema
        )
        self.assertEqual(registry_value, 60)

    def test_reply__sets_dashboard_display_days(self):
        # setup
        service = GDPRSettingsSet(self.portal, self.request)
        self.request["BODY"] = json.dumps({"dashboard_display_days": 120}).encode()

        # do it
        result = service.reply()

        # postcondition
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["dashboard_display_days"], 120)
        # Verify registry was updated
        registry_value = api.portal.get_registry_record(
            name="dashboard_display_days", interface=IGDPRSettingsSchema
        )
        self.assertEqual(registry_value, 120)

    def test_reply__retention_days_invalid__returns_error(self):
        # setup
        service = GDPRSettingsSet(self.portal, self.request)
        self.request["BODY"] = json.dumps({"retention_days": 0}).encode()

        # do it
        result = service.reply()

        # postcondition
        self.assertEqual(self.request.response.getStatus(), 400)
        self.assertEqual(result["error"]["type"], "BadRequest")

    def test_reply__dashboard_display_days_invalid__returns_error(self):
        # setup
        service = GDPRSettingsSet(self.portal, self.request)
        self.request["BODY"] = json.dumps({"dashboard_display_days": -5}).encode()

        # do it
        result = service.reply()

        # postcondition
        self.assertEqual(self.request.response.getStatus(), 400)
        self.assertEqual(result["error"]["type"], "BadRequest")
