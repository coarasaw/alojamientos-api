def test_registro_y_login_devuelven_tokens(api, db):
    r = api.post("/api/auth/registro/", {"username": "ana", "password": "clave12345", "rol": "HUESPED"})
    assert r.status_code == 201
    assert "password" not in r.data

    r = api.post("/api/auth/login/", {"username": "ana", "password": "clave12345"})
    assert r.status_code == 200
    assert "access" in r.data and "refresh" in r.data


def test_no_se_puede_registrar_un_admin_por_api(api, db):
    r = api.post("/api/auth/registro/", {"username": "x", "password": "clave12345", "rol": "ADMIN"})
    assert r.status_code == 400


def test_me_requiere_autenticacion(api):
    assert api.get("/api/auth/me/").status_code == 401


def test_health_check(api, db):
    r = api.get("/api/health/")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "db": "up"}
