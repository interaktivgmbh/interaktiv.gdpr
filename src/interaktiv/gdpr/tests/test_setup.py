from interaktiv.framework.test import TestCase
from plone.browserlayer import utils

from interaktiv.gdpr.interfaces import IInteraktivGDPRLayer
from interaktiv.gdpr.testing import INTERAKTIV_GDPR_INTEGRATION_TESTING


class TestSetup(TestCase):
    layer = INTERAKTIV_GDPR_INTEGRATION_TESTING
    product_name = 'interaktiv.gdpr'

    def test_product_installed(self):
        # setup
        installer = self.get_installer()

        # do it
        result = installer.is_product_installed(self.product_name)

        # postcondition
        self.assertTrue(result)

    def test_browserlayer_registered(self):
        # postcondition
        self.assertIn(IInteraktivGDPRLayer, utils.registered_layers())
