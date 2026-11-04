from datetime import timedelta
from decimal import Decimal

from reservas.models import Reserva


def _reservar(api, payload):
    return api.post("/api/reservas/", payload, format="json")


def test_huesped_crea_reserva_y_se_calcula_el_total(api_huesped, payload_reserva):
    r = _reservar(api_huesped, payload_reserva(noches=3))
    assert r.status_code == 201
    assert r.data["estado"] == "PENDIENTE"
    assert Decimal(r.data["precio_total"]) == Decimal("300.00")
    assert r.data["noches"] == 3


def test_reserva_solapada_devuelve_409(api_huesped, api_huesped2, payload_reserva):
    assert _reservar(api_huesped, payload_reserva(dias_desde=10, noches=5)).status_code == 201
    r = _reservar(api_huesped2, payload_reserva(dias_desde=12, noches=2))
    assert r.status_code == 409


def test_el_dia_de_checkout_queda_libre(api_huesped, api_huesped2, payload_reserva):
    assert _reservar(api_huesped, payload_reserva(dias_desde=10, noches=2)).status_code == 201
    # check-in el mismo día que el check-out anterior: permitido
    assert _reservar(api_huesped2, payload_reserva(dias_desde=12, noches=2)).status_code == 201


def test_checkout_anterior_al_checkin_devuelve_400(api_huesped, payload_reserva):
    p = payload_reserva()
    p["check_out"], p["check_in"] = p["check_in"], p["check_out"]
    assert _reservar(api_huesped, p).status_code == 400


def test_no_se_puede_reservar_en_el_pasado(api_huesped, payload_reserva):
    assert _reservar(api_huesped, payload_reserva(dias_desde=-5)).status_code == 400


def test_no_se_puede_superar_la_capacidad(api_huesped, payload_reserva):
    assert _reservar(api_huesped, payload_reserva(huespedes=10)).status_code == 400


def test_propietario_no_puede_crear_reservas(api_propietario, payload_reserva):
    assert _reservar(api_propietario, payload_reserva()).status_code == 403


def test_propietario_confirma_y_otro_propietario_no(
    api_huesped, api_propietario, api_otro_propietario, payload_reserva
):
    rid = _reservar(api_huesped, payload_reserva()).data["id"]
    assert api_otro_propietario.post(f"/api/reservas/{rid}/confirmar/").status_code == 404
    r = api_propietario.post(f"/api/reservas/{rid}/confirmar/")
    assert r.status_code == 200 and r.data["estado"] == "CONFIRMADA"
    # No se puede confirmar dos veces
    assert api_propietario.post(f"/api/reservas/{rid}/confirmar/").status_code == 400


def test_huesped_no_puede_confirmar(api_huesped, payload_reserva):
    rid = _reservar(api_huesped, payload_reserva()).data["id"]
    assert api_huesped.post(f"/api/reservas/{rid}/confirmar/").status_code == 403


def test_cancelacion_con_mas_de_7_dias_reembolsa_el_total(api_huesped, payload_reserva):
    rid = _reservar(api_huesped, payload_reserva(dias_desde=10, noches=3)).data["id"]
    r = api_huesped.post(f"/api/reservas/{rid}/cancelar/")
    assert r.status_code == 200
    assert r.data["estado"] == "CANCELADA"
    assert Decimal(r.data["monto_reembolsado"]) == Decimal("300.00")


def test_cancelacion_entre_2_y_6_dias_reembolsa_el_50(api_huesped, payload_reserva):
    rid = _reservar(api_huesped, payload_reserva(dias_desde=4, noches=2)).data["id"]
    r = api_huesped.post(f"/api/reservas/{rid}/cancelar/")
    assert Decimal(r.data["monto_reembolsado"]) == Decimal("100.00")


def test_cancelacion_con_menos_de_2_dias_no_reembolsa(api_huesped, payload_reserva):
    rid = _reservar(api_huesped, payload_reserva(dias_desde=1, noches=2)).data["id"]
    r = api_huesped.post(f"/api/reservas/{rid}/cancelar/")
    assert Decimal(r.data["monto_reembolsado"]) == Decimal("0.00")


def test_cancelar_libera_las_fechas(api_huesped, api_huesped2, payload_reserva):
    rid = _reservar(api_huesped, payload_reserva(dias_desde=10, noches=3)).data["id"]
    api_huesped.post(f"/api/reservas/{rid}/cancelar/")
    assert _reservar(api_huesped2, payload_reserva(dias_desde=10, noches=3)).status_code == 201


def test_no_se_puede_cancelar_una_reserva_ajena(api_huesped, api_huesped2, payload_reserva):
    rid = _reservar(api_huesped, payload_reserva()).data["id"]
    assert api_huesped2.post(f"/api/reservas/{rid}/cancelar/").status_code == 404


def test_cada_huesped_ve_solo_sus_reservas(api_huesped, api_huesped2, payload_reserva):
    _reservar(api_huesped, payload_reserva(dias_desde=10))
    assert api_huesped.get("/api/reservas/").data["count"] == 1
    assert api_huesped2.get("/api/reservas/").data["count"] == 0
