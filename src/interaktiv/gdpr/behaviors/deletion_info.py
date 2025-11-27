import interaktiv.framework as framework
import zope.schema as schema
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from zope.component import adapts
from zope.interface import provider, implementer

from interaktiv.gdpr import _


@provider(IFormFieldProvider)
class IDeletionInfoBehavior(model.Schema):
    deletion_date = schema.Date(
        title=_('Deletion Date'),
        default=None,
        required=False
    )
    deletion_info = schema.Text(
        title=_('Deletion Info'),
        default='{}',
        required=False,
        constraint=framework.form.json_constraint
    )


@implementer(IDeletionInfoBehavior)
class DeletionInfoBehavior(object):
    adapts(IDexterityContent)

    def __init__(self, context):
        self.context = context
