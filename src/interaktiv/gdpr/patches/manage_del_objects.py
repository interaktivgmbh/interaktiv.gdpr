from typing import Any

from OFS.interfaces import IObjectManager
from OFS.ObjectManager import ObjectManager
from plone.dexterity.content import DexterityContent
from zope.globalrequest import getRequest
from zope.interface.interfaces import ComponentLookupError
from zope.publisher.interfaces.browser import IBrowserRequest

from interaktiv.gdpr import logger
from interaktiv.gdpr.config import (
    MARKED_FOR_DELETION_CONTAINER_ID,
    MARKED_FOR_DELETION_REQUEST_PARAM_NAME,
)
from interaktiv.gdpr.deletion_log import DeletionLog
from interaktiv.gdpr.registry.deletion_log import IGDPRSettingsSchema
from interaktiv.gdpr.utils import get_registry_setting

_original_manage_delObjects = ObjectManager.manage_delObjects


def is_feature_enabled() -> bool:
    try:
        result = get_registry_setting(
            "marked_deletion_enabled", IGDPRSettingsSchema, True
        )
        return result if result is not None else True
    except ComponentLookupError:
        return True


def get_marked_deletion_container() -> DexterityContent | None:
    try:
        from plone import api

        portal = api.portal.get()
        if MARKED_FOR_DELETION_CONTAINER_ID in portal:
            return portal[MARKED_FOR_DELETION_CONTAINER_ID]
    except Exception as e:
        logger.error(f"Error getting marked deletion container: {e}")
    return None


def should_move_to_container() -> bool:
    request: IBrowserRequest | None = getRequest()
    if request is None:
        return False
    return request.get(MARKED_FOR_DELETION_REQUEST_PARAM_NAME, False)


def _is_in_deletion_container(obj: DexterityContent) -> bool:
    container = get_marked_deletion_container()
    if container is None:
        return False
    obj_path = "/".join(obj.getPhysicalPath())
    container_path = "/".join(container.getPhysicalPath())
    return obj_path.startswith(container_path + "/")


def _log_direct_deletion(container: IObjectManager, ids: str | list[str]) -> None:
    if isinstance(ids, str):
        ids = [ids]

    for obj_id in ids:
        try:
            if obj_id in container.objectIds():
                obj = container[obj_id]
                # Skip logging if object is in marked-for-deletion container
                # (it already has a pending entry that will be updated separately)
                if _is_in_deletion_container(obj):
                    continue
                DeletionLog.add_entry(obj, status="deleted")
        except Exception as e:
            logger.error(f"Error logging deletion for {obj_id}: {e}")


def patched_manage_delObjects(
    self: IObjectManager, ids: str | list[str] | None = None, REQUEST: Any = None
) -> list[str] | None:
    from plone import api

    if not is_feature_enabled():
        _log_direct_deletion(self, ids)
        return _original_manage_delObjects(self, ids, REQUEST)

    if not should_move_to_container():
        _log_direct_deletion(self, ids)
        return _original_manage_delObjects(self, ids, REQUEST)

    container = get_marked_deletion_container()

    if container is None:
        logger.warning("MarkedDeletionContainer not found, using direct deletion")
        _log_direct_deletion(self, ids)
        return _original_manage_delObjects(self, ids, REQUEST)

    if isinstance(ids, str):
        ids = [ids]

    try:
        moved_titles: list[str] = []

        for obj_id in ids:
            try:
                obj = self[obj_id]
                obj_title = obj.title_or_id()

                DeletionLog.add_entry(obj, status="pending")

                cookie = self.manage_cutObjects([obj_id])
                container.manage_pasteObjects(cookie)

                moved_titles.append(obj_title)
                logger.info(f"Moved object '{obj_title}' to marked deletion container")

            except Exception as e:
                logger.error(f"Error moving object {obj_id}: {e}")
                continue

        if REQUEST is not None:
            if moved_titles:
                api.portal.show_message(
                    message=f"Items moved to deletion container: {', '.join(moved_titles)}",
                    request=REQUEST,
                    type="info",
                )

            if hasattr(self, "absolute_url"):
                REQUEST.RESPONSE.redirect(self.absolute_url())

        return moved_titles

    except Exception as e:
        logger.error(f"Error in patched_manage_delObjects: {e}")
        _log_direct_deletion(self, ids)
        return _original_manage_delObjects(self, ids, REQUEST)


def apply_patch() -> None:
    ObjectManager.manage_delObjects = patched_manage_delObjects
    logger.info(
        f'Patching "{ObjectManager.__module__}.manage_delObjects" with "{patched_manage_delObjects.__module__}"'
    )
