from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
from ZPublisher.BaseRequest import DefaultPublishTraverse

from interaktiv.gdpr.views import check_access_allowed, is_inside_deletion_container


@implementer(IPublishTraverse)
class MarkedDeletionContainerTraverser(DefaultPublishTraverse):
    def publishTraverse(self, request, name):
        obj = super().publishTraverse(request, name)

        check_access_allowed(self.context)

        return obj


@implementer(IPublishTraverse)
class MarkedDeletionContainerRESTTraverser(DefaultPublishTraverse):
    def publishTraverse(self, request, name):
        obj = super().publishTraverse(request, name)

        if is_inside_deletion_container(self.context):
            check_access_allowed(self.context)

        return obj
