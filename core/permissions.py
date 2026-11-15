from typing import Any

from rest_framework import permissions
from rest_framework.request import Request


class IsOwner(permissions.BasePermission):

    def has_object_permission(
        self,
        request: Request,
        view,
        obj: Any,
        owner_field: str = "owner",
    ) -> bool:
        owner = getattr(obj, owner_field, None)
        return request.user == owner
