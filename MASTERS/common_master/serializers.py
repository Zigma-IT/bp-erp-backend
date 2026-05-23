"""Serializers for shared geography, tax, company, and project masters."""

from django.db import connections
from django.db.models import Q
from rest_framework import serializers

from .models import (
    City,
    Continent,
    Country,
    State,
    Tax,
    CommonMaster,
    Company,
    Project,
    CustomerProfile,
    CustomerContactPerson,
    CustomerStatutoryDetails,
    CustomerAccountDetails,
    CustomerBillingDetails,
    CustomerShippingDetails,
    CustomerDocument,
    SupplierProfile,
    SupplierContactPerson,
    SupplierAccountDetails,
    SupplierStatutoryDetails, 
    SupplierBillingDetails,
    SupplierShippingDetails,
    SupplierDocuments,
)


def _masters_db_alias() -> str:
    return "masters_db" if "masters_db" in connections.databases else "default"


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

    def validate(self, attrs):
        if not attrs.get("name"):
            raise serializers.ValidationError("City name required")
        if not attrs.get("state"):
            raise serializers.ValidationError("State required")
        return attrs


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

    def validate(self, attrs):
        if not attrs.get("name"):
            raise serializers.ValidationError("Tax name required")
        if attrs.get("value") is None:
            raise serializers.ValidationError("Tax value required")
        if float(attrs["value"]) < 0:
            raise serializers.ValidationError("Tax cannot be negative")
        return attrs



# Company creation
class CompanySerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True)
    state_name = serializers.CharField(source="state.name", read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True)

    class Meta:
        model = Company
        fields = "__all__"


class ApplicationTypeRelatedField(serializers.PrimaryKeyRelatedField):
    """Accept numeric IDs even when they arrive as quoted strings from the UI."""

    def to_internal_value(self, data):
        if data in (None, ""):
            return None

        if isinstance(data, str):
            cleaned = data.strip()

            while len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
                cleaned = cleaned[1:-1].strip()

            cleaned = cleaned.replace("\\", "")

            if cleaned == "":
                return None

            if cleaned.isdigit():
                data = int(cleaned)
            else:
                data = cleaned

        return super().to_internal_value(data)


# Project Creation
class ProjectSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    state_name = serializers.CharField(source="state.name", read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True)
    application_type_name = serializers.CharField(source="application_type.name", read_only=True)
    application_type = ApplicationTypeRelatedField(
        queryset=CommonMaster.objects.filter(
            Q(type="APPLICATION_TYPE")
            | Q(type="Application Type")
            | Q(type="APPLICATION TYPE")
        ),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Project
        fields = "__all__"

class CustomerProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="pk", read_only=True)

    class Meta:
        model = CustomerProfile
        fields = [
            "id",
            "unique_id",
            "customer_name",
            "customer_no",
            "customer_group_id",
            "customer_sub_category_id",
            "property",
            "currency",
            "country",
            "state",
            "city",
            "address",
            "pincode",
            "gst_status",
            "gst_no",
            "pan_no",
            "mobile_no",
            "phone_no",
            "email_id",
            "provisional_status",
            "provisional_no",
            "is_active",
            "is_delete",
            "created_at",
            "updated_at",
            "acc_year",
            "session_id",
            "sess_user_type",
            "sess_user_id",
            "sess_company_id",
            "sess_branch_id",
        ]
        read_only_fields = [
            "id",
            "unique_id",
            "created_at",
            "updated_at",
        ]

    @staticmethod
    def _coerce_blankable_fields(validated_data, *, fill_missing):
        text_fields = [
            "currency",
            "address",
            "pincode",
            "gst_no",
            "pan_no",
            "phone_no",
            "email_id",
            "provisional_no",
            "acc_year",
            "session_id",
            "sess_user_type",
        ]
        integer_fields = [
            "customer_group_id",
            "customer_sub_category_id",
            "sess_user_id",
            "sess_company_id",
            "sess_branch_id",
        ]

        for field_name in text_fields:
            if fill_missing:
                if validated_data.get(field_name) is None:
                    validated_data[field_name] = ""
            elif field_name in validated_data and validated_data[field_name] is None:
                validated_data[field_name] = ""

        for field_name in integer_fields:
            if fill_missing:
                validated_data.setdefault(field_name, None)
            elif field_name in validated_data and validated_data[field_name] == "":
                validated_data[field_name] = None
        return validated_data

    @staticmethod
    def _resolve_unique_id(model_class, pk):
        if pk in (None, ""):
            return ""
        value = (
            model_class.objects.using(_masters_db_alias())
            .filter(pk=pk)
            .values_list("unique_id", flat=True)
            .first()
        )
        return str(value) if value else ""

    @staticmethod
    def _resolve_pk(model_class, unique_id):
        if not unique_id:
            return None
        try:
            return (
                model_class.objects.using(_masters_db_alias())
                .filter(unique_id=unique_id)
                .values_list("pk", flat=True)
                .first()
            )
        except Exception:
            return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data

    def create(self, validated_data):
        return super().create(self._coerce_blankable_fields(validated_data, fill_missing=True))

    def update(self, instance, validated_data):
        return super().update(
            instance,
            self._coerce_blankable_fields(validated_data, fill_missing=False),
        )


class CustomerContactPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerContactPerson
        fields = "__all__"


class CustomerStatutoryDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerStatutoryDetails
        fields = "__all__"


class CustomerAccountDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAccountDetails
        fields = "__all__"


class CustomerBillingDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerBillingDetails
        fields = "__all__"
class CustomerShippingDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerShippingDetails
        fields = "__all__"

class CustomerDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerDocument
        fields = "__all__"


class SupplierProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="pk", read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        db_alias = _masters_db_alias()
        related_querysets = {
            "group": CommonMaster.objects.using(db_alias).all(),
            "country": Country.objects.using(db_alias).all(),
            "state": State.objects.using(db_alias).all(),
            "city": City.objects.using(db_alias).all(),
            "msme_type": CommonMaster.objects.using(db_alias).all(),
            "project": Project.objects.using(db_alias).all(),
        }
        for field_name, queryset in related_querysets.items():
            field = self.fields.get(field_name)
            if field is not None and hasattr(field, "queryset"):
                field.queryset = queryset

    @staticmethod
    def _normalize_optional_fields(validated_data):
        text_fields = [
            "currency",
            "reference",
            "pincode",
            "address",
            "corporate_address",
            "phone_no",
            "fax_no",
            "pan_no",
            "gst_no",
            "email_id",
            "website",
            "arn_no",
            "acc_year",
            "session_id",
            "sess_user_type",
        ]
        integer_fields = [
            "sess_user_id",
            "sess_company_id",
            "sess_branch_id",
        ]

        for field_name in text_fields:
            if field_name in validated_data and validated_data[field_name] is None:
                validated_data[field_name] = ""

        for field_name in integer_fields:
            if field_name in validated_data and validated_data[field_name] == "":
                validated_data[field_name] = None

        return validated_data

    def create(self, validated_data):
        return super().create(self._normalize_optional_fields(validated_data))

    def update(self, instance, validated_data):
        return super().update(instance, self._normalize_optional_fields(validated_data))

    class Meta:
        model = SupplierProfile
        fields = "__all__"


class SupplierContactPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierContactPerson
        fields = "__all__"



class SupplierStatutoryDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierStatutoryDetails
        fields = "__all__"

class SupplierAccountDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierAccountDetails
        fields = "__all__"


class SupplierBillingDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierBillingDetails
        fields = "__all__"

class SupplierShippingDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierShippingDetails
        fields = "__all__"        

class SupplierDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierDocuments
        fields = "__all__"
