"""Serializers for admin master setup screens.

These serializers support user creation, screen mapping, user types, and
permission assignment screens used by the admin module.
"""

from rest_framework import serializers
from django.contrib.auth.models import User as AuthUser

from .models import MainScreen, Role, Staff, UserCreation, UserScreen, UserType, UserTypePermission, ScreenSection
from hr_master.models import StaffCreation


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(write_only=True)
    staff = serializers.CharField(write_only=True)
    user_type = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    role_name = serializers.CharField(source="role.name", read_only=True)
    staff_name = serializers.CharField(source="staff.name", read_only=True)
    user_type_name = serializers.CharField(source="user_type.name", read_only=True)

    class Meta:
        model = UserCreation
        fields = "__all__"

    def _resolve_staff(self, value, *, mobile="0000000000"):
        if value in (None, ""):
            return value

        if isinstance(value, Staff):
            return value

        value_str = str(value).strip()
        if not value_str:
            return value

        if value_str.isdigit():
            existing = Staff.objects.filter(pk=int(value_str)).first()
            if existing:
                return existing

            hr_staff = StaffCreation.objects.filter(staff_id=int(value_str), is_delete=False).first()
            if hr_staff:
                return Staff.objects.filter(name__iexact=hr_staff.staff_name).first() or Staff.objects.create(
                    name=hr_staff.staff_name,
                    mobile=hr_staff.personal_contact_no or mobile,
                )

        existing = Staff.objects.filter(name__iexact=value_str).first()
        if existing:
            return existing

        hr_staff = StaffCreation.objects.filter(staff_name__iexact=value_str, is_delete=False).first()
        if hr_staff:
            return Staff.objects.filter(name__iexact=hr_staff.staff_name).first() or Staff.objects.create(
                name=hr_staff.staff_name,
                mobile=hr_staff.personal_contact_no or mobile,
            )

        return Staff.objects.create(name=value_str, mobile=mobile)

    def _sync_auth_user(self, instance, raw_password=None):
        auth_user = AuthUser.objects.filter(username=instance.username).first()
        if auth_user is None:
            auth_user = AuthUser(username=instance.username)

        auth_user.first_name = instance.staff.name if instance.staff_id else ""
        auth_user.is_active = instance.is_active

        if raw_password:
            auth_user.set_password(raw_password)

        auth_user.save()

    def _resolve_related(self, model, value, *, defaults=None, allow_null=False):
        if value in (None, ""):
            return None if allow_null else value

        if isinstance(value, model):
            return value

        value_str = str(value).strip()
        if not value_str:
            return None if allow_null else value

        if value_str.isdigit():
            existing = model.objects.filter(pk=int(value_str)).first()
            if existing:
                return existing

        existing = model.objects.filter(name__iexact=value_str).first()
        if existing:
            return existing

        return model.objects.create(name=value_str, **(defaults or {}))

    def create(self, validated_data):
        mobile = validated_data.get("mobile") or "0000000000"
        raw_password = validated_data.get("password")
        role_value = validated_data.pop("role")
        staff_value = validated_data.pop("staff")
        user_type_value = validated_data.pop("user_type", None)

        validated_data["role"] = self._resolve_related(Role, role_value)
        validated_data["staff"] = self._resolve_staff(staff_value, mobile=mobile)
        validated_data["user_type"] = self._resolve_related(
            UserType,
            user_type_value,
            allow_null=True,
        )

        instance = super().create(validated_data)
        self._sync_auth_user(instance, raw_password=raw_password)
        return instance

    def update(self, instance, validated_data):
        raw_password = validated_data.get("password")
        if "role" in validated_data:
            validated_data["role"] = self._resolve_related(Role, validated_data["role"])

        if "staff" in validated_data:
            validated_data["staff"] = self._resolve_staff(
                validated_data["staff"],
                mobile=validated_data.get("mobile") or instance.mobile or "0000000000",
            )

        if "user_type" in validated_data:
            validated_data["user_type"] = self._resolve_related(
                UserType,
                validated_data["user_type"],
                allow_null=True,
            )

        instance = super().update(instance, validated_data)
        self._sync_auth_user(instance, raw_password=raw_password)
        return instance


class UserScreenSerializer(serializers.ModelSerializer):
    main_screen_name = serializers.CharField(source="main_screen.name", read_only=True)
    screen_section_name = serializers.CharField(source="screen_section.name", read_only=True)
  
    class Meta:
        model = UserScreen
        fields = "__all__"

    
class UserTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserType
        fields = "__all__"


class MainScreenSerializer(serializers.ModelSerializer):
    active_status = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MainScreen
        fields = "__all__"

    def get_active_status(self, obj):
        return "Active" if obj.status else "Inactive"

    def validate_folder_key(self, value):
        if value in (None, ""):
            return value
        return str(value).strip().lower().replace(" ", "-").replace("_", "-")

   

class UserTypePermissionSerializer(serializers.ModelSerializer):
    user_type = serializers.PrimaryKeyRelatedField(queryset=UserType.objects.all())
    main_screen = serializers.PrimaryKeyRelatedField(queryset=MainScreen.objects.all())
    user_screen = serializers.PrimaryKeyRelatedField(
        queryset=UserScreen.objects.all(),
        required=False,
        allow_null=True,
    )
    user_type_name = serializers.CharField(source="user_type.name", read_only=True)
    main_screen_name = serializers.CharField(source="main_screen.name", read_only=True)
    screen_name = serializers.CharField(source="user_screen.screen_name", read_only=True)
    screen_section = serializers.IntegerField(source="user_screen.screen_section_id", read_only=True)
    screen_section_name = serializers.CharField(source="user_screen.screen_section.name", read_only=True)

    class Meta:
        model = UserTypePermission
        fields = "__all__"

    def validate(self, attrs):
        user_screen = attrs.get("user_screen") or getattr(self.instance, "user_screen", None)
        main_screen = attrs.get("main_screen") or getattr(self.instance, "main_screen", None)

        if user_screen and main_screen and user_screen.main_screen_id != main_screen.id:
            raise serializers.ValidationError(
                {"user_screen": "Selected screen does not belong to the selected main screen."}
            )

        return attrs
class ScreenSectionSerializer(serializers.ModelSerializer):
    main_screen_name = serializers.CharField(
        source='main_screen.name',
        read_only=True
    )
    active_status = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ScreenSection
        fields = "__all__"

    def get_active_status(self, obj):
        return "Active" if obj.is_active else "Inactive"
