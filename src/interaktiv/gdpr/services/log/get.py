from plone import api
from plone.restapi.services import Service

from interaktiv.gdpr.deletion_log import DeletionLog


class DeletionLogGet(Service):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def reply(self):
        log = DeletionLog.get_deletion_log()

        enriched_log = []
        for entry in log:
            enriched_entry = dict(entry)

            if entry["status"] == "pending":
                obj = api.content.get(UID=entry["uid"])
                if obj:
                    enriched_entry["current_path"] = "/".join(obj.getPhysicalPath())
                    enriched_entry["current_url"] = obj.absolute_url()

            enriched_log.append(enriched_entry)

        return {"items": enriched_log, "total": len(enriched_log)}
