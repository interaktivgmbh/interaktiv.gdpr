from typing import Any

import plone.protect.interfaces
from plone import api
from plone.dexterity.content import DexterityContent
from plone.restapi.services import Service
from zope.interface import alsoProvides, implementer
from zope.publisher.interfaces import IPublishTraverse

from interaktiv.gdpr import _, logger
from interaktiv.gdpr.config import MARKED_FOR_DELETION_CONTAINER_ID
from interaktiv.gdpr.deletion_log import DeletionLog
from interaktiv.gdpr.registry.deletion_log import TDeletionLogEntry
from interaktiv.gdpr.utils import create_error_response, create_success_response


@implementer(IPublishTraverse)
class WithdrawDeletion(Service):

    def __init__(self, context: DexterityContent, request: Any) -> None:
        self.context = context
        self.request = request
        self.uid: str | None = None

    # noinspection PyUnusedLocal
    def publishTraverse(self, request: Any, name: str) -> "WithdrawDeletion":
        self.uid = name
        return self

    def _validate_uid(self) -> dict[str, Any] | None:
        if not self.uid:
            return create_error_response(
                self.request, 400, "BadRequest", _("UID is required")
            )
        return None

    def _get_log_entry(self) -> tuple[TDeletionLogEntry | None, dict[str, Any] | None]:
        log_entry = DeletionLog.get_pending_entry_by_uid(self.uid)
        if not log_entry:
            error = create_error_response(
                self.request,
                404,
                "NotFound",
                _(
                    "No pending deletion log entry found for UID: ${uid}",
                    mapping={"uid": self.uid},
                ),
            )
            return None, error
        return log_entry, None

    def _get_deletion_container(
        self,
    ) -> tuple[DexterityContent | None, dict[str, Any] | None]:
        portal = api.portal.get()
        container = portal.get(MARKED_FOR_DELETION_CONTAINER_ID)

        if not container:
            error = create_error_response(
                self.request,
                500,
                "InternalError",
                _("Marked deletion container not found"),
            )
            return None, error
        return container, None

    def _get_object(self) -> tuple[DexterityContent | None, dict[str, Any] | None]:
        obj = api.content.get(UID=self.uid)
        if not obj:
            error = create_error_response(
                self.request,
                404,
                "NotFound",
                _("Object with UID ${uid} not found", mapping={"uid": self.uid}),
            )
            return None, error
        return obj, None

    def _parse_original_path(
        self, original_path: str
    ) -> tuple[tuple[str, str] | None, dict[str, Any] | None]:
        path_parts = original_path.strip("/").split("/")

        if len(path_parts) < 2:
            error = create_error_response(
                self.request,
                400,
                "BadRequest",
                _("Invalid original path: ${path}", mapping={"path": original_path}),
            )
            return None, error

        original_parent_path = "/".join(path_parts[:-1])
        original_id = path_parts[-1]
        return (original_parent_path, original_id), None

    def _get_target_container(
        self, original_parent_path: str
    ) -> tuple[DexterityContent | None, dict[str, Any] | None]:
        portal = api.portal.get()

        try:
            if original_parent_path == portal.getId():
                return portal, None

            portal_id = portal.getId()
            if original_parent_path.startswith(portal_id + "/"):
                i = len(portal_id) + 1
                relative_path = original_parent_path[i:]
                return portal.restrictedTraverse(relative_path), None
            elif original_parent_path == portal_id:
                return portal, None
            else:
                return portal.restrictedTraverse(original_parent_path), None

        except (KeyError, AttributeError):
            error = create_error_response(
                self.request,
                404,
                "NotFound",
                _(
                    "Original parent container not found: /${path}",
                    mapping={"path": original_parent_path},
                ),
            )
            return None, error

    def _check_name_conflict(
        self,
        target_container: DexterityContent,
        original_id: str,
        original_parent_path: str,
    ) -> dict[str, Any] | None:
        if original_id in target_container.objectIds():
            return create_error_response(
                self.request,
                409,
                "Conflict",
                _(
                    'Name conflict: An object with id "${id}" already exists at /${path}',
                    mapping={"id": original_id, "path": original_parent_path},
                ),
            )
        return None

    def _move_object(
        self,
        obj: DexterityContent,
        container: DexterityContent,
        target_container: DexterityContent,
        original_id: str,
        log_entry: TDeletionLogEntry,
        original_parent_path: str,
    ) -> dict[str, Any]:
        try:
            cookie = container.manage_cutObjects([obj.getId()])
            target_container.manage_pasteObjects(cookie)

            pasted_obj = target_container[obj.getId()]
            if pasted_obj.getId() != original_id:
                api.content.rename(obj=pasted_obj, new_id=original_id)

            DeletionLog.update_entry_status(self.uid, "withdrawn")

            logger.info(
                f"Withdrawal successful:\n"
                f"  UID: {self.uid}\n"
                f"  Title: {log_entry['title']}\n"
                f"  Restored to: /{original_parent_path}/{original_id}"
            )

            return create_success_response(
                self.request,
                _(
                    'Object "${title}" has been restored to its original location',
                    mapping={"title": log_entry["title"]},
                ),
                restored_path=f"/{original_parent_path}/{original_id}",
                uid=self.uid,
            )

        except Exception as e:
            logger.error(f"Error during withdrawal: {e}")
            return create_error_response(
                self.request,
                500,
                "InternalError",
                _("Error restoring object: ${error}", mapping={"error": str(e)}),
            )

    def reply(self) -> dict[str, Any]:
        if "IDisableCSRFProtection" in dir(plone.protect.interfaces):
            alsoProvides(self.request, plone.protect.interfaces.IDisableCSRFProtection)

        if error := self._validate_uid():
            return error

        log_entry, error = self._get_log_entry()
        if error:
            return error

        container, error = self._get_deletion_container()
        if error:
            return error

        obj, error = self._get_object()
        if error:
            return error

        original_path = log_entry.get("original_path", "")
        path_info, error = self._parse_original_path(original_path)
        if error:
            return error

        original_parent_path, original_id = path_info

        target_container, error = self._get_target_container(original_parent_path)
        if error:
            return error

        if error := self._check_name_conflict(
            target_container, original_id, original_parent_path
        ):
            return error

        return self._move_object(
            obj,
            container,
            target_container,
            original_id,
            log_entry,
            original_parent_path,
        )
