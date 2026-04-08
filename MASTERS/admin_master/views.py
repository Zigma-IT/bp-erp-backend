# user_creations - This file defines the API views for the user creations module in the MASTERS app, including functions for listing users with pagination and search functionality, creating new users, updating existing users, and toggling user status. These views handle HTTP requests and return appropriate responses based on the operations performed on the User model.
from django.shortcuts import render
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from MASTERS.schema_utils import DATATABLE_PARAMETERS, query_int_parameter
from .models import UserCreation
from .serializers import UserSerializer


@api_view(['GET'])
def user_list(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    queryset = UserCreation.objects.select_related('role', 'staff', 'user_type')

    total_records = queryset.count()

    if search_value:
        queryset = queryset.filter(
            Q(username__icontains=search_value) |
            Q(staff__name__icontains=search_value) |
            Q(mobile__icontains=search_value)
        )

    filtered_records = queryset.count()

    queryset = queryset[start:start+length]

    serializer = UserSerializer(queryset, many=True)

    data = []
    for i, item in enumerate(serializer.data, start=1):
        data.append({
            "sno": start + i,
            "name": item["staff_name"],
            "phone": item["mobile"],
            "username": item["username"],
            "user_type": item["user_type_name"],
            "work_location": item["project"],
            "status": "Active" if item["is_active"] else "Inactive",
            "id": item["id"]
        })

    return Response({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": filtered_records,
        "data": data
    })

@api_view(['POST'])
def create_user(request):
    serializer = UserSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User created successfully"})
    
    return Response(serializer.errors, status=400)

@api_view(['PUT'])
def update_user(request, pk):
    try:
        user = UserCreation.objects.get(pk=pk)
    except UserCreation.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    serializer = UserSerializer(user, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Updated successfully"})
    
    return Response(serializer.errors, status=400)


@api_view(['PATCH'])
def toggle_user_status(request, pk):
    try:
        user = UserCreation.objects.get(pk=pk)
        user.is_active = not user.is_active
        user.save()
        return Response({"status": user.is_active})
    except UserCreation.DoesNotExist:
        return Response({"error": "Not found"}, status=404)
    

# user_screens - This file defines the API views for managing user screens in the admin module of the MASTERS app, including functions for listing user screens with pagination and search functionality, creating new user screens, updating existing user screens, toggling user screen status, and retrieving main screen and screen section lists. These views handle HTTP requests and return appropriate responses based on the operations performed on the UserScreen model and related entities.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from .models import ScreenSection, UserScreen
from .serializers import UserScreenSerializer


@api_view(['GET'])
def user_screen_list(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search = request.GET.get('search[value]', '')

    queryset = UserScreen.objects.select_related('main_screen', 'screen_section')

    total = queryset.count()

    if search:
        queryset = queryset.filter(
            Q(screen_name__icontains=search) |
            Q(folder_name__icontains=search) |
            Q(main_screen__name__icontains=search) |
            Q(screen_section__name__icontains=search)
        )

    filtered = queryset.count()

    queryset = queryset[start:start+length]

    serializer = UserScreenSerializer(queryset, many=True)

    data = []
    for i, item in enumerate(serializer.data, start=1):
        data.append({
            "sno": start + i,
            "screen_name": item["screen_name"],
            "screen_section": item["screen_section_name"],
            "main_screen": item["main_screen_name"],
            "order_no": item["order_no"],
            "status": "Active" if item["is_active"] else "Inactive",
            "id": item["id"]
        })

    return Response({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": filtered,
        "data": data
    })

@api_view(['POST'])
def create_user_screen(request):
    data = request.data.copy()

    # Handle "All" checkbox
    if data.get('all_permissions'):
        data['can_add'] = True
        data['can_update'] = True
        data['can_list'] = True
        data['can_delete'] = True
        data['can_view'] = True
        data['can_print'] = True

    serializer = UserScreenSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Created successfully"})
    
    return Response(serializer.errors, status=400)


@api_view(['PUT'])
def update_user_screen(request, pk):
    try:
        obj = UserScreen.objects.get(pk=pk)
    except UserScreen.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    serializer = UserScreenSerializer(obj, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Updated"})
    
    return Response(serializer.errors, status=400)


@api_view(['PATCH'])
def toggle_status(request, pk):
    obj = UserScreen.objects.get(pk=pk)
    obj.is_active = not obj.is_active
    obj.save()

    return Response({"status": obj.is_active})
@api_view(['GET'])
def main_screen_list(request):
    from .models import MainScreen
    data = list(MainScreen.objects.values('id', 'name'))
    return Response(data)


@api_view(['GET'])
def screen_section_list(request):
    main_id = request.GET.get('main_screen_id')

    queryset = ScreenSection.objects.all()

    if main_id:
        queryset = queryset.filter(main_screen_id=main_id)

    data = list(queryset.values('id', 'name'))
    return Response(data)


# user_types - This file defines the API views for managing user types in the admin module of the MASTERS app, including functions for listing user types with pagination and search functionality, creating new user types, updating existing user types, and toggling user type status. These views handle HTTP requests and return appropriate responses based on the operations performed on the UserType model.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from .models import UserType
from .serializers import UserTypeSerializer


@api_view(['GET'])
def user_type_list(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search = request.GET.get('search[value]', '')

    queryset = UserType.objects.all()

    total = queryset.count()

    if search:
        queryset = queryset.filter(name__icontains=search)

    filtered = queryset.count()

    queryset = queryset[start:start+length]

    serializer = UserTypeSerializer(queryset, many=True)

    data = []
    for i, item in enumerate(serializer.data, start=1):
        data.append({
            "sno": start + i,
            "user_type": item["name"],
            "status": "Active" if item["is_active"] else "Inactive",
            "id": item["id"]
        })

    return Response({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": filtered,
        "data": data
    })

@api_view(['POST'])
def create_user_type(request):
    serializer = UserTypeSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Created successfully"})
    
    return Response(serializer.errors, status=400)

@api_view(['PUT'])
def update_user_type(request, pk):
    try:
        obj = UserType.objects.get(pk=pk)
    except UserType.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    serializer = UserTypeSerializer(obj, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Updated successfully"})
    
    return Response(serializer.errors, status=400)

@api_view(['PATCH'])
def toggle_user_type(request, pk):
    try:
        obj = UserType.objects.get(pk=pk)
        obj.is_active = not obj.is_active
        obj.save()
        return Response({"status": obj.is_active})
    except UserType.DoesNotExist:
        return Response({"error": "Not found"}, status=404)
    

# user_type_permissions - This file defines the API views for managing user type permissions in the admin module of the MASTERS app, including functions for listing user type permissions with pagination and search functionality, creating new user type permissions, updating existing user type permissions, and toggling user type permission status. These views handle HTTP requests and return appropriate responses based on the operations performed on the UserTypePermission model and related entities.
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from .models import UserType, MainScreen, UserTypePermission
from .serializers import *


class UserTypeViewSet(viewsets.ModelViewSet):
    queryset = UserType.objects.all().order_by('id')
    serializer_class = UserTypeSerializer


class MainScreenViewSet(viewsets.ModelViewSet):
    queryset = MainScreen.objects.all().order_by('id')
    serializer_class = MainScreenSerializer


class UserTypePermissionViewSet(viewsets.ModelViewSet):
    queryset = UserTypePermission.objects.select_related('user_type', 'main_screen').all().order_by('id')
    serializer_class = UserTypePermissionSerializer

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.status = request.data.get('status', instance.status)
        instance.save()
        return Response({"message": "Status updated"})


# Path-based views for user_type_permissions
@api_view(['GET'])
def user_type_permission_list(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search = request.GET.get('search[value]', '')

    queryset = UserTypePermission.objects.select_related('user_type', 'main_screen')

    total = queryset.count()

    if search:
        queryset = queryset.filter(
            Q(user_type__name__icontains=search) |
            Q(main_screen__name__icontains=search)
        )

    filtered = queryset.count()
    queryset = queryset[start:start+length]

    serializer = UserTypePermissionSerializer(queryset, many=True)

    data = []
    for i, item in enumerate(serializer.data, start=1):
        data.append({
            "sno": start + i,
            "user_type": item["user_type_name"] if "user_type_name" in item else item["user_type"],
            "main_screen": item["main_screen_name"] if "main_screen_name" in item else item["main_screen"],
            "status": "Active" if item["status"] else "Inactive",
            "id": item["id"]
        })

    return Response({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": filtered,
        "data": data
    })


@api_view(['POST'])
def create_user_type_permission(request):
    serializer = UserTypePermissionSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def update_user_type_permission(request, pk):
    try:
        obj = UserTypePermission.objects.get(pk=pk)
    except UserTypePermission.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = UserTypePermissionSerializer(obj, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Updated successfully", "data": serializer.data})
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
def toggle_user_type_permission(request, pk):
    try:
        obj = UserTypePermission.objects.get(pk=pk)
    except UserTypePermission.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    
    obj.status = not obj.status
    obj.save()

    return Response({"message": "Status toggled", "status": obj.status})


user_list = extend_schema(
    parameters=DATATABLE_PARAMETERS,
    responses=OpenApiTypes.OBJECT,
)(user_list)
create_user = extend_schema(
    request=UserSerializer,
    responses=OpenApiTypes.OBJECT,
)(create_user)
update_user = extend_schema(
    request=UserSerializer,
    responses=OpenApiTypes.OBJECT,
)(update_user)
toggle_user_status = extend_schema(
    request=None,
    responses=OpenApiTypes.OBJECT,
)(toggle_user_status)

user_screen_list = extend_schema(
    parameters=DATATABLE_PARAMETERS,
    responses=OpenApiTypes.OBJECT,
)(user_screen_list)
create_user_screen = extend_schema(
    request=UserScreenSerializer,
    responses=OpenApiTypes.OBJECT,
)(create_user_screen)
update_user_screen = extend_schema(
    request=UserScreenSerializer,
    responses=OpenApiTypes.OBJECT,
)(update_user_screen)
toggle_status = extend_schema(
    request=None,
    responses=OpenApiTypes.OBJECT,
)(toggle_status)
main_screen_list = extend_schema(
    responses=OpenApiTypes.OBJECT,
)(main_screen_list)
screen_section_list = extend_schema(
    parameters=[
        query_int_parameter(
            "main_screen_id",
            "Optional main screen ID to filter screen sections.",
        )
    ],
    responses=OpenApiTypes.OBJECT,
)(screen_section_list)

user_type_list = extend_schema(
    parameters=DATATABLE_PARAMETERS,
    responses=OpenApiTypes.OBJECT,
)(user_type_list)
create_user_type = extend_schema(
    request=UserTypeSerializer,
    responses=OpenApiTypes.OBJECT,
)(create_user_type)
update_user_type = extend_schema(
    request=UserTypeSerializer,
    responses=OpenApiTypes.OBJECT,
)(update_user_type)
toggle_user_type = extend_schema(
    request=None,
    responses=OpenApiTypes.OBJECT,
)(toggle_user_type)

user_type_permission_list = extend_schema(
    parameters=DATATABLE_PARAMETERS,
    responses=OpenApiTypes.OBJECT,
)(user_type_permission_list)
create_user_type_permission = extend_schema(
    request=UserTypePermissionSerializer,
    responses=OpenApiTypes.OBJECT,
)(create_user_type_permission)
update_user_type_permission = extend_schema(
    request=UserTypePermissionSerializer,
    responses=OpenApiTypes.OBJECT,
)(update_user_type_permission)
toggle_user_type_permission = extend_schema(
    request=None,
    responses=OpenApiTypes.OBJECT,
)(toggle_user_type_permission)
