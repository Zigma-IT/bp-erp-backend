from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Department, Employee, ManualAttendance


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data["username"], password=data["password"])
        if not user:
            raise serializers.ValidationError("Invalid username or password")
        data["user"] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError({"new_password": "New passwords do not match"})

        user = self.context["request"].user
        if not user.check_password(data["old_password"]):
            raise serializers.ValidationError({"old_password": "Old password is incorrect"})

        return data


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "description", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class EmployeeListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "user",
            "employee_id",
            "department",
            "designation",
            "phone",
            "date_of_joining",
            "is_active",
        ]


class EmployeeCreateUpdateSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(source="user", queryset=User.objects.all(), write_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        source="department",
        queryset=Department.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Employee
        fields = [
            "id",
            "user_id",
            "employee_id",
            "department_id",
            "designation",
            "phone",
            "date_of_joining",
            "is_active",
        ]


class ManualAttendanceListSerializer(serializers.ModelSerializer):
    employee = EmployeeListSerializer(read_only=True)
    recorded_by = UserSerializer(read_only=True)

    class Meta:
        model = ManualAttendance
        fields = [
            "id",
            "employee",
            "attendance_date",
            "status",
            "check_in_time",
            "check_out_time",
            "remarks",
            "recorded_by",
            "recorded_at",
            "updated_at",
        ]
        read_only_fields = ["recorded_at", "updated_at", "recorded_by"]


class ManualAttendanceCreateUpdateSerializer(serializers.ModelSerializer):
    employee_id = serializers.PrimaryKeyRelatedField(source="employee", queryset=Employee.objects.all(), write_only=True)

    class Meta:
        model = ManualAttendance
        fields = ["id", "employee_id", "attendance_date", "status", "check_in_time", "check_out_time", "remarks"]

    def create(self, validated_data):
        return ManualAttendance.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
