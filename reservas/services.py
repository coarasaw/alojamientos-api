"""Reglas de negocio de las reservas. No depende de DRF: se puede testear sin HTTP."""
import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from alojamientos.models import Alojamiento

from .models import Reserva

logger = logging.getLogger("reservas")

# Política de cancelación (días de anticipación -> % de reembolso)
DIAS_REEMBOLSO_TOTAL = 7
DIAS_REEMBOLSO_PARCIAL = 2
PORCENTAJE_PARCIAL = Decimal("0.50")


class ReglaDeNegocioError(Exception):
    """Se violó una regla de negocio (HTTP 400)."""


class ConflictoDeFechasError(ReglaDeNegocioError):
    """Las fechas se pisan con otra reserva (HTTP 409)."""


def calcular_reembolso(reserva, hoy):
    dias = (reserva.check_in - hoy).days
    if dias >= DIAS_REEMBOLSO_TOTAL:
        porcentaje = Decimal("1")
    elif dias >= DIAS_REEMBOLSO_PARCIAL:
        porcentaje = PORCENTAJE_PARCIAL
    else:
        porcentaje = Decimal("0")
    return (reserva.precio_total * porcentaje).quantize(Decimal("0.01"))


def crear_reserva(*, huesped, alojamiento_id, check_in, check_out, huespedes):
    hoy = timezone.localdate()
    if check_in < hoy:
        raise ReglaDeNegocioError("La fecha de check-in no puede ser pasada.")
    if check_out <= check_in:
        raise ReglaDeNegocioError("El check-out debe ser posterior al check-in.")

    with transaction.atomic():
        # Bloqueamos el alojamiento: dos reservas simultáneas se serializan
        try:
            alojamiento = Alojamiento.objects.select_for_update().get(
                pk=alojamiento_id, activo=True
            )
        except Alojamiento.DoesNotExist:
            raise ReglaDeNegocioError("El alojamiento no existe o no está disponible.")

        if alojamiento.propietario_id == huesped.id:
            raise ReglaDeNegocioError("No podés reservar tu propio alojamiento.")
        if huespedes > alojamiento.capacidad:
            raise ReglaDeNegocioError(
                f"El alojamiento admite hasta {alojamiento.capacidad} huéspedes."
            )
        if Reserva.objects.solapadas(check_in, check_out).filter(alojamiento=alojamiento).exists():
            logger.warning(
                "reserva_rechazada_solapamiento alojamiento=%s huesped=%s %s/%s",
                alojamiento.pk, huesped.pk, check_in, check_out,
            )
            raise ConflictoDeFechasError("El alojamiento no está disponible en esas fechas.")

        noches = (check_out - check_in).days
        reserva = Reserva.objects.create(
            alojamiento=alojamiento,
            huesped=huesped,
            check_in=check_in,
            check_out=check_out,
            huespedes=huespedes,
            precio_total=alojamiento.precio_noche * noches,
        )

    logger.info(
        "reserva_creada id=%s alojamiento=%s huesped=%s total=%s",
        reserva.pk, alojamiento.pk, huesped.pk, reserva.precio_total,
    )
    return reserva


def confirmar_reserva(reserva):
    with transaction.atomic():
        reserva = Reserva.objects.select_for_update().get(pk=reserva.pk)
        if reserva.estado != Reserva.Estado.PENDIENTE:
            raise ReglaDeNegocioError("Solo se pueden confirmar reservas pendientes.")
        reserva.estado = Reserva.Estado.CONFIRMADA
        reserva.save(update_fields=["estado"])
    logger.info("reserva_confirmada id=%s", reserva.pk)
    return reserva


def cancelar_reserva(reserva):
    hoy = timezone.localdate()
    with transaction.atomic():
        reserva = Reserva.objects.select_for_update().get(pk=reserva.pk)
        if reserva.estado == Reserva.Estado.CANCELADA:
            raise ReglaDeNegocioError("La reserva ya está cancelada.")
        if reserva.check_in <= hoy:
            raise ReglaDeNegocioError("No se puede cancelar una reserva que ya comenzó.")
        reserva.monto_reembolsado = calcular_reembolso(reserva, hoy)
        reserva.estado = Reserva.Estado.CANCELADA
        reserva.save(update_fields=["estado", "monto_reembolsado"])
    logger.info(
        "reserva_cancelada id=%s reembolso=%s", reserva.pk, reserva.monto_reembolsado
    )
    return reserva
