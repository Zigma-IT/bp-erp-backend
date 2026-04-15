from rest_framework import serializers

<<<<<<< HEAD
from .models import MainScreen, UserCreation, UserScreen, UserType, UserTypePermission
=======
from .models import MainScreen, Role, Staff, User, UserScreen, UserType, UserTypePermission
>>>>>>> origin/dev


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
        role_value = validated_data.pop("role")
        staff_value = validated_data.pop("staff")
        user_type_value = validated_data.pop("user_type", None)

        validated_data["role"] = self._resolve_related(Role, role_value)
        validated_data["staff"] = self._resolve_related(
            Staff,
            staff_value,
            defaults={"mobile": mobile},
        )
        validated_data["user_type"] = self._resolve_related(
            UserType,
            user_type_value,
            allow_null=True,
        )

        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "role" in validated_data:
            validated_data["role"] = self._resolve_related(Role, validated_data["role"])

        if "staff" in validated_data:
            validated_data["staff"] = self._resolve_related(
                Staff,
                validated_data["staff"],
                defaults={"mobile": validated_data.get("mobile") or instance.mobile or "0000000000"},
            )

        if "user_type" in validated_data:
            validated_data["user_type"] = self._resolve_related(
                UserType,
                validated_data["user_type"],
                allow_null=True,
            )

        return super().update(instance, validated_data)


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
    class Meta:
        model = MainScreen
        fields = "__all__"


class UserTypePermissionSerializer(serializers.ModelSerializer):
    user_type = serializers.PrimaryKeyRelatedField(queryset=UserType.objects.all())
    main_screen = serializers.PrimaryKeyRelatedField(queryset=MainScreen.objects.all())
    user_type_name = serializers.CharField(source="user_type.name", read_only=True)
    main_screen_name = serializers.CharField(source="main_screen.name", read_only=True)

    class Meta:
        model = UserTypePermission
        fields = "__all__"
