from rest_framework import serializers
from .models import (
    DepartmentCreation,
    DesignationCreation,
    StaffCreation,
    StaffEmploymentStatus,
    StaffDependentDetails,
    StaffAccountDetails,
    StaffQualificationDetails,
    LwfEntry,
    ProfessionalTax,
    LeaveMasterCreation,
    ReasonCreation,
    PayCycle,
    SalaryCategory,
    GradeMaster,
    BandMaster,
    LevelMaster,
)


class DepartmentCreationSerializer(serializers.ModelSerializer):

    class Meta:
        model = DepartmentCreation
        fields = '__all__'


class DesignationCreationSerializer(serializers.ModelSerializer):

    band_name = serializers.CharField(source='band.band_name', read_only=True)
    level_name = serializers.CharField(source='level.level_name', read_only=True)

    class Meta:
        model = DesignationCreation
        fields = '__all__'


class StaffCreationSerializer(serializers.ModelSerializer):

    class Meta:
        model = StaffCreation
        fields = '__all__'

class StaffEmploymentStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = StaffEmploymentStatus
        fields = '__all__'


class StaffDependentDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = StaffDependentDetails
        fields = '__all__'

class StaffAccountDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = StaffAccountDetails
        fields = '__all__'


class StaffQualificationSerializer(serializers.ModelSerializer):

    class Meta:

        model = StaffQualificationDetails

        fields = '__all__'


class LwfEntrySerializer(serializers.ModelSerializer):

    class Meta:

        model = LwfEntry

        fields = "__all__"

class ProfessionalTaxSerializer(serializers.ModelSerializer):

    class Meta:

        model = ProfessionalTax

        fields = "__all__"

class LeaveMasterCreationSerializer(serializers.ModelSerializer):

    class Meta:

        model = LeaveMasterCreation

        fields = "__all__"


class ReasonCreationSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReasonCreation
        fields = "__all__"

class PayCycleSerializer(serializers.ModelSerializer):

    class Meta:
        model = PayCycle
        fields = "__all__"

class SalaryCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SalaryCategory
        fields = "__all__"

class GradeMasterSerializer(serializers.ModelSerializer):

    class Meta:
        model = GradeMaster
        fields = "__all__"


class BandMasterSerializer(serializers.ModelSerializer):

    class Meta:
        model = BandMaster
        fields = "__all__"


class LevelMasterSerializer(serializers.ModelSerializer):

    band_name = serializers.CharField(source="band.band_name", read_only=True)

    class Meta:
        model = LevelMaster
        fields = "__all__"