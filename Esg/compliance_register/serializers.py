from rest_framework import serializers
from .models import (    ESGComplianceRegister,
    ESGComplianceEntry,
    ESGComplianceHistory,
    ESGComplianceStateLog,
    ESGComplianceMailLog,
    InsuranceRegister,
    InsuranceRegisterDetail,

)


class ESGComplianceRegisterSerializer(serializers.ModelSerializer):
    unique_id = serializers.CharField(read_only=True)

    class Meta:
        model = ESGComplianceRegister
        fields = "__all__"


class ESGComplianceEntrySerializer(serializers.ModelSerializer):
    unique_id = serializers.CharField(read_only=True)

    class Meta:
        model = ESGComplianceEntry
        fields = "__all__"


class ESGComplianceHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ESGComplianceHistory
        fields = "__all__"

class InsuranceRegisterDetailSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = InsuranceRegisterDetail
        fields = "__all__"
        read_only_fields = ["register"]

class InsuranceRegisterSerializer(
    serializers.ModelSerializer
):
    unique_id = serializers.CharField(read_only=True)
    details = InsuranceRegisterDetailSerializer(
        many=True
    )

    class Meta:
        model = InsuranceRegister
        fields = "__all__"

    def create(self, validated_data):

        details_data = validated_data.pop(
            "details"
        )

        register = InsuranceRegister.objects.create(
            **validated_data
        )

        for item in details_data:

            InsuranceRegisterDetail.objects.create(
                register=register,
                **item
            )

        return register
