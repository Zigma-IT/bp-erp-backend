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

from .models import TaskCategory , TaskSubCategory , PriorityCreation , ProblemType , RemarkCreation
from .serializers import TaskCategorySerializer , TaskSubCategorySerializer , PriorityCreationSerializer , ProblemTypeSerializer , RemarkCreationSerializer


# CREATE
class TaskCategoryCreateAPIView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):

        serializer = TaskCategorySerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Task Category Created Successfully",
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
class TaskCategoryListAPIView(ListAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    serializer_class = TaskCategorySerializer

    def get_queryset(self):

        return TaskCategory.objects.filter(
            is_delete=False
        ).order_by('-id')


# RETRIEVE
class TaskCategoryRetrieveAPIView(RetrieveAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = TaskCategory.objects.filter(
        is_delete=False
    )

    serializer_class = TaskCategorySerializer

    lookup_field = 'id'


# UPDATE
class TaskCategoryUpdateAPIView(UpdateAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = TaskCategory.objects.filter(
        is_delete=False
    )

    serializer_class = TaskCategorySerializer

    lookup_field = 'id'


# DELETE
class TaskCategoryDeleteAPIView(DestroyAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = TaskCategory.objects.all()

    serializer_class = TaskCategorySerializer

    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):

        instance = self.get_object()

        instance.is_delete = True
        instance.save()

        return Response(
            {
                "status": True,
                "message": "Task Category Deleted Successfully"
            },
            status=status.HTTP_200_OK
        )


class TaskCategoryToggleAPIView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def patch(self, request, id):

        try:
            instance = TaskCategory.objects.get(
                id=id,
                is_delete=False
            )
        except TaskCategory.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "Task Category not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        is_active = request.data.get("is_active")

        if is_active is None:
            return Response(
                {
                    "status": False,
                    "message": "is_active is required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if isinstance(is_active, str):
            normalized = is_active.strip().lower()
            if normalized in ["true", "1", "active", "yes"]:
                is_active = True
            elif normalized in ["false", "0", "inactive", "no"]:
                is_active = False

        instance.is_active = bool(is_active)
        instance.save(update_fields=["is_active", "updated"])

        return Response(
            {
                "status": True,
                "message": "Task Category status updated successfully",
                "data": TaskCategorySerializer(instance).data
            },
            status=status.HTTP_200_OK
        )



# CREATE
class TaskSubCategoryCreateAPIView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):

        data = request.data.copy()

        data['unique_id'] = str(uuid.uuid4())[:12]

        serializer = TaskSubCategorySerializer(data=data)

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Task Sub Category Created Successfully",
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
class TaskSubCategoryListAPIView(ListAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    serializer_class = TaskSubCategorySerializer

    def get_queryset(self):

        return TaskSubCategory.objects.filter(
            is_delete=False
        ).order_by('-id')


# RETRIEVE
class TaskSubCategoryRetrieveAPIView(RetrieveAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = TaskSubCategory.objects.filter(
        is_delete=False
    )

    serializer_class = TaskSubCategorySerializer

    lookup_field = 'id'


# UPDATE
class TaskSubCategoryUpdateAPIView(UpdateAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = TaskSubCategory.objects.filter(
        is_delete=False
    )

    serializer_class = TaskSubCategorySerializer

    lookup_field = 'id'


# DELETE
class TaskSubCategoryDeleteAPIView(DestroyAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = TaskSubCategory.objects.all()

    serializer_class = TaskSubCategorySerializer

    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):

        instance = self.get_object()

        instance.is_delete = True
        instance.save()

        return Response(
            {
                "status": True,
                "message": "Task Sub Category Deleted Successfully"
            },
            status=status.HTTP_200_OK
        )


class TaskSubCategoryToggleAPIView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def patch(self, request, id):

        try:
            instance = TaskSubCategory.objects.get(
                id=id,
                is_delete=False
            )
        except TaskSubCategory.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "Task Sub Category not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        is_active = request.data.get("is_active")

        if is_active is None:
            return Response(
                {
                    "status": False,
                    "message": "is_active is required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if isinstance(is_active, str):
            normalized = is_active.strip().lower()
            if normalized in ["true", "1", "active", "yes"]:
                is_active = True
            elif normalized in ["false", "0", "inactive", "no"]:
                is_active = False

        instance.is_active = bool(is_active)
        instance.save(update_fields=["is_active", "updated"])

        return Response(
            {
                "status": True,
                "message": "Task Sub Category status updated successfully",
                "data": TaskSubCategorySerializer(instance).data
            },
            status=status.HTTP_200_OK
        )

# CREATE
class PriorityCreationCreateAPIView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):

        data = request.data.copy()

        data['unique_id'] = str(uuid.uuid4())[:12]

        serializer = PriorityCreationSerializer(data=data)

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Priority Created Successfully",
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
class PriorityCreationListAPIView(ListAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    serializer_class = PriorityCreationSerializer

    def get_queryset(self):

        return PriorityCreation.objects.filter(
            is_delete=False
        ).order_by('-id')


# RETRIEVE
class PriorityCreationRetrieveAPIView(RetrieveAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = PriorityCreation.objects.filter(
        is_delete=False
    )

    serializer_class = PriorityCreationSerializer

    lookup_field = 'id'


# UPDATE
class PriorityCreationUpdateAPIView(UpdateAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = PriorityCreation.objects.filter(
        is_delete=False
    )

    serializer_class = PriorityCreationSerializer

    lookup_field = 'id'


# DELETE
class PriorityCreationDeleteAPIView(DestroyAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = PriorityCreation.objects.all()

    serializer_class = PriorityCreationSerializer

    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):

        instance = self.get_object()

        instance.is_delete = True
        instance.save()

        return Response(
            {
                "status": True,
                "message": "Priority Deleted Successfully"
            },
            status=status.HTTP_200_OK
        )


class PriorityCreationToggleAPIView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def patch(self, request, id):

        try:
            instance = PriorityCreation.objects.get(
                id=id,
                is_delete=False
            )
        except PriorityCreation.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "Priority not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        is_active = request.data.get("is_active")

        if is_active is None:
            return Response(
                {
                    "status": False,
                    "message": "is_active is required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if isinstance(is_active, str):
            normalized = is_active.strip().lower()
            if normalized in ["true", "1", "active", "yes"]:
                is_active = True
            elif normalized in ["false", "0", "inactive", "no"]:
                is_active = False

        instance.is_active = bool(is_active)
        instance.save(update_fields=["is_active", "updated"])

        return Response(
            {
                "status": True,
                "message": "Priority status updated successfully",
                "data": PriorityCreationSerializer(instance).data
            },
            status=status.HTTP_200_OK
        )

# CREATE
class ProblemTypeCreateAPIView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):

        data = request.data.copy()

        data['unique_id'] = str(uuid.uuid4())[:12]

        serializer = ProblemTypeSerializer(data=data)

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Problem Type Created Successfully",
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
class ProblemTypeListAPIView(ListAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    serializer_class = ProblemTypeSerializer

    def get_queryset(self):

        return ProblemType.objects.filter(
            is_delete=False
        ).order_by('-id')


# RETRIEVE
class ProblemTypeRetrieveAPIView(RetrieveAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = ProblemType.objects.filter(
        is_delete=False
    )

    serializer_class = ProblemTypeSerializer

    lookup_field = 'id'


# UPDATE
class ProblemTypeUpdateAPIView(UpdateAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = ProblemType.objects.filter(
        is_delete=False
    )

    serializer_class = ProblemTypeSerializer

    lookup_field = 'id'


# DELETE
class ProblemTypeDeleteAPIView(DestroyAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = ProblemType.objects.all()

    serializer_class = ProblemTypeSerializer

    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):

        instance = self.get_object()

        instance.is_delete = True
        instance.save()

        return Response(
            {
                "status": True,
                "message": "Problem Type Deleted Successfully"
            },
            status=status.HTTP_200_OK
        )


class ProblemTypeToggleAPIView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def patch(self, request, id):

        try:
            instance = ProblemType.objects.get(
                id=id,
                is_delete=False
            )
        except ProblemType.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "Problem Type not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        is_active = request.data.get("is_active")

        if is_active is None:
            return Response(
                {
                    "status": False,
                    "message": "is_active is required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if isinstance(is_active, str):
            normalized = is_active.strip().lower()
            if normalized in ["true", "1", "active", "yes"]:
                is_active = True
            elif normalized in ["false", "0", "inactive", "no"]:
                is_active = False

        instance.is_active = bool(is_active)
        instance.save(update_fields=["is_active", "updated"])

        return Response(
            {
                "status": True,
                "message": "Problem Type status updated successfully",
                "data": ProblemTypeSerializer(instance).data
            },
            status=status.HTTP_200_OK
        )



# CREATE
class RemarkCreationCreateAPIView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):

        data = request.data.copy()

        data['unique_id'] = str(uuid.uuid4())[:12]

        serializer = RemarkCreationSerializer(data=data)

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Remark Created Successfully",
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
class RemarkCreationListAPIView(ListAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    serializer_class = RemarkCreationSerializer

    def get_queryset(self):

        return RemarkCreation.objects.filter(
            is_delete=False
        ).order_by('-id')


# RETRIEVE
class RemarkCreationRetrieveAPIView(RetrieveAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = RemarkCreation.objects.filter(
        is_delete=False
    )

    serializer_class = RemarkCreationSerializer

    lookup_field = 'id'


# UPDATE
class RemarkCreationUpdateAPIView(UpdateAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = RemarkCreation.objects.filter(
        is_delete=False
    )

    serializer_class = RemarkCreationSerializer

    lookup_field = 'id'


# DELETE
class RemarkCreationDeleteAPIView(DestroyAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = RemarkCreation.objects.all()

    serializer_class = RemarkCreationSerializer

    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):

        instance = self.get_object()

        instance.is_delete = True
        instance.save()

        return Response(
            {
                "status": True,
                "message": "Remark Deleted Successfully"
            },
            status=status.HTTP_200_OK
        )


class RemarkCreationToggleAPIView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def patch(self, request, id):

        try:
            instance = RemarkCreation.objects.get(
                id=id,
                is_delete=False
            )
        except RemarkCreation.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "Remark not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        is_active = request.data.get("is_active")

        if is_active is None:
            return Response(
                {
                    "status": False,
                    "message": "is_active is required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if isinstance(is_active, str):
            normalized = is_active.strip().lower()
            if normalized in ["true", "1", "active", "yes"]:
                is_active = True
            elif normalized in ["false", "0", "inactive", "no"]:
                is_active = False

        instance.is_active = bool(is_active)
        instance.save(update_fields=["is_active", "updated"])

        return Response(
            {
                "status": True,
                "message": "Remark status updated successfully",
                "data": RemarkCreationSerializer(instance).data
            },
            status=status.HTTP_200_OK
        )
