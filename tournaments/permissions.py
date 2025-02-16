from rest_framework import permissions

from .models import AnonymousBracket


class IsTournamenOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `owner`.
        return obj.owner.user == request.user


class IsBracketOwnerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.

        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.tournament.owner.user == request.user


class IsTournamentModeratorOrOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.id == obj.tournament.owner_id or obj.tournament.moderators.filter(id=request.user.id).exists():
            return True
        return False


class IsAnonymousBracket(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if AnonymousBracket.objects.filter(bracket=obj).exists():
            return True
        return False
