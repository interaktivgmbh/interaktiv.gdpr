from AccessControl import getSecurityManager
from plone import api
from plone.dexterity.content import DexterityContent
from zExceptions import Unauthorized

from interaktiv.gdpr.config import (
    MARKED_FOR_DELETION_ALLOWED_ROLES,
    MARKED_FOR_DELETION_CONTAINER_ID,
)


def is_inside_deletion_container(context: DexterityContent) -> bool:
    portal_url = api.portal.get().absolute_url()
    container_url = f"{portal_url}/{MARKED_FOR_DELETION_CONTAINER_ID}/"
    return context.absolute_url().startswith(container_url)


def check_access_allowed(context):
    sm = getSecurityManager()
    user = sm.getUser()

    if user is None:
        raise Unauthorized("Access to deleted content is restricted.")

    user_roles = set(user.getRolesInContext(context))

    if not user_roles & MARKED_FOR_DELETION_ALLOWED_ROLES:
        raise Unauthorized("Access to deleted content is restricted.")
