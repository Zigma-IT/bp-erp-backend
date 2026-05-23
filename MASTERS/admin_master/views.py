"""Admin master APIs for users, screens, user types, and permissions.

The file is grouped by frontend screen so a developer can jump directly to the
matching endpoints for user creation, user screen setup, user type setup, and
permission mapping.
"""

from collections import defaultdict

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from MASTERS.schema_utils import DATATABLE_PARAMETERS, query_int_parameter
from .models import MainScreen, ScreenSection, UserCreation, UserScreen, UserType, UserTypePermission
from .serializers import (
    MainScreenSerializer,
    UserScreenSerializer,
    UserSerializer,
    UserTypePermissionSerializer,
    UserTypeSerializer,
    ScreenSectionSerializer,

)


def _permission_group_payload(queryset):
    records = list(queryset.order_by("user_screen__screen_section__name", "user_screen__order_no", "id"))
    if not records:
        return None

    serializer = UserTypePermissionSerializer(records, many=True)
    first = records[0]
    permissions = []

    for item in serializer.data:
        permissions.append(
            {
                "id": item["id"],
                "user_screen": item.get("user_screen"),
                "screen_name": item.get("screen_name") or "",
                "screen_section": item.get("screen_section"),
                "screen_section_name": item.get("screen_section_name") or "",
                "can_view": item.get("can_view", False),
                "can_add": item.get("can_add", False),
                "can_update": item.get("can_update", False),
                "can_list": item.get("can_list", False),
                "can_delete": item.get("can_delete", False),
                "can_print": item.get("can_print", False),
                "status": item.get("status", True),
            }
        )

    return {
        "id": first.id,
        "user_type": first.user_type_id,
        "user_type_name": first.user_type.name,
        "main_screen": first.main_screen_id,
        "main_screen_name": first.main_screen.name,
        "status": all(record.status for record in records),
        "permissions": permissions,
    }


def _main_screen_lookup_payload(main_screen_id=None):
    main_screens = MainScreen.objects.all().order_by("order_no", "name")
    main_screen_serializer = MainScreenSerializer(main_screens, many=True)

    payload = {
        "success": True,
        "data": [
            {
                "id": item["id"],
                "name": item["name"],
                "screen_type": item.get("screen_type", ""),
                "order_no": item.get("order_no", 0),
                "status": item.get("active_status", "Active"),
                "folder_key": item.get("folder_key", ""),
                "icon": item.get("icon", ""),
                "description": item.get("description", ""),
            }
            for item in main_screen_serializer.data
        ],
    }

    if main_screen_id is None:
        return payload

    screen_sections = ScreenSection.objects.select_related("main_screen").filter(
        main_screen_id=main_screen_id
    ).order_by("order_no", "id")
    user_screens = UserScreen.objects.select_related("main_screen", "screen_section").filter(
        main_screen_id=main_screen_id
    ).order_by("screen_section__order_no", "screen_section__name", "order_no", "id")

    section_serializer = ScreenSectionSerializer(screen_sections, many=True)
    screen_serializer = UserScreenSerializer(user_screens, many=True)

    payload["screen_sections"] = section_serializer.data
    payload["screens"] = screen_serializer.data
    return payload


def _user_detail_payload(user):
    """
    Return a detail payload that matches the frontend edit form expectations.

    The list endpoint already returns a transformed shape, but the edit form
    also loads a user directly by id. Keeping this payload compatible avoids
    having the frontend guess at serializer field names.
    """
    serialized = UserSerializer(user).data
    return {
        "id": user.id,
        "name": user.staff.name if user.staff_id else "",
        "staff": user.staff_id,
        "phone": user.mobile or (user.staff.mobile if user.staff_id else ""),
        "work_location": user.project or "",
        "username": user.username,
        "is_active": user.is_active,
        "is_team_head": user.is_team_head,
        "role": user.role_id,
        "role_name": user.role.name if user.role_id else "",
        "user_type_name": user.user_type.name if user.user_type_id else "",
        "user_type": user.user_type_id,
        "raw": serialized,
    }


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

@api_view(['GET', 'PUT'])
def update_user(request, pk):
    try:
        user = UserCreation.objects.get(pk=pk)
    except UserCreation.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    if request.method == "GET":
        return Response(_user_detail_payload(user))

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
    

@api_view(['GET'])
def user_screen_list(request):
    raw = str(request.GET.get("raw", "")).lower() in {"1", "true", "yes"}
    main_screen_id = request.GET.get("main_screen_id")
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search = request.GET.get('search[value]', '')

    queryset = UserScreen.objects.select_related('main_screen', 'screen_section')

    if main_screen_id:
        try:
            queryset = queryset.filter(main_screen_id=int(main_screen_id))
        except (TypeError, ValueError):
            return Response({"error": "main_screen_id must be a valid integer."}, status=400)
    if raw:
        serializer = UserScreenSerializer(
            queryset.order_by('screen_section__order_no', 'screen_section__name', 'order_no'),
            many=True
        )
        return Response(serializer.data)

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


@api_view(['GET', 'PUT'])
def update_user_screen(request, pk):
    try:
        obj = UserScreen.objects.get(pk=pk)
    except UserScreen.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    if request.method == "GET":
        return Response(UserScreenSerializer(obj).data)

    serializer = UserScreenSerializer(obj, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Updated"})
    
    return Response(serializer.errors, status=400)


@api_view(['PATCH'])
def toggle_status(request, pk):
    try:
        obj = UserScreen.objects.get(pk=pk)
    except UserScreen.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    obj.is_active = not obj.is_active
    obj.save()

    return Response({"status": obj.is_active})


@api_view(['GET'])
def main_screen_list(request):
    lookup = str(request.GET.get("lookup", "")).lower() in {"1", "true", "yes"}
    main_screen_id = request.GET.get("main_screen_id")

    if lookup:
        parsed_main_screen_id = None
        if main_screen_id not in (None, ""):
            try:
                parsed_main_screen_id = int(main_screen_id)
            except (TypeError, ValueError):
                return Response(
                    {"success": False, "data": [], "error": "main_screen_id must be a valid integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(_main_screen_lookup_payload(parsed_main_screen_id))

    queryset = MainScreen.objects.all().order_by("order_no", "name")
    serializer = MainScreenSerializer(queryset, many=True)

    data = []
    for index, item in enumerate(serializer.data, start=1):
        data.append({
            "sno": index,
            "id": item["id"],
            "name": item["name"],
            "screen_type": item.get("screen_type", ""),
            "order_no": item.get("order_no", 0),
            "status": item.get("active_status", "Active"),
            "folder_key": item.get("folder_key", ""),
            "icon": item.get("icon", ""),
            "description": item.get("description", ""),
        })

    return Response({
        "draw": int(request.GET.get("draw", 1)),
        "recordsTotal": len(data),
        "recordsFiltered": len(data),
        "data": data,
    })





def screen_section_list(request):
    main_id = request.GET.get('main_screen_id')

    queryset = ScreenSection.objects.all()

    if main_id:
        queryset = queryset.filter(main_screen_id=main_id)

    data = list(queryset.values('id', 'name'))
    return Response(data)


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

@api_view(['GET', 'PUT'])
def update_user_type(request, pk):
    try:
        obj = UserType.objects.get(pk=pk)
    except UserType.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    if request.method == "GET":
        return Response(UserTypeSerializer(obj).data)

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
    

class UserTypeViewSet(viewsets.ModelViewSet):
    queryset = UserType.objects.all().order_by('id')
    serializer_class = UserTypeSerializer


class MainScreenViewSet(viewsets.ModelViewSet):
    queryset = MainScreen.objects.all().order_by('id')
    serializer_class = MainScreenSerializer

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.status = request.data.get("status", instance.status)
        instance.save(update_fields=["status", "updated_at"])
        return Response(MainScreenSerializer(instance).data)


class UserTypePermissionViewSet(viewsets.ModelViewSet):
    queryset = UserTypePermission.objects.select_related('user_type', 'main_screen', 'user_screen', 'user_screen__screen_section').all().order_by('id')
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

    queryset = UserTypePermission.objects.select_related('user_type', 'main_screen', 'user_screen', 'user_screen__screen_section')

    if search:
        queryset = queryset.filter(
            Q(user_type__name__icontains=search) |
            Q(main_screen__name__icontains=search)
        )

    groups = defaultdict(list)
    for permission in queryset.order_by("user_type__name", "main_screen__name", "user_screen__order_no", "id"):
        groups[(permission.user_type_id, permission.main_screen_id)].append(permission)

    grouped_records = list(groups.values())
    total_groups = len(
        {
            (permission.user_type_id, permission.main_screen_id)
            for permission in UserTypePermission.objects.all().only("user_type_id", "main_screen_id")
        }
    )
    filtered = len(grouped_records)
    paginated_groups = grouped_records[start:start+length]

    data = []
    for i, records in enumerate(paginated_groups, start=1):
        first = records[0]
        data.append({
            "sno": start + i,
            "user_type": first.user_type.name,
            "main_screen": first.main_screen.name,
            "status": "Active" if all(item.status for item in records) else "Inactive",
            "id": first.id,
            "screen_count": sum(1 for item in records if item.user_screen_id),
            "can_view": any(item.can_view for item in records),
            "can_add": any(item.can_add for item in records),
            "can_update": any(item.can_update for item in records),
            "can_list": any(item.can_list for item in records),
            "can_delete": any(item.can_delete for item in records),
            "can_print": any(item.can_print for item in records),
        })

    return Response({
        "draw": draw,
        "recordsTotal": total_groups,
        "recordsFiltered": filtered,
        "data": data
    })


@api_view(['POST'])
def create_user_type_permission(request):
    user_type = request.data.get("user_type")
    main_screen = request.data.get("main_screen")
    permissions = request.data.get("permissions")
    group_status = request.data.get("status", True)

    if not isinstance(permissions, list) or len(permissions) == 0:
        return Response({"permissions": ["At least one screen permission is required."]}, status=status.HTTP_400_BAD_REQUEST)

    existing_records = {
        record.user_screen_id: record
        for record in UserTypePermission.objects.filter(user_type_id=user_type, main_screen_id=main_screen)
    }
    created_records = []
    kept_ids = []

    for permission in permissions:
        user_screen_id = permission.get("user_screen")
        payload = {
            "user_type": user_type,
            "main_screen": main_screen,
            "user_screen": user_screen_id,
            "can_view": permission.get("can_view", False),
            "can_add": permission.get("can_add", False),
            "can_update": permission.get("can_update", False),
            "can_list": permission.get("can_list", False),
            "can_delete": permission.get("can_delete", False),
            "can_print": permission.get("can_print", False),
            "status": permission.get("status", group_status),
        }
        serializer = UserTypePermissionSerializer(existing_records.get(user_screen_id), data=payload, partial=bool(existing_records.get(user_screen_id)))
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        saved = serializer.save()
        created_records.append(saved)
        kept_ids.append(saved.id)

    UserTypePermission.objects.filter(user_type_id=user_type, main_screen_id=main_screen).exclude(id__in=kept_ids).delete()

    grouped_payload = _permission_group_payload(
        UserTypePermission.objects.select_related("user_type", "main_screen", "user_screen", "user_screen__screen_section").filter(
            user_type_id=created_records[0].user_type_id,
            main_screen_id=created_records[0].main_screen_id,
        )
    )
    return Response({"message": "Created successfully", "data": grouped_payload}, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT'])
def update_user_type_permission(request, pk):
    try:
        obj = UserTypePermission.objects.select_related("user_type", "main_screen").get(pk=pk)
    except UserTypePermission.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        grouped_queryset = UserTypePermission.objects.select_related(
            "user_type", "main_screen", "user_screen", "user_screen__screen_section"
        ).filter(user_type=obj.user_type, main_screen=obj.main_screen)
        payload = _permission_group_payload(grouped_queryset)
        if payload is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(payload)

    user_type = request.data.get("user_type", obj.user_type_id)
    main_screen = request.data.get("main_screen", obj.main_screen_id)
    permissions = request.data.get("permissions")
    group_status = request.data.get("status", True)

    if not isinstance(permissions, list) or len(permissions) == 0:
        return Response({"permissions": ["At least one screen permission is required."]}, status=status.HTTP_400_BAD_REQUEST)

    existing_records = {
        record.user_screen_id: record
        for record in UserTypePermission.objects.filter(user_type=obj.user_type, main_screen=obj.main_screen)
    }
    kept_ids = []

    for permission in permissions:
        user_screen_id = permission.get("user_screen")
        instance = existing_records.get(user_screen_id)
        payload = {
            "user_type": user_type,
            "main_screen": main_screen,
            "user_screen": user_screen_id,
            "can_view": permission.get("can_view", False),
            "can_add": permission.get("can_add", False),
            "can_update": permission.get("can_update", False),
            "can_list": permission.get("can_list", False),
            "can_delete": permission.get("can_delete", False),
            "can_print": permission.get("can_print", False),
            "status": permission.get("status", group_status),
        }
        serializer = UserTypePermissionSerializer(instance, data=payload, partial=bool(instance))
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        saved = serializer.save()
        kept_ids.append(saved.id)

    UserTypePermission.objects.filter(user_type=obj.user_type, main_screen=obj.main_screen).exclude(id__in=kept_ids).delete()

    grouped_payload = _permission_group_payload(
        UserTypePermission.objects.select_related("user_type", "main_screen", "user_screen", "user_screen__screen_section").filter(
            user_type_id=user_type,
            main_screen_id=main_screen,
        )
    )
    return Response({"message": "Updated successfully", "data": grouped_payload})


@api_view(['PATCH'])
def toggle_user_type_permission(request, pk):
    try:
        obj = UserTypePermission.objects.select_related("user_type", "main_screen").get(pk=pk)
    except UserTypePermission.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    queryset = UserTypePermission.objects.filter(user_type=obj.user_type, main_screen=obj.main_screen)
    next_status = not all(item.status for item in queryset)
    queryset.update(status=next_status)

    return Response({"message": "Status toggled", "status": next_status})


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
    parameters=DATATABLE_PARAMETERS + [
        query_int_parameter(
            "main_screen_id",
            "Optional main screen ID to filter user screens.",
        ),
        OpenApiParameter(
            name="raw",
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Return raw serializer data for mapping screens to sections.",
        ),
    ],
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
    parameters=[
        OpenApiParameter(
            name="lookup",
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Return lookup data with a consistent success/data envelope.",
        ),
        query_int_parameter(
            "main_screen_id",
            "Optional main screen ID to include matching screen sections and user screens.",
        ),
    ],
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
@api_view(['GET'])
def screen_section_list(request):
    lookup = str(request.GET.get("lookup", "")).lower() in {"1", "true", "yes"}
    main_id = request.GET.get('main_screen_id')

    queryset = ScreenSection.objects.select_related('main_screen').all().order_by('order_no', 'id')

    if main_id:
        queryset = queryset.filter(main_screen_id=main_id)

    if lookup:
        serializer = ScreenSectionSerializer(queryset, many=True)
        return Response(serializer.data)

    serializer = ScreenSectionSerializer(
        queryset,
        many=True
    )

    return Response({
        "status": True,
        "count": queryset.count(),
        "data": serializer.data
    })


@api_view(['POST', 'GET'])
def create_screen_section(request):

    # GET METHOD
    if request.method == 'GET':
        return Response({
            "message": "Send POST request",
            "required_fields": {
                "name": "string",
                "main_screen": "main_screen_id"
            }
        })

    # POST METHOD
    serializer = ScreenSectionSerializer(
        data=request.data
    )

    if serializer.is_valid():
        serializer.save()

        return Response({
            "status": True,
            "message": "Screen Section Created Successfully",
            "data": serializer.data
        })

    return Response({
        "status": False,
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
def update_screen_section(request, pk):

    try:
        obj = ScreenSection.objects.get(pk=pk)

    except ScreenSection.DoesNotExist:
        return Response({
            "status": False,
            "message": "Screen Section Not Found"
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            "status": True,
            "data": ScreenSectionSerializer(obj).data
        })

    serializer = ScreenSectionSerializer(
        obj,
        data=request.data
    )

    if serializer.is_valid():
        serializer.save()

        return Response({
            "status": True,
            "message": "Updated Successfully",
            "data": serializer.data
        })

    return Response({
        "status": False,
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
def toggle_screen_section(request, pk):

    try:
        obj = ScreenSection.objects.get(pk=pk)

    except ScreenSection.DoesNotExist:
        return Response({
            "status": False,
            "message": "Screen Section Not Found"
        }, status=status.HTTP_404_NOT_FOUND)

    obj.is_active = not obj.is_active
    obj.save()

    return Response({
        "status": True,
        "message": "Status Updated",
        "is_active": obj.is_active
    })
