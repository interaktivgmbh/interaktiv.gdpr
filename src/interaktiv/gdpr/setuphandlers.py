from typing import NoReturn

from Products.CMFPlone.Portal import PloneSite
from plone import api


def create_marked_deletion_container():
    portal = api.portal.get()
    container_id = 'marked-for-deletion'

    if container_id not in portal:
        api.content.create(
            container=portal,
            type='MarkedDeletionContainer',
            id=container_id,
            title='Marked Deletion Container'
        )


# noinspection PyUnusedLocal
def post_install(context: PloneSite) -> NoReturn:
    create_marked_deletion_container()
