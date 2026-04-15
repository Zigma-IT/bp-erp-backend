# Login and Change Password views for the Admin app, providing API endpoints for user authentication, retrieving user details, logging out, and changing passwords in the MASTERS app.
# Home page views for managing departments, employees, and manual attendance records in the admin module of the MASTERS app.
from django.shortcuts import render
from rest_framework import status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

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
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view


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
            user = serializer.validated_data['user']
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
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Home page views for managing departments, employees, and manual attendance records in the admin module of the MASTERS app.
from django.shortcuts import render
from rest_framework import viewsets, status,serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .models import Department, Employee, ManualAttendance
from .serializers import (
    DepartmentSerializer,
    EmployeeListSerializer,
    EmployeeCreateUpdateSerializer,
    ManualAttendanceListSerializer,
    ManualAttendanceCreateUpdateSerializer,
)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related('user', 'department').all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ManualAttendance.objects.select_related('employee', 'recorded_by').all()
        
        # Filter by date range if provided
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(attendance_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(attendance_date__lte=date_to)
        
        # Filter by employee if provided
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-attendance_date')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ManualAttendanceCreateUpdateSerializer
        return ManualAttendanceListSerializer

    def perform_create(self, serializer):
        # Ensure employee_id exists
        employee_id = self.request.data.get('employee_id')
        try:
            employee = Employee.objects.get(id=employee_id)
            serializer.save(recorded_by=self.request.user)
        except Employee.DoesNotExist:
            raise serializers.ValidationError({'employee_id': 'Employee not found'})

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
