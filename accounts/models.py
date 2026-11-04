from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Rol(models.TextChoices):
        HUESPED = "HUESPED", "Huésped"
        PROPIETARIO = "PROPIETARIO", "Propietario"
        ADMIN = "ADMIN", "Administrador"

    rol = models.CharField(max_length=12, choices=Rol.choices, default=Rol.HUESPED)

    def save(self, *args, **kwargs):
        # Los superusuarios creados con createsuperuser son administradores
        if self.is_superuser:
            self.rol = self.Rol.ADMIN
        super().save(*args, **kwargs)
