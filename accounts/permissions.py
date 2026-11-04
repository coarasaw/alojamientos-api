from rest_framework.permissions import BasePermission

from .models import User


class TieneRol(BasePermission):
    roles: tuple = ()

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.rol in self.roles)


class EsHuesped(TieneRol):
    roles = (User.Rol.HUESPED,)
