from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.models import User


class PermisoAlojamiento(BasePermission):
    """Lectura pública. Escritura: propietarios y admins; solo sobre lo propio (admin: todo)."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        u = request.user
        return bool(
            u and u.is_authenticated and u.rol in (User.Rol.PROPIETARIO, User.Rol.ADMIN)
        )

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user.rol == User.Rol.ADMIN or obj.propietario_id == request.user.id
