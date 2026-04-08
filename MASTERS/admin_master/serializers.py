from rest_framework import serializers

from .models import MainScreen, UserCreation, UserScreen, UserType, UserTypePermission


class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)
    staff_name = serializers.CharField(source="staff.name", read_only=True)
    user_type_name = serializers.CharField(source="user_type.name", read_only=True)

    class Meta:
        model = UserCreation
        fields = "__all__"


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
    user_type_name = serializers.CharField(source="user_type.name", read_only=True)
    main_screen_name = serializers.CharField(source="main_screen.name", read_only=True)

    class Meta:
        model = UserTypePermission
        fields = "__all__"
