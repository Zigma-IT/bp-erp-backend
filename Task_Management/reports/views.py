from rest_framework.permissions import AllowAny
from rest_framework.generics import ListAPIView

from tasks.models import TaskCreation

from .serializers import TaskReportSerializer


class TaskReportListAPIView(ListAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    serializer_class = TaskReportSerializer

    def get_queryset(self):

        return TaskCreation.objects.filter(
            is_delete=False
        ).order_by('-created_date', '-id')
