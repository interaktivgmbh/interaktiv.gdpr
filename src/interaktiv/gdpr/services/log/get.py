from typing import Any

from plone import api
from plone.dexterity.content import DexterityContent
from plone.restapi.services import Service
from zope.publisher.interfaces.browser import IBrowserRequest

from interaktiv.gdpr.deletion_log import DeletionLog
from interaktiv.gdpr.registry.deletion_log import TDeletionLogEntry

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500


class DeletionLogGet(Service):

    def __init__(self, context: DexterityContent, request: IBrowserRequest) -> None:
        self.context = context
        self.request = request

    def _get_pagination_params(self) -> tuple[int, int]:
        try:
            start = max(0, int(self.request.get("start", 0)))
        except (ValueError, TypeError):
            start = 0

        try:
            size = max(
                1, min(int(self.request.get("size", DEFAULT_PAGE_SIZE)), MAX_PAGE_SIZE)
            )
        except (ValueError, TypeError):
            size = DEFAULT_PAGE_SIZE

        return start, size

    # noinspection PyMethodMayBeStatic
    def _enrich_entry(self, entry: TDeletionLogEntry) -> dict[str, Any]:
        enriched_entry: dict[str, Any] = dict(entry)

        if entry["status"] == "pending":
            obj = api.content.get(UID=entry["uid"])
            if obj:
                enriched_entry["current_path"] = "/".join(obj.getPhysicalPath())
                enriched_entry["current_url"] = obj.absolute_url()

        return enriched_entry

    def reply(self) -> dict[str, Any]:
        log = DeletionLog.get_deletion_log()
        total = len(log)

        start, size = self._get_pagination_params()
        _end = start + size
        paginated_log = log[start:_end]
        enriched_log = [self._enrich_entry(entry) for entry in paginated_log]

        return {
            "items": enriched_log,
            "total": total,
            "start": start,
            "size": len(enriched_log),
        }
