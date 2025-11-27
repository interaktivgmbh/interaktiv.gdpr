import json
from typing import List, TypedDict

from plone.schema.jsonfield import JSONField
from zope import schema
from zope.interface import Interface


class TDeletionLogEntry(TypedDict):
    uid: str
    datetime: str
    title: str
    portal_type: str
    original_path: str
    user_id: str
    subobject_count: int
    review_state: str
    status: str  # 'pending', 'deleted', 'withdrawn'
    status_changed: str  # datetime when status changed
    status_changed_by: str  # user who changed status


DELETION_LOG_JSON_SCHEMA = json.dumps({
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "uid": {"type": "string"},
            "datetime": {"type": "string"},
            "title": {"type": "string"},
            "portal_type": {"type": "string"},
            "original_path": {"type": "string"},
            "user_id": {"type": "string"},
            "subobject_count": {"type": "integer"},
            "review_state": {"type": "string"},
            "status": {"type": "string", "enum": ["pending", "deleted", "withdrawn"]},
            "status_changed": {"type": "string"},
            "status_changed_by": {"type": "string"}
        },
        "required": ["uid", "datetime", "title", "portal_type", "original_path", "user_id", "status"]
    }
})

DELETION_LOG_DEFAULT: List[TDeletionLogEntry] = []


class IGDPRSettingsSchema(Interface):
    marked_deletion_enabled = schema.Bool(
        title='Marked Deletion Feature Enabled',
        description='When enabled, deleted content is moved to a marked deletion container instead of being permanently deleted.',
        default=True,
        required=True
    )


class IDeletionLogSchema(Interface):
    deletion_log = JSONField(
        title='Deletion Log',
        description='Log of all deletion requests including pending, deleted, and withdrawn items',
        schema=DELETION_LOG_JSON_SCHEMA,
        default=DELETION_LOG_DEFAULT
    )
