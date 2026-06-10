from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ShiftCreation , ShiftRoster , WeekoffCreation , HolidayCreation , LeaveEntry
from .serializers import ShiftCreationSerializer , ShiftRosterSerializer , WeekoffCreationSerializer , HolidayCreationSerializer , LeaveEntrySerializer


def _clean_string(value):
    if value is None:
        return ""
    return str(value).strip()


def _read_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ["1", "true", "yes", "active"]
    return False


def _get_created_shift(shift_unique_id, shift_name):
    shift_unique_id = _clean_string(shift_unique_id)
    shift_name = _clean_string(shift_name)

    if not shift_unique_id and not shift_name:
        return None

    queryset = ShiftCreation.objects.filter(is_delete=False, is_active=True)

    if shift_unique_id:
        shift = queryset.filter(unique_id=shift_unique_id).first()
        if shift:
            return shift

    if shift_name:
        return queryset.filter(shift_name__iexact=shift_name).first()

    return None


def _month_filters(month_value):
    if not month_value:
        return {}

    parts = str(month_value).split("-")
    if len(parts) < 2:
        return {}

    try:
        year = int(parts[0])
        month = int(parts[1])
    except ValueError:
        return {}

    if month < 1 or month > 12:
        return {}

    next_year = year + 1 if month == 12 else year
    next_month = 1 if month == 12 else month + 1

    return {
        "shift_date__gte": f"{year:04d}-{month:02d}-01",
        "shift_date__lt": f"{next_year:04d}-{next_month:02d}-01",
    }


class ShiftCreationCreateAPIView(APIView):

    def post(self, request):

        serializer = ShiftCreationSerializer(
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class ShiftCreationListAPIView(APIView):

    def get(self, request):

        queryset = ShiftCreation.objects.filter(
            is_delete=False
        ).order_by('-id')

        serializer = ShiftCreationSerializer(
            queryset,
            many=True
        )

        return Response(serializer.data)


class ShiftCreationRetrieveAPIView(APIView):

    def get(self, request, pk):

        obj = ShiftCreation.objects.get(pk=pk)

        serializer = ShiftCreationSerializer(obj)

        return Response(serializer.data)


class ShiftCreationUpdateAPIView(APIView):

    def put(self, request, pk):

        obj = ShiftCreation.objects.get(pk=pk)

        serializer = ShiftCreationSerializer(
            obj,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data)

        return Response(serializer.errors)


class ShiftCreationDeleteAPIView(APIView):

    def delete(self, request, pk):

        obj = ShiftCreation.objects.get(pk=pk)

        obj.is_delete = True
        obj.save()

        return Response(
            {"message": "Deleted Successfully"}
        )


class ShiftRosterListCreateAPIView(
    generics.ListCreateAPIView
):
    queryset = ShiftRoster.objects.filter(
        is_delete=False
    )
    serializer_class = ShiftRosterSerializer

    def get_queryset(self):
        params = self.request.query_params
        queryset = ShiftRoster.objects.filter(is_delete=False)

        main_unique_id = params.get("main_unique_id") or params.get("mainUniqueId")
        employee_id = params.get("employee_id") or params.get("employeeId")
        project_id = params.get("project_id") or params.get("projectId")
        project_name = params.get("project_name") or params.get("projectName")
        month_value = params.get("month") or params.get("month_value") or params.get("monthValue")

        if main_unique_id:
            queryset = queryset.filter(main_unique_id=main_unique_id)

        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        project_filter = Q()
        if project_id:
            project_filter |= Q(project_id=project_id) | Q(project_id__isnull=True, employee_id=project_id)
        if project_name:
            project_filter |= Q(project_name=project_name) | Q(employee_id=project_name)
        if project_filter:
            queryset = queryset.filter(project_filter)

        month_filter = _month_filters(month_value)
        if month_filter:
            queryset = queryset.filter(**month_filter)

        return queryset.order_by("shift_date", "employee_id", "id")


class ShiftRosterBulkUpsertAPIView(APIView):

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        assignments = data.get("assignments")

        if not isinstance(assignments, list):
            return Response(
                {"assignments": ["Expected a list of roster assignments."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        main_unique_id = _clean_string(
            data.get("main_unique_id") or data.get("mainUniqueId")
        ) or f"SHIFT-ROSTER-{int(timezone.now().timestamp() * 1000)}"
        project_id = _clean_string(data.get("project_id") or data.get("projectId"))
        project_name = _clean_string(data.get("project_name") or data.get("projectName"))

        saved_rows = []

        for assignment in assignments:
            if not isinstance(assignment, dict):
                continue

            roster_id = assignment.get("id")
            employee_id = _clean_string(
                assignment.get("employee_id") or assignment.get("employeeId")
            )
            shift_date = _clean_string(
                assignment.get("shift_date") or assignment.get("shiftDate")
            )

            if not employee_id or not shift_date:
                continue

            selected_shift = _get_created_shift(
                assignment.get("shift_unique_id") or assignment.get("shiftUniqueId"),
                assignment.get("shift_name") or assignment.get("shiftName"),
            )

            row_project_id = _clean_string(
                assignment.get("project_id") or assignment.get("projectId")
            ) or project_id
            row_project_name = _clean_string(
                assignment.get("project_name") or assignment.get("projectName")
            ) or project_name

            defaults = {
                "main_unique_id": main_unique_id,
                "project_id": row_project_id or None,
                "project_name": row_project_name or None,
                "employee_id": employee_id,
                "shift_date": shift_date,
                "shift_unique_id": selected_shift.unique_id if selected_shift else None,
                "shift_name": selected_shift.shift_name if selected_shift else None,
                "is_weekoff": _read_bool(
                    assignment.get("is_weekoff", assignment.get("isWeekoff"))
                ),
                "is_holiday": _read_bool(
                    assignment.get("is_holiday", assignment.get("isHoliday"))
                ),
                "is_delete": False,
            }

            roster = None
            if roster_id:
                roster = ShiftRoster.objects.filter(pk=roster_id).first()

            if roster:
                for field_name, value in defaults.items():
                    setattr(roster, field_name, value)
                roster.save()
            else:
                lookup = {
                    "employee_id": employee_id,
                    "shift_date": shift_date,
                }

                if row_project_id:
                    lookup["project_id"] = row_project_id
                elif row_project_name:
                    lookup["project_name"] = row_project_name
                else:
                    lookup["main_unique_id"] = main_unique_id

                roster, _created = ShiftRoster.objects.update_or_create(
                    defaults=defaults,
                    **lookup
                )

            saved_rows.append(roster)

        serializer = ShiftRosterSerializer(saved_rows, many=True)
        return Response(
            {
                "status": True,
                "main_unique_id": main_unique_id,
                "data": serializer.data,
            }
        )

    def put(self, request):
        return self.post(request)


class ShiftRosterRetrieveAPIView(
    generics.RetrieveAPIView
):
    queryset = ShiftRoster.objects.all()
    serializer_class = ShiftRosterSerializer


class ShiftRosterUpdateAPIView(
    generics.UpdateAPIView
):
    queryset = ShiftRoster.objects.all()
    serializer_class = ShiftRosterSerializer


class ShiftRosterDeleteAPIView(
    generics.DestroyAPIView
):
    queryset = ShiftRoster.objects.all()
    serializer_class = ShiftRosterSerializer

    def perform_destroy(self, instance):
        instance.is_delete = True
        instance.save()


class WeekoffCreationListCreateAPIView(
    generics.ListCreateAPIView
):
    queryset = WeekoffCreation.objects.filter(
        is_delete=False
    )
    serializer_class = WeekoffCreationSerializer


class WeekoffCreationRetrieveAPIView(
    generics.RetrieveAPIView
):
    queryset = WeekoffCreation.objects.filter(
        is_delete=False
    )
    serializer_class = WeekoffCreationSerializer


class WeekoffCreationUpdateAPIView(
    generics.UpdateAPIView
):
    queryset = WeekoffCreation.objects.filter(
        is_delete=False
    )
    serializer_class = WeekoffCreationSerializer


class WeekoffCreationDeleteAPIView(
    generics.DestroyAPIView
):
    queryset = WeekoffCreation.objects.filter(
        is_delete=False
    )
    serializer_class = WeekoffCreationSerializer

    def perform_destroy(self, instance):
        instance.is_delete = True
        instance.save()


class HolidayCreationListCreateAPIView(
    generics.ListCreateAPIView
):
    queryset = HolidayCreation.objects.filter(
        is_delete=False
    )
    serializer_class = HolidayCreationSerializer


class HolidayCreationRetrieveAPIView(
    generics.RetrieveAPIView
):
    queryset = HolidayCreation.objects.filter(
        is_delete=False
    )
    serializer_class = HolidayCreationSerializer


class HolidayCreationUpdateAPIView(
    generics.UpdateAPIView
):
    queryset = HolidayCreation.objects.filter(
        is_delete=False
    )
    serializer_class = HolidayCreationSerializer


class HolidayCreationDeleteAPIView(
    generics.DestroyAPIView
):
    queryset = HolidayCreation.objects.filter(
        is_delete=False
    )
    serializer_class = HolidayCreationSerializer

    def perform_destroy(self, instance):
        instance.is_delete = True
        instance.save()

class LeaveEntryListCreateAPIView(
    generics.ListCreateAPIView
):
    queryset = LeaveEntry.objects.filter(
        is_delete=False
    )
    serializer_class = LeaveEntrySerializer


class LeaveEntryRetrieveAPIView(
    generics.RetrieveAPIView
):
    queryset = LeaveEntry.objects.filter(
        is_delete=False
    )
    serializer_class = LeaveEntrySerializer


class LeaveEntryUpdateAPIView(
    generics.UpdateAPIView
):
    queryset = LeaveEntry.objects.filter(
        is_delete=False
    )
    serializer_class = LeaveEntrySerializer


class LeaveEntryDeleteAPIView(
    generics.DestroyAPIView
):
    queryset = LeaveEntry.objects.filter(
        is_delete=False
    )
    serializer_class = LeaveEntrySerializer

    def perform_destroy(self, instance):
        instance.is_delete = True
        instance.save()