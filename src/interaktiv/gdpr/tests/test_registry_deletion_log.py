from interaktiv.gdpr.registry.deletion_log import (
    DELETION_LOG_DEFAULT,
    DELETION_LOG_JSON_SCHEMA,
    IDeletionLogSchema,
    IGDPRSettingsSchema,
    TDeletionLogEntry,
)
from interaktiv.gdpr.testing import (
    INTERAKTIV_GDPR_INTEGRATION_TESTING,
    InteraktivGDPRTestCase,
)


class TestTDeletionLogEntry(InteraktivGDPRTestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def test_typeddict_fields(self):
        # setup
        entry: TDeletionLogEntry = {
            "uid": "test-uid",
            "datetime": "2024-01-15T10:30:00",
            "title": "Test Title",
            "portal_type": "Document",
            "original_path": "/plone/test",
            "user_id": "admin",
            "subobject_count": 0,
            "review_state": "published",
            "status": "pending",
            "status_changed": "2024-01-15T10:30:00",
            "status_changed_by": "admin",
        }

        # postcondition
        self.assertEqual(entry["uid"], "test-uid")
        self.assertEqual(entry["status"], "pending")
        self.assertEqual(entry["portal_type"], "Document")


class TestDeletionLogJsonSchema(InteraktivGDPRTestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def test_json_schema_is_valid_json(self):
        # setup
        import json

        # do it
        parsed = json.loads(DELETION_LOG_JSON_SCHEMA)

        # postcondition
        self.assertEqual(parsed["type"], "array")
        self.assertIn("items", parsed)
        self.assertIn("properties", parsed["items"])

    def test_json_schema_required_fields(self):
        # setup
        import json

        parsed = json.loads(DELETION_LOG_JSON_SCHEMA)

        # postcondition
        required = parsed["items"]["required"]
        self.assertIn("uid", required)
        self.assertIn("datetime", required)
        self.assertIn("title", required)
        self.assertIn("status", required)


class TestDeletionLogDefault(InteraktivGDPRTestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def test_default_is_empty_list(self):
        # postcondition
        self.assertEqual(DELETION_LOG_DEFAULT, [])
        self.assertIsInstance(DELETION_LOG_DEFAULT, list)


class TestIGDPRSettingsSchema(InteraktivGDPRTestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def test_marked_deletion_enabled_field(self):
        # postcondition
        field = IGDPRSettingsSchema["marked_deletion_enabled"]
        self.assertEqual(field.default, False)

    def test_retention_days_field(self):
        # postcondition
        field = IGDPRSettingsSchema["retention_days"]
        self.assertEqual(field.default, 30)
        self.assertEqual(field.min, 1)

    def test_display_days_field(self):
        # postcondition
        field = IGDPRSettingsSchema["display_days"]
        self.assertEqual(field.default, 90)
        self.assertEqual(field.min, 1)


class TestIDeletionLogSchema(InteraktivGDPRTestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def test_deletion_log_field(self):
        # postcondition
        field = IDeletionLogSchema["deletion_log"]
        self.assertEqual(field.default, [])
