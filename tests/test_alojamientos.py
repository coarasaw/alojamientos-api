from datetime import timedelta

from reservas.models import Reserva


def test_propietario_crea_alojamiento(api_propietario):
    r = api_propietario.post(
        "/api/alojamientos/",
        {"titulo": "Casa en Tigre", "ciudad": "Tigre", "precio_noche": "80.00", "capacidad": 6},
    )
    assert r.status_code == 201
    assert r.data["propietario"] == "duenio"


def test_huesped_no_puede_crear_alojamiento(api_huesped):
    r = api_huesped.post(
        "/api/alojamientos/",
        {"titulo": "X", "ciudad": "Y", "precio_noche": "50.00", "capacidad": 2},
    )
    assert r.status_code == 403


def test_propietario_no_edita_alojamiento_ajeno(api_otro_propietario, alojamiento):
    r = api_otro_propietario.patch(f"/api/alojamientos/{alojamiento.pk}/", {"titulo": "Hackeado"})
    assert r.status_code == 403


def test_busqueda_publica_por_ciudad(api, alojamiento):
    r = api.get("/api/alojamientos/?ciudad=buenos")
    assert r.status_code == 200
    assert r.data["count"] == 1
    assert api.get("/api/alojamientos/?ciudad=cordoba").data["count"] == 0


def test_busqueda_excluye_alojamientos_ocupados(api, alojamiento, huesped, hoy):
    Reserva.objects.create(
        alojamiento=alojamiento, huesped=huesped, check_in=hoy + timedelta(days=10),
        check_out=hoy + timedelta(days=15), huespedes=2, precio_total=500,
        estado=Reserva.Estado.CONFIRMADA,
    )
    ocupado = f"desde={hoy + timedelta(days=12)}&hasta={hoy + timedelta(days=14)}"
    libre = f"desde={hoy + timedelta(days=20)}&hasta={hoy + timedelta(days=22)}"
    assert api.get(f"/api/alojamientos/?{ocupado}").data["count"] == 0
    assert api.get(f"/api/alojamientos/?{libre}").data["count"] == 1


def test_busqueda_con_rango_invertido_devuelve_400(api):
    r = api.get("/api/alojamientos/?desde=2030-05-10&hasta=2030-05-01")
    assert r.status_code == 400


def test_disponibilidad_informa_fechas_ocupadas(api, alojamiento, huesped, hoy):
    Reserva.objects.create(
        alojamiento=alojamiento, huesped=huesped, check_in=hoy + timedelta(days=10),
        check_out=hoy + timedelta(days=13), huespedes=2, precio_total=300,
        estado=Reserva.Estado.PENDIENTE,
    )
    url = f"/api/alojamientos/{alojamiento.pk}/disponibilidad/"
    r = api.get(url, {"desde": hoy + timedelta(days=11), "hasta": hoy + timedelta(days=12)})
    assert r.status_code == 200
    assert r.data["disponible"] is False
    assert len(r.data["fechas_ocupadas"]) == 1
