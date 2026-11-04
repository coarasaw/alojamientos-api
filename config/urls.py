from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from alojamientos.views import AlojamientoViewSet
from reservas.views import ReservaViewSet
from valoraciones.views import ValoracionViewSet

router = DefaultRouter()
router.register("alojamientos", AlojamientoViewSet, basename="alojamiento")
router.register("reservas", ReservaViewSet, basename="reserva")
router.register("valoraciones", ValoracionViewSet, basename="valoracion")


def health(request):
    """Health check para Docker / Render / monitoreo."""
    try:
        connection.ensure_connection()
    except Exception:
        return JsonResponse({"status": "error", "db": "down"}, status=503)
    return JsonResponse({"status": "ok", "db": "up"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/auth/", include("accounts.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    path("api/", include(router.urls)),
]
