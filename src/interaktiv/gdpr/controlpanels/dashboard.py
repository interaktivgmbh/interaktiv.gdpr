from typing import List, Tuple

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.dexterity.content import DexterityContent

from interaktiv.gdpr.deletion_info_helper import DeletionInfoHelper, TDeletionInfo


class DeletionInfoDashboard(BrowserView):
    template = ViewPageTemplateFile("templates/deletion_info_dashboard.pt")

    def __call__(self) -> str:
        return self.template(self)

    @staticmethod
    def get_marked_objects_for_deletion() -> List[Tuple[DexterityContent, TDeletionInfo]]:
        return DeletionInfoHelper.get_marked_objects_for_deletion()
