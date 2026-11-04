from rest_framework import serializers

from .models import User


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    # Por API solo se puede ser huésped o propietario; el admin se crea por consola
    rol = serializers.ChoiceField(
        choices=[User.Rol.HUESPED, User.Rol.PROPIETARIO], default=User.Rol.HUESPED
    )

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "rol"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "rol"]
