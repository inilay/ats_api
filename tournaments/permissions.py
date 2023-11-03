from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated, IsAdminUser


class IsTournamenOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        print("I!")
        return True

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        print('work perm')
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `owner`.
        return obj.owner.user == request.user


class IsBracketOwnerOrReadOnly(permissions.BasePermission):
     def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        
        if request.method in permissions.SAFE_METHODS:
            return True
    
        return obj.tournament.owner.user == request.user


class AuthMixin:
    
    def dasd(self,):
        print('asfdaf')