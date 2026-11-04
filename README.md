# API REST de Reservas de Alojamientos

TP Final Grupal · Programación de Vanguardia · Django + Django REST Framework + JWT.

Backend desacoplado: expone solo una API REST (JSON). El frontend (Angular u otro proyecto Django) la consume por HTTP.

## 1. Puesta en marcha (sin Docker)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

python manage.py migrate
python manage.py createsuperuser   # crea un administrador (rol ADMIN)
python manage.py runserver
```

- API: http://localhost:8000/api/
- Documentación Swagger (para probar los endpoints): http://localhost:8000/api/docs/
- Panel admin de Django: http://localhost:8000/admin/
- Health check: http://localhost:8000/api/health/

Por defecto usa SQLite. Si defines `POSTGRES_DB` (y el resto de variables de `.env.example`) usa PostgreSQL.

## 2. Puesta en marcha con Docker (PostgreSQL + backend)

```bash
docker compose up --build
```

Levanta dos contenedores: `db` (PostgreSQL 16) y `backend` (Django + gunicorn, aplica las migraciones al arrancar). Para crear el admin:

```bash
docker compose exec backend python manage.py createsuperuser
```

## 3. Tests

```bash
pytest -v
```

33 tests: autenticación, permisos por rol, búsqueda, disponibilidad, solapamiento de reservas, política de cancelación y valoraciones. El mismo comando corre en GitHub Actions (`.github/workflows/ci.yml`).

## 4. Estructura

```
config/          settings, urls, wsgi
accounts/        usuario con rol (HUESPED, PROPIETARIO, ADMIN), registro, JWT, permisos
alojamientos/    modelo Alojamiento, búsqueda con filtros, disponibilidad
reservas/        modelo Reserva, services.py (reglas de negocio), cancelar/confirmar
valoraciones/    modelo Valoracion (una por reserva)
tests/           pytest + pytest-django
```

Capas y responsabilidades:

| Capa | Archivo | Responsabilidad |
|---|---|---|
| Rutas / controlador | `views.py` | HTTP, permisos, traducir errores de dominio a 400/403/409 |
| Validación de entrada | `serializers.py` | Formato de datos, conversión a JSON |
| Reglas de negocio | `reservas/services.py` | Solapamiento, capacidad, reembolsos, estados. No depende de DRF |
| Persistencia | `models.py` | Modelos, restricciones (`CheckConstraint`), consultas (`solapadas`, `activas`) |

## 5. Endpoints

Autenticación con JWT: `Authorization: Bearer <access_token>`.

| Método | Ruta | Quién | Descripción |
|---|---|---|---|
| POST | `/api/auth/registro/` | Público | Alta de huésped o propietario |
| POST | `/api/auth/login/` | Público | Devuelve `access` y `refresh` |
| POST | `/api/auth/refresh/` | Público | Renueva el `access` |
| GET | `/api/auth/me/` | Autenticado | Datos del usuario actual |
| GET | `/api/alojamientos/` | Público | Búsqueda: `ciudad`, `huespedes`, `precio_max`, `desde`+`hasta` |
| GET | `/api/alojamientos/{id}/` | Público | Detalle con promedio de valoraciones |
| POST | `/api/alojamientos/` | Propietario, Admin | Crear alojamiento |
| PUT/PATCH | `/api/alojamientos/{id}/` | Dueño, Admin | Editar |
| DELETE | `/api/alojamientos/{id}/` | Dueño, Admin | Baja lógica (`activo=false`) |
| GET | `/api/alojamientos/{id}/disponibilidad/?desde=&hasta=` | Público | ¿Está libre? + fechas ocupadas |
| POST | `/api/reservas/` | Huésped | Crear reserva (queda PENDIENTE) |
| GET | `/api/reservas/` | Autenticado | Huésped: las suyas · Propietario: las de sus alojamientos · Admin: todas |
| GET | `/api/reservas/{id}/` | Según rol | Detalle |
| POST | `/api/reservas/{id}/confirmar/` | Propietario del alojamiento, Admin | PENDIENTE → CONFIRMADA |
| POST | `/api/reservas/{id}/cancelar/` | Huésped que reservó, Admin | Cancela y calcula reembolso |
| POST | `/api/valoraciones/` | Huésped | Valorar una estadía finalizada |
| GET | `/api/valoraciones/?alojamiento={id}` | Público | Valoraciones de un alojamiento |
| GET | `/api/health/` | Público | Estado de la API y la base |

Los listados están paginados (`count`, `next`, `previous`, `results`).

### Ejemplos

**Registro**

```bash
curl -X POST http://localhost:8000/api/auth/registro/ \
  -H "Content-Type: application/json" \
  -d '{"username":"laura","email":"laura@mail.com","password":"clave12345","rol":"PROPIETARIO"}'
```
```json
{"id": 1, "username": "laura", "email": "laura@mail.com", "rol": "PROPIETARIO"}
```

**Login**

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"laura","password":"clave12345"}'
```
```json
{"refresh": "eyJ...", "access": "eyJ..."}
```

**Crear alojamiento (propietario)**

```bash
curl -X POST http://localhost:8000/api/alojamientos/ \
  -H "Authorization: Bearer $TOKEN_PROPIETARIO" -H "Content-Type: application/json" \
  -d '{"titulo":"Depto luminoso en Palermo","descripcion":"2 ambientes con balcón","ciudad":"Buenos Aires","precio_noche":"85000.00","capacidad":4}'
```
```json
{"id": 1, "propietario": "laura", "titulo": "Depto luminoso en Palermo", "descripcion": "2 ambientes con balcón",
 "ciudad": "Buenos Aires", "precio_noche": "85000.00", "capacidad": 4,
 "promedio_valoracion": null, "cantidad_valoraciones": 0, "creado": "2026-10-21T23:21:01-03:00"}
```

**Buscar alojamientos libres**

```bash
curl "http://localhost:8000/api/alojamientos/?ciudad=buenos&huespedes=2&desde=2027-03-10&hasta=2027-03-14"
```

**Crear reserva (huésped)**

```bash
curl -X POST http://localhost:8000/api/reservas/ \
  -H "Authorization: Bearer $TOKEN_HUESPED" -H "Content-Type: application/json" \
  -d '{"alojamiento":1,"check_in":"2027-03-10","check_out":"2027-03-14","huespedes":2}'
```
```json
{"id": 1, "alojamiento": 1, "alojamiento_titulo": "Depto luminoso en Palermo", "huesped": "juan",
 "check_in": "2027-03-10", "check_out": "2027-03-14", "noches": 4, "huespedes": 2,
 "precio_total": "340000.00", "estado": "PENDIENTE", "monto_reembolsado": "0.00", "creada": "2026-10-21T23:21:01-03:00"}
```

**Reserva en fechas ocupadas** → `409 Conflict`

```json
{"detail": "El alojamiento no está disponible en esas fechas."}
```

**Consultar disponibilidad**

```bash
curl "http://localhost:8000/api/alojamientos/1/disponibilidad/?desde=2027-03-11&hasta=2027-03-13"
```
```json
{"alojamiento": 1, "desde": "2027-03-11", "hasta": "2027-03-13", "disponible": false,
 "fechas_ocupadas": [{"check_in": "2027-03-10", "check_out": "2027-03-14"}]}
```

**Cancelar** (con 7 o más días de anticipación → reembolso total)

```bash
curl -X POST http://localhost:8000/api/reservas/1/cancelar/ -H "Authorization: Bearer $TOKEN_HUESPED"
```
```json
{"id": 1, "estado": "CANCELADA", "monto_reembolsado": "340000.00", "...": "..."}
```

**Valorar una estadía terminada**

```bash
curl -X POST http://localhost:8000/api/valoraciones/ \
  -H "Authorization: Bearer $TOKEN_HUESPED" -H "Content-Type: application/json" \
  -d '{"reserva":1,"puntaje":5,"comentario":"Excelente ubicación"}'
```

### Códigos de error

| Código | Cuándo |
|---|---|
| 400 | Datos inválidos o regla de negocio violada (check-out anterior al check-in, capacidad excedida, valorar antes de tiempo) |
| 401 | Falta el token o está vencido |
| 403 | El rol no tiene permiso (un huésped intentando crear un alojamiento) |
| 404 | No existe o no es visible para ese usuario |
| 409 | Las fechas se solapan con otra reserva activa |

## 6. Reglas de negocio

- **Estados de la reserva:** PENDIENTE → CONFIRMADA → CANCELADA. "En curso" y "Completada" se derivan de las fechas (no se guardan), lo que evita estados desactualizados.
- **Solapamiento:** una reserva PENDIENTE o CONFIRMADA bloquea las fechas. El día de check-out queda libre para otro check-in. Cancelar libera las fechas.
- **Concurrencia:** `crear_reserva` bloquea el alojamiento con `select_for_update()` dentro de una transacción. Con PostgreSQL, dos reservas simultáneas se serializan y solo una gana. (SQLite ignora el bloqueo; por eso Docker usa PostgreSQL.)
- **Capacidad:** no se acepta más huéspedes que `capacidad`.
- **Política de cancelación:** 7 o más días de anticipación → 100 % · entre 2 y 6 días → 50 % · menos de 2 días → 0 %. No se puede cancelar una reserva que ya empezó. Las constantes están al comienzo de `reservas/services.py`.
- **Valoraciones:** solo el huésped que reservó, solo si la reserva está CONFIRMADA y el check-out ya pasó, y una sola por reserva. El promedio se calcula en la consulta.
- **Roles:** el admin no se puede crear por API (solo con `createsuperuser`). Un propietario no puede reservar su propio alojamiento.

## 7. Observabilidad

- `GET /api/health/` responde 200 si la base está arriba y 503 si no. Lo usan el healthcheck de Docker Compose y Render.
- Logger `reservas` (a consola) con eventos estructurados: `reserva_creada`, `reserva_confirmada`, `reserva_cancelada` y `reserva_rechazada_solapamiento`.
- Para el documento: a partir de esos eventos se pueden derivar métricas como tasa de cancelación, ocupación y reservas rechazadas por solapamiento. Para métricas HTTP se puede sumar `django-prometheus`.

## 8. Conexión con el frontend

- CORS: `CORS_ALLOWED_ORIGINS` (variable de entorno) define qué orígenes pueden llamar a la API. Por defecto `http://localhost:4200` (Angular) y `http://localhost:8001` (un frontend Django).
- El frontend guarda el `access` token y lo envía en `Authorization: Bearer ...`. Cuando vence (60 min) usa `/api/auth/refresh/`.
- El contrato de la API está en `/api/schema/` (OpenAPI), útil para generar clientes.

## 9. Despliegue en Render

Servicio web con entorno Docker apuntando a este repositorio, más una base PostgreSQL de Render. Variables: `SECRET_KEY`, `DEBUG=0`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` y los datos de conexión (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`). El `Dockerfile` ya ejecuta las migraciones al arrancar.

## 10. Cómo se armó, paso a paso

```bash
python -m venv .venv && source .venv/bin/activate
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers drf-spectacular
django-admin startproject config .
python manage.py startapp accounts
python manage.py startapp alojamientos
python manage.py startapp reservas
python manage.py startapp valoraciones
# 1) AUTH_USER_MODEL = "accounts.User" ANTES de la primera migración
# 2) modelos -> serializers -> services (reglas) -> views -> urls
python manage.py makemigrations accounts alojamientos reservas valoraciones
python manage.py migrate
```
