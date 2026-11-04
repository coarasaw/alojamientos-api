from django.conf import settings
from django.db import models


class ReservaQuerySet(models.QuerySet):
    def activas(self):
        """Reservas que bloquean fechas: pendientes y confirmadas."""
        return self.filter(estado__in=[Reserva.Estado.PENDIENTE, Reserva.Estado.CONFIRMADA])

    def solapadas(self, desde, hasta):
        """Reservas activas que se pisan con [desde, hasta). El día de check-out queda libre."""
        return self.activas().filter(check_in__lt=hasta, check_out__gt=desde)


class Reserva(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        CONFIRMADA = "CONFIRMADA", "Confirmada"
        CANCELADA = "CANCELADA", "Cancelada"

    alojamiento = models.ForeignKey(
        "alojamientos.Alojamiento", on_delete=models.PROTECT, related_name="reservas"
    )
    huesped = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reservas"
    )
    check_in = models.DateField()
    check_out = models.DateField()
    huespedes = models.PositiveSmallIntegerField()
    precio_total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    monto_reembolsado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    creada = models.DateTimeField(auto_now_add=True)

    objects = ReservaQuerySet.as_manager()

    class Meta:
        ordering = ["-creada"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(check_out__gt=models.F("check_in")),
                name="reserva_checkout_posterior_a_checkin",
            )
        ]

    @property
    def noches(self):
        return (self.check_out - self.check_in).days

    def __str__(self):
        return f"Reserva {self.pk} - {self.alojamiento_id} ({self.check_in} a {self.check_out})"
