from typing import Any

from rest_framework import permissions
from rest_framework.request import Request

from accounts.models import User


class IsSelf(permissions.BasePermission):

    def has_object_permission(
        self,
        request: Request,
        view,
        obj: User,
    ) -> bool:
        return request.user == obj


class IsOwner(permissions.BasePermission):

    def has_object_permission(
        self,
        request: Request,
        view,
        obj: Any,
    ) -> bool:
        owner_field = getattr(view, "owner_field", "owner")
        owner = getattr(obj, owner_field, None)
        return request.user == owner
