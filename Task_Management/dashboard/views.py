from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common_master.models import Company, Project
from followups.models import TaskFollowups
from login_home.models import Department
from tasks.models import TaskCreation


def _normalize_status(value):
    normalized = str(value or "").strip().lower()
    if normalized == "completed":
        return "completed"
    if normalized in {"in_progress", "in progress", "progressing"}:
        return "progressing"
    return "pending"


def _base_queryset():
    return TaskCreation.objects.filter(is_delete=False, is_active=True)


def _with_age(tasks):
    today = timezone.now().date()
    for task in tasks:
        created_at = getattr(task, "created_date", None)
        created_date = created_at.date() if created_at else today
        age_days = max((today - created_date).days, 0)
        yield task, age_days


def _build_lookup(model, label_attr):
    lookup = {}
    for obj in model.objects.all():
        label = str(getattr(obj, label_attr, "") or "").strip()
        if not label:
            continue
        lookup[str(getattr(obj, "id", ""))] = label
        unique_id = getattr(obj, "unique_id", None)
        if unique_id not in (None, ""):
            lookup[str(unique_id)] = label
    return lookup


def _display_value(raw_value, lookup):
    key = str(raw_value or "").strip()
    if not key:
        return "-"
    return lookup.get(key, key)


def _serialize_task(task, lookups):
    return {
        "id": task.id,
        "task_code": task.task_code or task.unique_id,
        "company": _display_value(task.company_id, lookups["company"]),
        "project": _display_value(task.project_id, lookups["project"]),
        "department": _display_value(task.department_id, lookups["department"]),
        "category": _display_value(task.task_category_id, lookups["category"]),
        "sub_category": _display_value(task.task_sub_category_id, lookups["sub_category"]),
        "assigned_to": (task.assigned_to or "").strip() or "-",
        "priority": (task.priority or "Normal").strip() or "Normal",
        "status": task.status or "Pending",
        "created_date": task.created_date,
    }


class DashboardKPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        tasks = list(_base_queryset())
        today = timezone.now().date()

        new_count = 0
        opening = 0
        pending = 0
        progressing = 0
        completed = 0

        for task in tasks:
            status_key = _normalize_status(task.status)
            created_date = task.created_date.date() if task.created_date else today

            if created_date == today:
                new_count += 1

            if status_key == "completed":
                completed += 1
            elif status_key == "progressing":
                progressing += 1
                if created_date < today:
                    opening += 1
            else:
                pending += 1
                if created_date < today:
                    opening += 1

        return Response(
            {
                "opening": opening,
                "new_count": new_count,
                "pending": pending,
                "progressing": progressing,
                "completed": completed,
            }
        )


class AgeAnalysisView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        counts = {
            "d1": 0,
            "d5": 0,
            "d10": 0,
            "d15": 0,
            "d30": 0,
            "d30plus": 0,
        }

        for _, age_days in _with_age(_base_queryset()):
            if age_days <= 1:
                counts["d1"] += 1
            if age_days <= 5:
                counts["d5"] += 1
            if age_days <= 10:
                counts["d10"] += 1
            if age_days <= 15:
                counts["d15"] += 1
            if age_days <= 30:
                counts["d30"] += 1
            if age_days > 30:
                counts["d30plus"] += 1

        return Response(counts)


class _GroupedBreakdownView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    field_name = ""
    response_label = ""
    label_model = None
    label_attr = ""

    def get(self, request):
        label_lookup = _build_lookup(self.label_model, self.label_attr) if self.label_model else {}
        grouped = (
            _base_queryset()
            .values(self.field_name)
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        data = []
        for item in grouped:
            raw_value = item.get(self.field_name)
            data.append(
                {
                    self.response_label: _display_value(raw_value, label_lookup),
                    "total": item["total"],
                }
            )
        return Response(data)


class DepartmentWiseView(_GroupedBreakdownView):
    field_name = "department_id"
    response_label = "department_display"
    label_model = Department
    label_attr = "name"


class CompanyWiseView(_GroupedBreakdownView):
    field_name = "company_id"
    response_label = "company_display"
    label_model = Company
    label_attr = "name"


class ProjectWiseView(_GroupedBreakdownView):
    field_name = "project_id"
    response_label = "project_display"
    label_model = Project
    label_attr = "name"


class RemarkAnalysisView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        data = (
            TaskFollowups.objects.filter(is_delete=False, is_active=True)
            .values("remarks_type")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        return Response(
            [
                {
                    "remarks_type__remark_type": item["remarks_type"] or "No Remark",
                    "total": item["total"],
                }
                for item in data
            ]
        )


class MonthlyAnalyticsView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        today = timezone.now().date().replace(day=1)
        month_starts = []
        current = today
        for _ in range(5, -1, -1):
            month_starts.append(current)
            previous_month_last_day = current - timedelta(days=1)
            current = previous_month_last_day.replace(day=1)
        month_starts.reverse()

        tasks = list(
            _base_queryset()
            .annotate(task_month=TruncMonth("created_date"))
            .values("task_month")
            .annotate(
                new_count=Count("id"),
                completed_count=Count("id", filter=Q(status__iexact="Completed")),
            )
            .order_by("task_month")
        )

        task_map = {}
        for item in tasks:
            month = item["task_month"]
            if month is None:
                continue
            task_map[month.date().replace(day=1)] = item

        response = []
        for month_start in sorted(month_starts):
            item = task_map.get(month_start, {})
            response.append(
                {
                    "task_date": month_start.isoformat(),
                    "new_count": item.get("new_count", 0),
                    "completed_count": item.get("completed_count", 0),
                }
            )

        return Response(response)


class TaskListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        lookups = {
            "company": _build_lookup(Company, "name"),
            "project": _build_lookup(Project, "name"),
            "department": _build_lookup(Department, "name"),
            "category": {},
            "sub_category": {},
        }

        tasks = _base_queryset().order_by("-created_date")
        return Response([_serialize_task(task, lookups) for task in tasks])
