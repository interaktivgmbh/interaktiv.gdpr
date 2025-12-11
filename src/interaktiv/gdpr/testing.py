from interaktiv.framework.test import TestCase, TestLayer
from plone import api
from plone.app.testing import FunctionalTesting, IntegrationTesting
from plone.testing.zope import WSGI_SERVER_FIXTURE
from zope.configuration import xmlconfig

from interaktiv.gdpr import create_marked_deletion_container
from interaktiv.gdpr.config import MARKED_FOR_DELETION_CONTAINER_ID
from interaktiv.gdpr.registry.deletion_log import IGDPRSettingsSchema


class InteraktivGDPRLayer(TestLayer):

    def __init__(self):
        super().__init__()
        self.products_to_import = ["interaktiv.framework"]
        self.product_to_install = "interaktiv.gdpr"

    def setUpZope(self, app, configuration_context):
        # Load plone.restapi meta.zcml first for plone:service directive
        import plone.restapi

        xmlconfig.file("meta.zcml", plone.restapi, context=configuration_context)
        xmlconfig.file("configure.zcml", plone.restapi, context=configuration_context)

        # Now proceed with normal setup
        super().setUpZope(app, configuration_context)


INTERAKTIV_GDPR_FIXTURE = InteraktivGDPRLayer()
INTERAKTIV_GDPR_INTEGRATION_TESTING = IntegrationTesting(
    bases=(INTERAKTIV_GDPR_FIXTURE,), name="InteraktivGDPRLayer:Integration"
)
INTERAKTIV_GDPR_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(INTERAKTIV_GDPR_FIXTURE, WSGI_SERVER_FIXTURE),
    name="InteraktivGDPRLayer:Functional",
)


class InteraktivGDPRTestCase(TestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING

    def setUp(self):
        super().setUp()

        create_marked_deletion_container()
        self.container = self.portal[MARKED_FOR_DELETION_CONTAINER_ID]

        api.portal.set_registry_record(
            name="deletion_log_enabled", interface=IGDPRSettingsSchema, value=True
        )
