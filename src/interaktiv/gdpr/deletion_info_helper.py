import json
from typing import TypedDict, List, Tuple

from DateTime import DateTime
from plone import api

from interaktiv.gdpr import logger
from plone.dexterity.content import DexterityContent


class TDeletionInfo(TypedDict):
    datetime: str
    title: str
    portal_type: str
    path: str
    user_id: str
    subobject_count: int
    review_state: str


class DeletionInfoHelper:
    def run_deletion(self):
        for obj, info in self.get_marked_objects_for_deletion():
            if self.delete(obj):
                self.log(obj, info)

    @staticmethod
    def get_marked_objects_for_deletion() -> List[Tuple[DexterityContent, TDeletionInfo]]:
        objs = []

        for brain in api.content.find(deletion_date={"query": DateTime(), "range": "max"}):
            deletion_info_raw = getattr(brain, "deletion_info", None)
            deletion_info = json.loads(deletion_info_raw) if deletion_info_raw else {}

            if not deletion_info:
                continue

            objs.append((brain.getObject(), deletion_info))

        return objs

    @staticmethod
    def delete(obj) -> bool:
        return obj.aq_parent.manage_delObjects([obj.id])

    @staticmethod
    def log(obj, info):
        logger.info(
            "Deleted object:\n"
            f"  ID: {obj.getId()}\n"
            f"  Title: {info.get('title')}\n"
            f"  Portal type: {info.get('portal_type')}\n"
            f"  Path: {info.get('path')}\n"
            f"  User ID: {info.get('user_id')}\n"
            f"  Datetime: {info.get('datetime')}\n"
            f"  Subobject count: {info.get('subobject_count')}\n"
            f"  Review state: {info.get('review_state')}"
        )
