from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Valoracion(models.Model):
    # OneToOne: una sola valoración por reserva
    reserva = models.OneToOneField(
        "reservas.Reserva", on_delete=models.CASCADE, related_name="valoracion"
    )
    puntaje = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField(blank=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creada"]

    def __str__(self):
        return f"Valoración {self.puntaje}/5 de la reserva {self.reserva_id}"
