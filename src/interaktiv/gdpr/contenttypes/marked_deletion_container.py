from plone.volto.content import FolderishDocument
from plone.volto.interfaces import IFolderishDocument
from zope.interface import implementer


class IMarkedDeletionContainer(IFolderishDocument):
    """ . """


@implementer(IMarkedDeletionContainer)
class MarkedDeletionContainer(FolderishDocument):
    """ . """
