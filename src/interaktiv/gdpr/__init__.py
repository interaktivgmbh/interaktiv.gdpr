import logging

from zope.i18nmessageid import MessageFactory

logger = logging.getLogger('interaktiv.gdpr')
_ = MessageFactory("interaktiv.gdpr")

# Import patches to apply them
from interaktiv.gdpr import patches  # noqa
