from OFS.ObjectManager import ObjectManager
from plone import api
from plone.dexterity.content import DexterityContent
from zope.globalrequest import getRequest
from zope.interface.interfaces import ComponentLookupError

from interaktiv.gdpr import logger
from interaktiv.gdpr.config import (
    MARKED_FOR_DELETION_CONTAINER_ID,
    MARKED_FOR_DELETION_REQUEST_PARAM_NAME,
)
from interaktiv.gdpr.deletion_log import DeletionLog
from interaktiv.gdpr.registry.deletion_log import IGDPRSettingsSchema

# Store original method
_original_manage_delObjects = ObjectManager.manage_delObjects


def is_feature_enabled() -> bool:
    try:
        return api.portal.get_registry_record(
            name="marked_deletion_enabled", interface=IGDPRSettingsSchema
        )
    except (KeyError, api.exc.InvalidParameterError):
        # Default to True if registry record doesn't exist yet
        return True
    except ComponentLookupError:
        return True


def get_marked_deletion_container() -> DexterityContent | None:
    try:
        portal = api.portal.get()

        if MARKED_FOR_DELETION_CONTAINER_ID in portal:
            return portal[MARKED_FOR_DELETION_CONTAINER_ID]
    except Exception as e:
        logger.error(f"Error getting marked deletion container: {e}")

    return None


def should_move_to_container() -> bool:
    request = getRequest()

    if request is None:
        return False

    # Check for parameter that triggers move to container
    return request.get(MARKED_FOR_DELETION_REQUEST_PARAM_NAME, False)


def _log_direct_deletion(container, ids):
    """Log direct deletions to the deletion log."""
    if isinstance(ids, str):
        ids = [ids]

    for obj_id in ids:
        try:
            if obj_id in container.objectIds():
                obj = container[obj_id]
                DeletionLog.add_entry(obj, status="deleted")
        except Exception as e:
            logger.error(f"Error logging deletion for {obj_id}: {e}")


def patched_manage_delObjects(self, ids=None, REQUEST=None):
    """
    Patched version of manage_delObjects.

    By default, objects are deleted normally (original behavior).
    To move objects to MarkedDeletionContainer instead, set
    'mark_for_deletion' parameter to True in the request.

    The feature must also be enabled in the registry.

    When the feature is disabled, deletions are still logged to the deletion log.
    """
    # Check if feature is enabled
    if not is_feature_enabled():
        # Log the deletion before actually deleting
        _log_direct_deletion(self, ids)
        return _original_manage_delObjects(self, ids, REQUEST)

    # Default behavior: use original deletion (but still log it)
    if not should_move_to_container():
        _log_direct_deletion(self, ids)
        return _original_manage_delObjects(self, ids, REQUEST)

    # Move to container was requested
    # Get the marked deletion container
    container = get_marked_deletion_container()

    # If container doesn't exist, fall back to original deletion
    if container is None:
        logger.warning("MarkedDeletionContainer not found, using direct deletion")
        return _original_manage_delObjects(self, ids, REQUEST)

    # Convert ids to list if it's a string
    if isinstance(ids, str):
        ids = [ids]

    # Move objects to marked deletion container instead of deleting
    try:
        moved_titles = []

        for obj_id in ids:
            try:
                obj = self[obj_id]
                obj_title = obj.title_or_id()

                # Add entry to deletion log BEFORE moving (to capture original path)
                DeletionLog.add_entry(obj, status="pending")

                # Cut the object
                cookie = self.manage_cutObjects([obj_id])

                # Paste into marked deletion container
                container.manage_pasteObjects(cookie)

                moved_titles.append(obj_title)
                logger.info(f"Moved object '{obj_title}' to marked deletion container")

            except Exception as e:
                logger.error(f"Error moving object {obj_id}: {e}")
                # Continue with next object
                continue

        # Set status message
        if REQUEST is not None:
            if moved_titles:
                message = (
                    f"Items moved to deletion container: {', '.join(moved_titles)}"
                )
                api.portal.show_message(message=message, request=REQUEST, type="info")

            # Redirect back
            if hasattr(self, "absolute_url"):
                REQUEST.RESPONSE.redirect(self.absolute_url())

        return moved_titles

    except Exception as e:
        logger.error(f"Error in patched_manage_delObjects: {e}")
        # Fall back to original deletion on error
        return _original_manage_delObjects(self, ids, REQUEST)


def apply_patch():
    ObjectManager.manage_delObjects = patched_manage_delObjects
    logger.info(
        f'Patching "{ObjectManager.__module__}.manage_delObjects" with "{patched_manage_delObjects.__module__}"'
    )
