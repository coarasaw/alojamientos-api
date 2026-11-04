from rest_framework import serializers

from .models import Alojamiento


class AlojamientoSerializer(serializers.ModelSerializer):
    propietario = serializers.CharField(source="propietario.username", read_only=True)
    promedio_valoracion = serializers.SerializerMethodField()
    cantidad_valoraciones = serializers.SerializerMethodField()

    class Meta:
        model = Alojamiento
        fields = [
            "id", "propietario", "titulo", "descripcion", "ciudad", "precio_noche",
            "capacidad", "promedio_valoracion", "cantidad_valoraciones", "creado",
        ]
        read_only_fields = ["creado"]

    def get_promedio_valoracion(self, obj) -> float | None:
        promedio = getattr(obj, "promedio", None)
        return round(promedio, 2) if promedio is not None else None

    def get_cantidad_valoraciones(self, obj) -> int:
        return getattr(obj, "cantidad_valoraciones", 0)


def _validar_rango(attrs):
    if attrs["desde"] >= attrs["hasta"]:
        raise serializers.ValidationError("'hasta' debe ser posterior a 'desde'.")
    return attrs


class RangoFechasSerializer(serializers.Serializer):
    """Parámetros obligatorios para consultar disponibilidad."""

    desde = serializers.DateField()
    hasta = serializers.DateField()

    def validate(self, attrs):
        return _validar_rango(attrs)


class FiltrosBusquedaSerializer(serializers.Serializer):
    """Parámetros opcionales de búsqueda de alojamientos."""

    ciudad = serializers.CharField(required=False)
    huespedes = serializers.IntegerField(required=False, min_value=1)
    precio_max = serializers.DecimalField(required=False, max_digits=10, decimal_places=2)
    desde = serializers.DateField(required=False)
    hasta = serializers.DateField(required=False)

    def validate(self, attrs):
        if ("desde" in attrs) != ("hasta" in attrs):
            raise serializers.ValidationError("Hay que enviar 'desde' y 'hasta' juntos.")
        if "desde" in attrs:
            _validar_rango(attrs)
        return attrs
