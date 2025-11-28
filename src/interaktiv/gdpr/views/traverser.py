from plone.rest.traverse import RESTWrapper
from Products.CMFCore.interfaces import IContentish
from zope.component import queryMultiAdapter
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


class MarkedDeletionContainerRESTTraverser:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def publishTraverse(self, request, name):
        if is_inside_deletion_container(self.context):
            check_access_allowed(self.context)

        self._publish_traverse(request, name)

    def _publish_traverse(self, request, name):
        service = queryMultiAdapter(
            (self.context, request), name=request._rest_service_id + name
        )
        if service is not None:
            return service

        adapter = DefaultPublishTraverse(self.context, request)
        obj = adapter.publishTraverse(request, name)
        if IContentish.providedBy(obj) and not (
            "@@" in request["PATH_INFO"] or "++view++" in request["PATH_INFO"]
        ):
            return RESTWrapper(obj, request)

        return obj

    def browserDefault(self, request):
        return self.context, (request._rest_service_id,)
