"""Tests unitarios de las reglas de negocio, sin HTTP."""
from datetime import date
from decimal import Decimal

from reservas.models import Reserva
from reservas.services import calcular_reembolso


def _reserva(check_in):
    return Reserva(check_in=check_in, check_out=date(2030, 1, 20), precio_total=Decimal("200.00"))


def test_politica_de_reembolso_en_los_bordes():
    hoy = date(2030, 1, 1)
    assert calcular_reembolso(_reserva(date(2030, 1, 8)), hoy) == Decimal("200.00")  # 7 días
    assert calcular_reembolso(_reserva(date(2030, 1, 7)), hoy) == Decimal("100.00")  # 6 días
    assert calcular_reembolso(_reserva(date(2030, 1, 3)), hoy) == Decimal("100.00")  # 2 días
    assert calcular_reembolso(_reserva(date(2030, 1, 2)), hoy) == Decimal("0.00")    # 1 día
