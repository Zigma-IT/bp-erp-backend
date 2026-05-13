from rest_framework import serializers
from .models import DepartmentCreation, DesignationCreation, StaffCreation, StaffEmploymentStatus,StaffDependentDetails, StaffAccountDetails


class DepartmentCreationSerializer(serializers.ModelSerializer):

    class Meta:
        model = DepartmentCreation
        fields = '__all__'


class DesignationCreationSerializer(serializers.ModelSerializer):

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