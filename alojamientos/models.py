from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Alojamiento(models.Model):
    propietario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="alojamientos"
    )
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    ciudad = models.CharField(max_length=80, db_index=True)
    precio_noche = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("1"))]
    )
    capacidad = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]

    def __str__(self):
        return f"{self.titulo} ({self.ciudad})"
