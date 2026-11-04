from django.utils import timezone
from rest_framework import serializers

from reservas.models import Reserva

from .models import Valoracion


class ValoracionSerializer(serializers.ModelSerializer):
    autor = serializers.CharField(source="reserva.huesped.username", read_only=True)
    alojamiento = serializers.IntegerField(source="reserva.alojamiento_id", read_only=True)

    class Meta:
        model = Valoracion
        fields = ["id", "reserva", "alojamiento", "autor", "puntaje", "comentario", "creada"]
        read_only_fields = ["creada"]

    def validate_reserva(self, reserva):
        user = self.context["request"].user
        if reserva.huesped_id != user.id:
            raise serializers.ValidationError("Solo podés valorar tus propias reservas.")
        if reserva.estado != Reserva.Estado.CONFIRMADA or reserva.check_out > timezone.localdate():
            raise serializers.ValidationError(
                "Solo se puede valorar una estadía confirmada y ya finalizada."
            )
        return reserva
