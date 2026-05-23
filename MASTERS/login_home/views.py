"""Auth, employee, and attendance APIs for the login/home module."""

from typing import Any, cast

from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Department, Employee, ManualAttendance
from .serializers import (
    UserSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    DepartmentSerializer,
    EmployeeListSerializer,
    EmployeeCreateUpdateSerializer,
    ManualAttendanceListSerializer,
    ManualAttendanceCreateUpdateSerializer,
)


@extend_schema_view(
    login=extend_schema(request=LoginSerializer, responses=OpenApiTypes.OBJECT),
    me=extend_schema(responses=UserSerializer),
    logout=extend_schema(responses=OpenApiTypes.OBJECT),
    change_password=extend_schema(
        request=ChangePasswordSerializer,
        responses=OpenApiTypes.OBJECT,
    ),
)
class AuthViewSet(viewsets.ViewSet):
    """
    API endpoint for user authentication
    """
    serializer_class = LoginSerializer

    def get_serializer_class(self):
        serializers_map = {
            "login": LoginSerializer,
            "change_password": ChangePasswordSerializer,
            "me": UserSerializer,
        }
        return serializers_map.get(self.action, LoginSerializer)


    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        Login user and return auth token
        """
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            assert isinstance(validated_data, dict)
            user = cast(User, validated_data["user"])
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data,
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Get current logged-in user details
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Logout user by deleting token
        """
        request.user.auth_token.delete()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='my_permissions')
    def my_permissions(self, request):
        """
        Return the permission tree for the logged-in user based on their UserType.
        Returns all_access=True for super admins / users without a UserCreation record.
        """
        from admin_master.models import UserCreation, UserTypePermission

        try:
            user_creation = UserCreation.objects.select_related('user_type').get(
                username=request.user.username
            )
        except UserCreation.DoesNotExist:
            return Response({
                "all_access": True,
                "user_type": None,
                "user_type_name": "Super Admin",
                "main_screens": [],
            })

        if not user_creation.user_type:
            return Response({
                "all_access": True,
                "user_type": None,
                "user_type_name": "No User Type",
                "main_screens": [],
            })

        user_type = user_creation.user_type

        permissions = (
            UserTypePermission.objects
            .select_related('main_screen', 'user_screen', 'user_screen__screen_section')
            .filter(user_type=user_type, status=True)
            .order_by(
                'main_screen__order_no', 'main_screen__name',
                'user_screen__screen_section__order_no',
                'user_screen__order_no',
            )
        )

        main_screens: dict = {}
        for perm in permissions:
            ms = perm.main_screen
            if ms.id not in main_screens:
                main_screens[ms.id] = {
                    "id": ms.id,
                    "name": ms.name,
                    "folder_key": ms.folder_key or "",
                    "order_no": ms.order_no,
                    "screens": [],
                }
            if perm.user_screen:
                us = perm.user_screen
                main_screens[ms.id]["screens"].append({
                    "id": us.id,
                    "screen_name": us.screen_name,
                    "folder_name": us.folder_name,
                    "section_id": us.screen_section_id,
                    "section_name": us.screen_section.name if us.screen_section_id else "",
                    "order_no": us.order_no,
                    "can_add": perm.can_add,
                    "can_update": perm.can_update,
                    "can_list": perm.can_list,
                    "can_delete": perm.can_delete,
                    "can_view": perm.can_view,
                    "can_print": perm.can_print,
                })

        sorted_screens = sorted(
            main_screens.values(), key=lambda x: (x["order_no"], x["name"])
        )

        return Response({
            "all_access": False,
            "user_type": user_type.id,
            "user_type_name": user_type.name,
            "main_screens": sorted_screens,
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Change user password
        """
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            validated_data = serializer.validated_data
            assert isinstance(validated_data, dict)
            user = request.user
            user.set_password(cast(str, validated_data["new_password"]))
            user.save()
            return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related('user', 'department').all()
    serializer_class = EmployeeListSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self) -> type[serializers.BaseSerializer[Any]]:  # pyright: ignore[reportIncompatibleMethodOverride]
        if self.action in ['create', 'update', 'partial_update']:
            return EmployeeCreateUpdateSerializer
        return EmployeeListSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's employee profile"""
        try:
            employee = Employee.objects.get(user=request.user)
            serializer = EmployeeListSerializer(employee)
            return Response(serializer.data)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)


class ManualAttendanceViewSet(viewsets.ModelViewSet):
    queryset = ManualAttendance.objects.select_related('employee', 'recorded_by').all()
    serializer_class = ManualAttendanceListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[ManualAttendance]:  # pyright: ignore[reportIncompatibleMethodOverride]
        request = cast(Request, self.request)
        queryset = self.queryset.all()
        
        # Filter by date range if provided
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(attendance_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(attendance_date__lte=date_to)
        
        # Filter by employee if provided
        employee_id = request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-attendance_date')

    def get_serializer_class(self) -> type[serializers.BaseSerializer[Any]]:  # pyright: ignore[reportIncompatibleMethodOverride]
        if self.action in ['create', 'update', 'partial_update']:
            return ManualAttendanceCreateUpdateSerializer
        return ManualAttendanceListSerializer

    def perform_create(self, serializer: ManualAttendanceCreateUpdateSerializer) -> None:
        request = cast(Request, self.request)
        serializer.save(recorded_by=request.user)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create attendance records"""
        attendances = request.data
        if not isinstance(attendances, list):
            return Response({'error': 'Expected a list of attendance records'}, status=status.HTTP_400_BAD_REQUEST)
        
        created_records = []
        errors = []
        
        for attendance_data in attendances:
            serializer = ManualAttendanceCreateUpdateSerializer(
                data=attendance_data,
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save(recorded_by=request.user)
                created_records.append(serializer.data)
            else:
                errors.append(serializer.errors)
        
        return Response(
            {
                'created': created_records,
                'errors': errors,
                'total_created': len(created_records),
                'total_errors': len(errors)
            },
            status=status.HTTP_201_CREATED if created_records else status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's attendance records"""
        today = timezone.now().date()
        queryset = ManualAttendance.objects.filter(attendance_date=today).select_related('employee', 'recorded_by')
        serializer = ManualAttendanceListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def employee_attendance(self, request):
        """Get attendance for a specific employee"""
        employee_id = request.query_params.get('employee_id')
        if not employee_id:
            return Response({'error': 'employee_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = ManualAttendance.objects.filter(
            employee_id=employee_id
        ).select_related('employee', 'recorded_by').order_by('-attendance_date')
        
        # Pagination support
        limit = request.query_params.get('limit', 30)
        queryset = queryset[:int(limit)]
        
        serializer = ManualAttendanceListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get attendance statistics"""
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        employee_id = request.query_params.get('employee_id')
        
        queryset = ManualAttendance.objects.all()
        
        if date_from:
            queryset = queryset.filter(attendance_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(attendance_date__lte=date_to)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        stats = {
            'total': queryset.count(),
            'present': queryset.filter(status='present').count(),
            'absent': queryset.filter(status='absent').count(),
            'leave': queryset.filter(status='leave').count(),
            'half_day': queryset.filter(status='half_day').count(),
        }
        
        return Response(stats)
