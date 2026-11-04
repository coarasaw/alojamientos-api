from rest_framework import serializers

from .models import Reserva


class ReservaCreateSerializer(serializers.Serializer):
    alojamiento = serializers.IntegerField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    huespedes = serializers.IntegerField(min_value=1)


class ReservaSerializer(serializers.ModelSerializer):
    alojamiento_titulo = serializers.CharField(source="alojamiento.titulo", read_only=True)
    huesped = serializers.CharField(source="huesped.username", read_only=True)
    noches = serializers.IntegerField(read_only=True)

    class Meta:
        model = Reserva
        fields = [
            "id", "alojamiento", "alojamiento_titulo", "huesped", "check_in", "check_out",
            "noches", "huespedes", "precio_total", "estado", "monto_reembolsado", "creada",
        ]
