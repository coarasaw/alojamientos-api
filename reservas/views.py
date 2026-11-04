from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User

from . import services
from .models import Reserva
from .serializers import ReservaCreateSerializer, ReservaSerializer


class ReglaNegocio(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "regla_de_negocio"


class Conflicto(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "conflicto"


def _ejecutar(funcion, **kwargs):
    """Traduce los errores de dominio a respuestas HTTP."""
    try:
        return funcion(**kwargs)
    except services.ConflictoDeFechasError as e:
        raise Conflicto(str(e))
    except services.ReglaDeNegocioError as e:
        raise ReglaNegocio(str(e))


class ReservaViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return ReservaCreateSerializer
        return ReservaSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Reserva.objects.none()
        u = self.request.user
        qs = Reserva.objects.select_related("alojamiento", "huesped")
        if u.rol == User.Rol.ADMIN:
            return qs
        if u.rol == User.Rol.PROPIETARIO:
            return qs.filter(alojamiento__propietario=u)
        return qs.filter(huesped=u)

    @extend_schema(request=ReservaCreateSerializer, responses={201: ReservaSerializer})
    def create(self, request, *args, **kwargs):
        if request.user.rol != User.Rol.HUESPED:
            raise PermissionDenied("Solo los huéspedes pueden crear reservas.")
        serializer = ReservaCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        reserva = _ejecutar(
            services.crear_reserva,
            huesped=request.user,
            alojamiento_id=d["alojamiento"],
            check_in=d["check_in"],
            check_out=d["check_out"],
            huespedes=d["huespedes"],
        )
        return Response(ReservaSerializer(reserva).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=None, responses=ReservaSerializer)
    @action(detail=True, methods=["post"])
    def confirmar(self, request, pk=None):
        """El propietario del alojamiento (o un admin) confirma una reserva pendiente."""
        reserva = self.get_object()
        u = request.user
        if not (u.rol == User.Rol.ADMIN or reserva.alojamiento.propietario_id == u.id):
            raise PermissionDenied("Solo el propietario del alojamiento puede confirmar.")
        reserva = _ejecutar(services.confirmar_reserva, reserva=reserva)
        return Response(ReservaSerializer(reserva).data)

    @extend_schema(request=None, responses=ReservaSerializer)
    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        """El huésped (o un admin) cancela la reserva. El reembolso depende de la anticipación."""
        reserva = self.get_object()
        u = request.user
        if not (u.rol == User.Rol.ADMIN or reserva.huesped_id == u.id):
            raise PermissionDenied("Solo el huésped que reservó puede cancelar.")
        reserva = _ejecutar(services.cancelar_reserva, reserva=reserva)
        return Response(ReservaSerializer(reserva).data)
