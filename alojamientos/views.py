from django.db.models import Avg, Count
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from reservas.models import Reserva

from .models import Alojamiento
from .permissions import PermisoAlojamiento
from .serializers import (
    AlojamientoSerializer,
    FiltrosBusquedaSerializer,
    RangoFechasSerializer,
)


class AlojamientoViewSet(viewsets.ModelViewSet):
    serializer_class = AlojamientoSerializer
    permission_classes = [PermisoAlojamiento]

    def get_queryset(self):
        qs = (
            Alojamiento.objects.filter(activo=True)
            .select_related("propietario")
            .annotate(
                promedio=Avg("reservas__valoracion__puntaje"),
                cantidad_valoraciones=Count("reservas__valoracion"),
            )
            .order_by("-creado")
        )
        if self.action == "list":
            qs = self._aplicar_filtros(qs)
        return qs

    def _aplicar_filtros(self, qs):
        filtros = FiltrosBusquedaSerializer(data=self.request.query_params)
        filtros.is_valid(raise_exception=True)
        f = filtros.validated_data
        if "ciudad" in f:
            qs = qs.filter(ciudad__icontains=f["ciudad"])
        if "huespedes" in f:
            qs = qs.filter(capacidad__gte=f["huespedes"])
        if "precio_max" in f:
            qs = qs.filter(precio_noche__lte=f["precio_max"])
        if "desde" in f:
            ocupados = Reserva.objects.solapadas(f["desde"], f["hasta"]).values("alojamiento_id")
            qs = qs.exclude(pk__in=ocupados)
        return qs

    def perform_create(self, serializer):
        serializer.save(propietario=self.request.user)

    def perform_destroy(self, instance):
        # Baja lógica: se conserva el historial de reservas
        instance.activo = False
        instance.save(update_fields=["activo"])

    @extend_schema(
        parameters=[
            OpenApiParameter("desde", str, description="YYYY-MM-DD", required=True),
            OpenApiParameter("hasta", str, description="YYYY-MM-DD", required=True),
        ]
    )
    @action(detail=True, methods=["get"])
    def disponibilidad(self, request, pk=None):
        """Indica si el alojamiento está libre en el rango y lista las fechas ocupadas."""
        alojamiento = self.get_object()
        rango = RangoFechasSerializer(data=request.query_params)
        rango.is_valid(raise_exception=True)
        desde, hasta = rango.validated_data["desde"], rango.validated_data["hasta"]

        disponible = not (
            Reserva.objects.solapadas(desde, hasta).filter(alojamiento=alojamiento).exists()
        )
        ocupadas = (
            Reserva.objects.activas()
            .filter(alojamiento=alojamiento, check_out__gt=timezone.localdate())
            .order_by("check_in")
            .values("check_in", "check_out")
        )
        return Response(
            {
                "alojamiento": alojamiento.pk,
                "desde": desde,
                "hasta": hasta,
                "disponible": disponible,
                "fechas_ocupadas": list(ocupadas),
            }
        )
