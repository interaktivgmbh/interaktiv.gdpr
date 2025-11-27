from interaktiv.framework.test import TestLayer
from plone.app.testing import FunctionalTesting, IntegrationTesting
from plone.testing.zope import WSGI_SERVER_FIXTURE


class InteraktivGDPRLayer(TestLayer):

    def __init__(self):
        super(InteraktivGDPRLayer, self).__init__()
        self.products_to_import = ['interaktiv.framework']
        self.product_to_install = 'interaktiv.gdpr'


INTERAKTIV_GDPR_FIXTURE = InteraktivGDPRLayer()
INTERAKTIV_GDPR_INTEGRATION_TESTING = IntegrationTesting(
    bases=(INTERAKTIV_GDPR_FIXTURE,), name="InteraktivGDPRLayer:Integration"
)
INTERAKTIV_GDPR_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(INTERAKTIV_GDPR_FIXTURE, WSGI_SERVER_FIXTURE), name="InteraktivGDPRLayer:Functional"
)
