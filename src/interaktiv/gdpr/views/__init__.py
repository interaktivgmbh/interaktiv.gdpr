from plone import api
from plone.dexterity.content import DexterityContent
from zExceptions import Unauthorized

from interaktiv.gdpr.config import MARKED_FOR_DELETION_CONTAINER_ID


def is_inside_deletion_container(context: DexterityContent) -> bool:
    portal_url = api.portal.get().absolute_url()
    container_url = f"{portal_url}/{MARKED_FOR_DELETION_CONTAINER_ID}/"
    return context.absolute_url().startswith(container_url)


def check_access_allowed(context):
    if not api.user.has_permission("interaktiv.gdpr: View Controlpanel", obj=context):
        raise Unauthorized("Access to deleted content is restricted.")
