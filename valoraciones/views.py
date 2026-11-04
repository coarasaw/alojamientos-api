from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from accounts.permissions import EsHuesped

from .models import Valoracion
from .serializers import ValoracionSerializer


class ValoracionViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ValoracionSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), EsHuesped()]
        return [AllowAny()]

    @extend_schema(parameters=[OpenApiParameter("alojamiento", int, required=False)])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        qs = Valoracion.objects.select_related("reserva__huesped")
        alojamiento = self.request.query_params.get("alojamiento")
        if alojamiento and alojamiento.isdigit():
            qs = qs.filter(reserva__alojamiento_id=int(alojamiento))
        return qs
