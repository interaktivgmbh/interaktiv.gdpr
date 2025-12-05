from datetime import datetime

import plone.api as api

from interaktiv.gdpr.controlpanels.dashboard import DashboardView
from interaktiv.gdpr.deletion_info_helper import DeletionLogHelper
from interaktiv.gdpr.testing import (
    INTERAKTIV_GDPR_INTEGRATION_TESTING,
    InteraktivGDPRTestCase,
)


class TestDashboardView(InteraktivGDPRTestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def setUp(self):
        super().setUp()
        self.view = DashboardView(self.portal, self.request)

    def test_call(self):
        # do it
        result = self.view()

        # postcondition
        self.assertIsInstance(result, str)
        self.assertIn("html", result.lower())

    def test_format_datetime__valid_datetime(self):
        # setup
        iso_datetime = "2024-01-15T10:30:00"

        # do it
        result = self.view.format_datetime(iso_datetime)

        # postcondition
        self.assertIsInstance(result, str)
        self.assertIn("2024", result)

    def test_format_datetime__none(self):
        # do it
        result = self.view.format_datetime(None)

        # postcondition
        self.assertEqual(result, "")

    def test_format_datetime__invalid(self):
        # setup
        invalid_datetime = "not-a-datetime"

        # do it
        result = self.view.format_datetime(invalid_datetime)

        # postcondition
        self.assertEqual(result, invalid_datetime)

    def test_format_datetime__german_locale(self):
        # setup
        self.request["LANGUAGE"] = "de"
        iso_datetime = "2024-01-15T10:30:00"

        # do it
        result = self.view.format_datetime(iso_datetime)

        # postcondition
        self.assertEqual(result, "15.01.2024 10:30")

    def test_format_datetime__english_locale(self):
        # setup
        self.request["LANGUAGE"] = "en"
        iso_datetime = "2024-01-15T10:30:00"

        # do it
        result = self.view.format_datetime(iso_datetime)

        # postcondition
        self.assertEqual(result, "2024-01-15 10:30")

    def test_get_scheduled_deletion_date__valid(self):
        # setup
        iso_datetime = datetime.now().isoformat()

        # do it
        result = self.view.get_scheduled_deletion_date(iso_datetime)

        # postcondition
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, "")

    def test_get_scheduled_deletion_date__none(self):
        # do it
        result = self.view.get_scheduled_deletion_date(None)

        # postcondition
        self.assertEqual(result, "")

    def test_get_retention_days(self):
        # do it
        result = self.view.get_retention_days()

        # postcondition
        self.assertIsInstance(result, int)
        self.assertGreater(result, 0)

    def test_is_feature_enabled(self):
        # do it
        result = self.view.is_feature_enabled()

        # postcondition
        self.assertIsInstance(result, bool)

    def test_get_display_days(self):
        # do it
        result = self.view.get_display_days()

        # postcondition
        self.assertIsInstance(result, int)
        self.assertGreater(result, 0)

    def test_get_pending_entries__empty(self):
        # setup
        DeletionLogHelper.set_deletion_log([])

        # do it
        result = self.view.get_pending_entries()

        # postcondition
        self.assertEqual(result, [])

    def test_get_pending_entries__with_entries(self):
        # setup
        document = api.content.create(
            container=self.portal, type="Document", id="test-doc", title="Test Document"
        )
        DeletionLogHelper.add_entry(document, status="pending")

        # do it
        result = self.view.get_pending_entries()

        # postcondition
        self.assertGreater(len(result), 0)
        self.assertEqual(result[0]["status"], "pending")

    def test_get_deletion_log_for_display(self):
        # setup
        document = api.content.create(
            container=self.portal, type="Document", id="test-doc", title="Test Document"
        )
        DeletionLogHelper.add_entry(document, status="pending")

        # do it
        result = self.view.get_deletion_log_for_display()

        # postcondition
        self.assertIsInstance(result, list)

    def test_get_pending_count(self):
        # setup
        DeletionLogHelper.set_deletion_log([])
        document = api.content.create(
            container=self.portal, type="Document", id="test-doc", title="Test Document"
        )
        DeletionLogHelper.add_entry(document, status="pending")

        # do it
        result = self.view.get_pending_count()

        # postcondition
        self.assertEqual(result, 1)
