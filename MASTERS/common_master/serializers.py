from rest_framework import serializers

from .models import City, Continent, Country, State, Tax


class ContinentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Continent
        fields = "__all__"


class CountrySerializer(serializers.ModelSerializer):
    continent_name = serializers.CharField(source="continent.name", read_only=True)

    class Meta:
        model = Country
        fields = "__all__"


class StateSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = State
        fields = ["id", "name", "country", "country_name", "is_active", "created_at"]
        read_only_fields = ["created_at"]


class CitySerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True)
    state_name = serializers.CharField(source="state.name", read_only=True)
    city_type_name = serializers.CharField(source="city_type.name", read_only=True)

    class Meta:
        model = City
        fields = [
            "id",
            "country",
            "country_name",
            "state",
            "state_name",
            "name",
            "pincode",
            "city_type",
            "city_type_name",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate(self, data):
        if not data.get("name"):
            raise serializers.ValidationError("City name required")
        if not data.get("state"):
            raise serializers.ValidationError("State required")
        return data


class TaxSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = Tax
        fields = [
            "id",
            "country",
            "country_name",
            "name",
            "value",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate(self, data):
        if not data.get("name"):
            raise serializers.ValidationError("Tax name required")
        if data.get("value") is None:
            raise serializers.ValidationError("Tax value required")
        if float(data["value"]) < 0:
            raise serializers.ValidationError("Tax cannot be negative")
        return data
