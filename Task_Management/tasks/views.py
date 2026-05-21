import uuid

from rest_framework import status

from rest_framework.response import Response

from rest_framework.views import APIView

from rest_framework.permissions import AllowAny

from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
    DestroyAPIView,

)

from .models import TaskCreation , SelfTask

from .serializers import TaskCreationSerializer, SelfTaskSerializer


def _resolve_task_assignee(request, data):

    current_assignee = str(data.get('assigned_to') or '').strip()
    if current_assignee:
        return current_assignee

    request_user = getattr(request, 'user', None)
    if request_user is not None and getattr(request_user, 'is_authenticated', False):
        for attr in ('employee_id', 'staff_code', 'unique_id', 'id'):
            value = getattr(request_user, attr, None)
            if value not in (None, ''):
                return str(value).strip()

    for key in ('sess_user_id', 'created_user_id', 'updated_user_id'):
        value = str(data.get(key) or '').strip()
        if value:
            return value

    return ''


# CREATE
class TaskCreationCreateAPIView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):

        data = request.data.copy()

        data['unique_id'] = str(uuid.uuid4())[:12]
        data['assigned_to'] = _resolve_task_assignee(request, data)

        serializer = TaskCreationSerializer(
            data=data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Task Created Successfully",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            {
                "status": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


# LIST
class TaskCreationListAPIView(ListAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    serializer_class = TaskCreationSerializer

    def get_queryset(self):

        return TaskCreation.objects.filter(
            is_delete=False
        ).order_by('-id')


# RETRIEVE
class TaskCreationRetrieveAPIView(RetrieveAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = TaskCreation.objects.filter(
        is_delete=False
    )

    serializer_class = TaskCreationSerializer

    lookup_field = 'id'


# UPDATE
class TaskCreationUpdateAPIView(UpdateAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = TaskCreation.objects.filter(
        is_delete=False
    )

    serializer_class = TaskCreationSerializer

    lookup_field = 'id'

    def update(self, request, *args, **kwargs):

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()

        data['unique_id'] = data.get('unique_id') or instance.unique_id
        data['assigned_to'] = _resolve_task_assignee(request, data) or instance.assigned_to

        serializer = self.get_serializer(
            instance,
            data=data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)


# DELETE
class TaskCreationDeleteAPIView(DestroyAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = TaskCreation.objects.all()

    serializer_class = TaskCreationSerializer

    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):

        instance = self.get_object()

        instance.is_delete = True

        instance.save()

        return Response(
            {
                "status": True,
                "message": "Task Deleted Successfully"
            },
            status=status.HTTP_200_OK
        )

# CREATE
class SelfTaskCreateAPIView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):

        data = request.data.copy()

        data['unique_id'] = str(uuid.uuid4())[:12]

        serializer = SelfTaskSerializer(data=data)

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Self Task Created Successfully",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            {
                "status": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


# LIST
class SelfTaskListAPIView(ListAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    serializer_class = SelfTaskSerializer

    def get_queryset(self):

        return SelfTask.objects.filter(
            is_delete=False
        ).order_by('-id')


# RETRIEVE
class SelfTaskRetrieveAPIView(RetrieveAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = SelfTask.objects.filter(
        is_delete=False
    )

    serializer_class = SelfTaskSerializer

    lookup_field = 'id'


# UPDATE
class SelfTaskUpdateAPIView(UpdateAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = SelfTask.objects.filter(
        is_delete=False
    )

    serializer_class = SelfTaskSerializer

    lookup_field = 'id'


# DELETE
class SelfTaskDeleteAPIView(DestroyAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = SelfTask.objects.all()

    serializer_class = SelfTaskSerializer

    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):

        instance = self.get_object()

        instance.is_delete = True
        instance.save()

        return Response(
            {
                "status": True,
                "message": "Self Task Deleted Successfully"
            },
            status=status.HTTP_200_OK
        )
