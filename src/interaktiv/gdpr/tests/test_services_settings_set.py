import json

import plone.api as api
from interaktiv.framework.test import TestCase

from interaktiv.gdpr.deletion_info_helper import DeletionLogHelper
from interaktiv.gdpr.services.settings.set import GDPRSettingsSet
from interaktiv.gdpr.testing import INTERAKTIV_GDPR_INTEGRATION_TESTING


class TestGDPRSettingsSet(TestCase):
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
