from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from alojamientos.models import Alojamiento


@pytest.fixture
def hoy():
    return timezone.localdate()


@pytest.fixture
def propietario(db):
    return User.objects.create_user("duenio", password="clave12345", rol=User.Rol.PROPIETARIO)


@pytest.fixture
def otro_propietario(db):
    return User.objects.create_user("duenio2", password="clave12345", rol=User.Rol.PROPIETARIO)


@pytest.fixture
def huesped(db):
    return User.objects.create_user("huesped1", password="clave12345", rol=User.Rol.HUESPED)


@pytest.fixture
def huesped2(db):
    return User.objects.create_user("huesped2", password="clave12345", rol=User.Rol.HUESPED)


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser("admin", "a@a.com", "clave12345")


@pytest.fixture
def alojamiento(propietario):
    return Alojamiento.objects.create(
        propietario=propietario, titulo="Depto en Palermo", ciudad="Buenos Aires",
        precio_noche=Decimal("100.00"), capacidad=4,
    )


def cliente_para(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def api_huesped(huesped):
    return cliente_para(huesped)


@pytest.fixture
def api_huesped2(huesped2):
    return cliente_para(huesped2)


@pytest.fixture
def api_propietario(propietario):
    return cliente_para(propietario)


@pytest.fixture
def api_otro_propietario(otro_propietario):
    return cliente_para(otro_propietario)


@pytest.fixture
def payload_reserva(alojamiento, hoy):
    def _make(dias_desde=10, noches=3, huespedes=2):
        ci = hoy + timedelta(days=dias_desde)
        return {
            "alojamiento": alojamiento.pk,
            "check_in": ci.isoformat(),
            "check_out": (ci + timedelta(days=noches)).isoformat(),
            "huespedes": huespedes,
        }
    return _make
