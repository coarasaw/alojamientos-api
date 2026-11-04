from datetime import timedelta

from reservas.models import Reserva


def _reserva_finalizada(alojamiento, huesped, hoy, estado=Reserva.Estado.CONFIRMADA):
    return Reserva.objects.create(
        alojamiento=alojamiento, huesped=huesped, check_in=hoy - timedelta(days=10),
        check_out=hoy - timedelta(days=7), huespedes=2, precio_total=300, estado=estado,
    )


def test_no_se_puede_valorar_antes_de_terminar_la_estadia(api_huesped, alojamiento, huesped, hoy):
    futura = Reserva.objects.create(
        alojamiento=alojamiento, huesped=huesped, check_in=hoy + timedelta(days=5),
        check_out=hoy + timedelta(days=8), huespedes=2, precio_total=300,
        estado=Reserva.Estado.CONFIRMADA,
    )
    r = api_huesped.post("/api/valoraciones/", {"reserva": futura.pk, "puntaje": 5})
    assert r.status_code == 400


def test_valoracion_de_estadia_finalizada_y_promedio(api, api_huesped, alojamiento, huesped, hoy):
    reserva = _reserva_finalizada(alojamiento, huesped, hoy)
    r = api_huesped.post(
        "/api/valoraciones/", {"reserva": reserva.pk, "puntaje": 4, "comentario": "Muy lindo"}
    )
    assert r.status_code == 201
    detalle = api.get(f"/api/alojamientos/{alojamiento.pk}/").data
    assert detalle["promedio_valoracion"] == 4.0
    assert detalle["cantidad_valoraciones"] == 1


def test_no_se_puede_valorar_dos_veces_la_misma_reserva(api_huesped, alojamiento, huesped, hoy):
    reserva = _reserva_finalizada(alojamiento, huesped, hoy)
    assert api_huesped.post("/api/valoraciones/", {"reserva": reserva.pk, "puntaje": 5}).status_code == 201
    assert api_huesped.post("/api/valoraciones/", {"reserva": reserva.pk, "puntaje": 1}).status_code == 400


def test_no_se_puede_valorar_una_reserva_ajena(api_huesped2, alojamiento, huesped, hoy):
    reserva = _reserva_finalizada(alojamiento, huesped, hoy)
    assert api_huesped2.post("/api/valoraciones/", {"reserva": reserva.pk, "puntaje": 5}).status_code == 400


def test_puntaje_fuera_de_rango_devuelve_400(api_huesped, alojamiento, huesped, hoy):
    reserva = _reserva_finalizada(alojamiento, huesped, hoy)
    assert api_huesped.post("/api/valoraciones/", {"reserva": reserva.pk, "puntaje": 6}).status_code == 400


def test_no_se_puede_valorar_una_reserva_cancelada(api_huesped, alojamiento, huesped, hoy):
    reserva = _reserva_finalizada(alojamiento, huesped, hoy, estado=Reserva.Estado.CANCELADA)
    assert api_huesped.post("/api/valoraciones/", {"reserva": reserva.pk, "puntaje": 5}).status_code == 400
