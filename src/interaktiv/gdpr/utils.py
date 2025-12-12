from typing import Any

from plone import api
from zope.i18n import translate
from zope.interface import Interface
from zope.publisher.interfaces.browser import IBrowserRequest

from interaktiv.gdpr.registry.deletion_log import IGDPRSettingsSchema


def get_registry_setting(
    name: str, interface: type[Interface] = IGDPRSettingsSchema, default: Any = None
) -> Any:
    try:
        return api.portal.get_registry_record(name=name, interface=interface)
    except (KeyError, api.exc.InvalidParameterError):
        return default


def create_error_response(
    request: IBrowserRequest,
    status_code: int,
    error_type: str,
    message: str,
    **extra_fields: Any,
) -> dict[str, Any]:
    request.response.setStatus(status_code)

    if hasattr(message, "mapping"):
        message = translate(message, context=request)

    error_dict: dict[str, Any] = {
        "type": error_type,
        "message": message,
    }
    error_dict.update(extra_fields)

    return {"error": error_dict}


def create_success_response(
    request: IBrowserRequest,
    message: str,
    status_code: int = 200,
    **extra_fields: Any,
) -> dict[str, Any]:
    request.response.setStatus(status_code)

    if hasattr(message, "mapping"):
        message = translate(message, context=request)

    response: dict[str, Any] = {
        "status": "success",
        "message": message,
    }
    response.update(extra_fields)

    return response
