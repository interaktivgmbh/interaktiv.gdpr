import logging

from plone import api
from zope.i18nmessageid import MessageFactory

from interaktiv.gdpr.config import MARKED_FOR_DELETION_CONTAINER_ID

logger = logging.getLogger("interaktiv.gdpr")
_ = MessageFactory("interaktiv.gdpr")

# Import patches to apply them
from interaktiv.gdpr import patches  # noqa


def create_marked_deletion_container() -> None:
    portal = api.portal.get()

    if MARKED_FOR_DELETION_CONTAINER_ID not in portal:
        api.content.create(
            container=portal,
            type="MarkedDeletionContainer",
            id=MARKED_FOR_DELETION_CONTAINER_ID,
            title="Marked Deletion Container",
        )
