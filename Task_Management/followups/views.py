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

from .models import TaskFollowups
from .serializers import TaskFollowupsSerializer


# CREATE
class TaskFollowupsCreateAPIView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):

        data = request.data.copy()

        data['unique_id'] = str(uuid.uuid4())[:12]

        serializer = TaskFollowupsSerializer(data=data)

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Task Followup Created Successfully",
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
class TaskFollowupsListAPIView(ListAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    serializer_class = TaskFollowupsSerializer

    def get_queryset(self):

        return TaskFollowups.objects.filter(
            is_delete=False
        ).order_by('-id')


# RETRIEVE
class TaskFollowupsRetrieveAPIView(RetrieveAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = TaskFollowups.objects.filter(
        is_delete=False
    )

    serializer_class = TaskFollowupsSerializer

    lookup_field = 'id'


# UPDATE
class TaskFollowupsUpdateAPIView(UpdateAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = TaskFollowups.objects.filter(
        is_delete=False
    )

    serializer_class = TaskFollowupsSerializer

    lookup_field = 'id'


# DELETE
class TaskFollowupsDeleteAPIView(DestroyAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = TaskFollowups.objects.all()

    serializer_class = TaskFollowupsSerializer

    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):

        instance = self.get_object()

        instance.is_delete = True
        instance.save()

        return Response(
            {
                "status": True,
                "message": "Task Followup Deleted Successfully"
            },
            status=status.HTTP_200_OK
        )