from typing import NoReturn

from Products.CMFPlone.Portal import PloneSite
from plone import api

from interaktiv.gdpr.config import MARKED_FOR_DELETION_CONTAINER_ID
from interaktiv.gdpr.registry.deletion_log import IGDPRSettingsSchema


def is_marked_deletion_enabled() -> bool:
    """Check if the marked deletion feature is enabled."""
    try:
        return api.portal.get_registry_record(
            name='marked_deletion_enabled',
            interface=IGDPRSettingsSchema
        )
    except (KeyError, api.exc.InvalidParameterError):
        # Default to True if registry record doesn't exist yet
        return True


def create_marked_deletion_container():
    """Create the marked deletion container if the feature is enabled."""
    if not is_marked_deletion_enabled():
        return

    portal = api.portal.get()

    if MARKED_FOR_DELETION_CONTAINER_ID not in portal:
        api.content.create(
            container=portal,
            type='MarkedDeletionContainer',
            id=MARKED_FOR_DELETION_CONTAINER_ID,
            title='Marked Deletion Container'
        )


# noinspection PyUnusedLocal
def post_install(context: PloneSite) -> NoReturn:
    create_marked_deletion_container()
