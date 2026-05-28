from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
    DestroyAPIView,

)
from django.db import connection
from django.db.utils import OperationalError
from django.utils import timezone

from .models import DepartmentCreation, DesignationCreation, StaffCreation, StaffEmploymentStatus,StaffDependentDetails,StaffAccountDetails, StaffQualificationDetails, LwfEntry
from .serializers import DepartmentCreationSerializer, DesignationCreationSerializer, StaffCreationSerializer , StaffEmploymentStatusSerializer,StaffDependentDetailsSerializer,StaffAccountDetailsSerializer, StaffQualificationSerializer, LwfEntrySerializer


def _is_lwf_schema_mismatch(error: Exception) -> bool:
    message = str(error).lower()
    return "unknown column" in message and any(
        column in message
        for column in [
            "deduction_frequency",
            "deduction_months",
            "employer_amount",
            "excluded_designations",
            "effective_from",
        ]
    )


def _legacy_lwf_payload(data):
    timestamp = timezone.now()
    return {
        "unique_id": data.get("unique_id") or f"LWF-{int(timestamp.timestamp() * 1000)}",
        "project_id": data.get("project_id", ""),
        "state": data.get("state", ""),
        "amount": data.get("amount") or 0,
        "is_active": data.get("is_active", 1),
        "is_delete": data.get("is_delete", 0),
        "acc_year": data.get("acc_year", ""),
        "session_id": data.get("session_id", "web"),
        "sess_user_type": data.get("sess_user_type", "admin"),
        "sess_user_id": data.get("sess_user_id", "0"),
        "sess_company_id": data.get("sess_company_id", "0"),
        "sess_branch_id": data.get("sess_branch_id", "0"),
        "created": timestamp,
        "updated": timestamp,
    }


def _create_lwf_entry_legacy(data):
    payload = _legacy_lwf_payload(data)
    columns = list(payload.keys())
    placeholders = ", ".join(["%s"] * len(columns))
    sql = f"INSERT INTO lwf_entry ({', '.join(columns)}) VALUES ({placeholders})"

    with connection.cursor() as cursor:
        cursor.execute(sql, [payload[column] for column in columns])
        lwf_id = cursor.lastrowid

    payload["lwf_id"] = lwf_id
    return payload


def _update_lwf_entry_legacy(lwf_id, data):
    payload = {
        "project_id": data.get("project_id", ""),
        "state": data.get("state", ""),
        "amount": data.get("amount") or 0,
        "is_active": data.get("is_active", 1),
        "is_delete": data.get("is_delete", 0),
        "acc_year": data.get("acc_year", ""),
        "session_id": data.get("session_id", "web"),
        "sess_user_type": data.get("sess_user_type", "admin"),
        "sess_user_id": data.get("sess_user_id", "0"),
        "sess_company_id": data.get("sess_company_id", "0"),
        "sess_branch_id": data.get("sess_branch_id", "0"),
        "updated": timezone.now(),
    }

    assignments = ", ".join(f"{column} = %s" for column in payload.keys())
    sql = f"UPDATE lwf_entry SET {assignments} WHERE lwf_id = %s"

    with connection.cursor() as cursor:
        cursor.execute(sql, [*payload.values(), lwf_id])

    payload["lwf_id"] = lwf_id
    return payload

def _soft_delete_lwf_entry_legacy(lwf_id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE lwf_entry SET is_delete = 1, updated = %s WHERE lwf_id = %s", [timezone.now(), lwf_id])


def _fetch_lwf_legacy_rows(lwf_id=None):
    sql = """
        SELECT lwf_id, unique_id, project_id, state, amount, is_active, is_delete,
               updated, created, acc_year, session_id, sess_user_type,
               sess_user_id, sess_company_id, sess_branch_id
        FROM lwf_entry
        WHERE is_delete = 0
    """
    params = []
    if lwf_id is not None:
        sql += " AND lwf_id = %s"
        params.append(lwf_id)
    sql += " ORDER BY lwf_id DESC"

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _serialize_lwf_legacy_row(row):
    return {
        "lwf_id": row.get("lwf_id"),
        "unique_id": row.get("unique_id"),
        "project_id": row.get("project_id"),
        "state": row.get("state"),
        "amount": row.get("amount"),
        "deduction_frequency": None,
        "deduction_months": None,
        "employer_amount": None,
        "excluded_designations": None,
        "effective_from": None,
        "is_active": row.get("is_active"),
        "is_delete": row.get("is_delete"),
        "updated": row.get("updated"),
        "created": row.get("created"),
        "acc_year": row.get("acc_year"),
        "session_id": row.get("session_id"),
        "sess_user_type": row.get("sess_user_type"),
        "sess_user_id": row.get("sess_user_id"),
        "sess_company_id": row.get("sess_company_id"),
        "sess_branch_id": row.get("sess_branch_id"),
    }


# CREATE
class DepartmentCreateAPIView(APIView):

    def post(self, request):

        serializer = DepartmentCreationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Department Created Successfully",
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
class DepartmentListAPIView(ListAPIView):

    serializer_class = DepartmentCreationSerializer

    def get_queryset(self):
        return DepartmentCreation.objects.filter(is_delete=False).order_by('-id')


# RETRIEVE & UPDATE (Combined)
class DepartmentRetrieveAPIView(RetrieveAPIView):

    queryset = DepartmentCreation.objects.filter(is_delete=False)
    serializer_class = DepartmentCreationSerializer
    lookup_field = 'id'
    
    def put(self, request, *args, **kwargs):
        """Handle PUT requests for updating"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "status": True,
                    "message": "Department Updated Successfully",
                    "data": serializer.data
                }
            )
        
        return Response(
            {
                "status": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def patch(self, request, *args, **kwargs):
        """Handle PATCH requests for partial updates"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "status": True,
                    "message": "Department Updated Successfully",
                    "data": serializer.data
                }
            )
        
        return Response(
            {
                "status": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


# UPDATE
class DepartmentUpdateAPIView(UpdateAPIView):

    queryset = DepartmentCreation.objects.filter(is_delete=False)
    serializer_class = DepartmentCreationSerializer
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):

        partial = kwargs.pop('partial', False)

        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Department Updated Successfully",
                    "data": serializer.data
                }
            )

        return Response(
            {
                "status": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


# DELETE (SOFT DELETE)
class DepartmentDeleteAPIView(DestroyAPIView):

    queryset = DepartmentCreation.objects.all()
    serializer_class = DepartmentCreationSerializer
    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):

        instance = self.get_object()

        instance.is_delete = True
        instance.save()

        return Response(
            {
                "status": True,
                "message": "Department Deleted Successfully"
            },
            status=status.HTTP_200_OK
        )

        

# CREATE
class DesignationCreateAPIView(APIView):

    def post(self, request):

        serializer = DesignationCreationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Designation Created Successfully",
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
class DesignationListAPIView(ListAPIView):

    serializer_class = DesignationCreationSerializer

    def get_queryset(self):
        return DesignationCreation.objects.filter(
            is_delete=False
        ).order_by('-id')


# RETRIEVE & UPDATE (Combined)
class DesignationRetrieveAPIView(RetrieveAPIView):

    queryset = DesignationCreation.objects.filter(is_delete=False)
    serializer_class = DesignationCreationSerializer
    lookup_field = 'id'
    
    def put(self, request, *args, **kwargs):
        """Handle PUT requests for updating"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "status": True,
                    "message": "Designation Updated Successfully",
                    "data": serializer.data
                }
            )
        
        return Response(
            {
                "status": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def patch(self, request, *args, **kwargs):
        """Handle PATCH requests for partial updates"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "status": True,
                    "message": "Designation Updated Successfully",
                    "data": serializer.data
                }
            )
        
        return Response(
            {
                "status": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


# UPDATE
class DesignationUpdateAPIView(UpdateAPIView):

    queryset = DesignationCreation.objects.filter(is_delete=False)

    serializer_class = DesignationCreationSerializer

    lookup_field = 'id'

    def put(self, request, *args, **kwargs):

        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Designation Updated Successfully",
                    "data": serializer.data
                }
            )

        return Response(
            {
                "status": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


# DELETE
class DesignationDeleteAPIView(DestroyAPIView):

    queryset = DesignationCreation.objects.all()

    serializer_class = DesignationCreationSerializer

    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):

        instance = self.get_object()

        instance.is_delete = True
        instance.save()

        return Response(
            {
                "status": True,
                "message": "Designation Deleted Successfully"
            },
            status=status.HTTP_200_OK
        )


# CREATE
class StaffCreateAPIView(APIView):

    def post(self, request):

        serializer = StaffCreationSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Staff Created Successfully",
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
class StaffListAPIView(ListAPIView):

    serializer_class = StaffCreationSerializer

    def get_queryset(self):
        return StaffCreation.objects.filter(
            is_delete=False
        ).order_by('-staff_id')


# RETRIEVE & UPDATE (Combined)
class StaffRetrieveAPIView(RetrieveAPIView):

    queryset = StaffCreation.objects.filter(is_delete=False)
    serializer_class = StaffCreationSerializer
    lookup_field = 'staff_id'
    
    def put(self, request, *args, **kwargs):
        """Handle PUT requests for updating"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "status": True,
                    "message": "Staff Updated Successfully",
                    "data": serializer.data
                }
            )
        
        return Response(
            {
                "status": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def patch(self, request, *args, **kwargs):
        """Handle PATCH requests for partial updates"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "status": True,
                    "message": "Staff Updated Successfully",
                    "data": serializer.data
                }
            )
        
        return Response(
            {
                "status": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


# UPDATE
class StaffUpdateAPIView(UpdateAPIView):

    queryset = StaffCreation.objects.filter(
        is_delete=False
    )

    serializer_class = StaffCreationSerializer

    lookup_field = 'staff_id'


# DELETE
class StaffDeleteAPIView(DestroyAPIView):

    queryset = StaffCreation.objects.all()

    serializer_class = StaffCreationSerializer

    lookup_field = 'staff_id'

    def delete(self, request, *args, **kwargs):

        instance = self.get_object()

        instance.is_delete = True
        instance.save()

        return Response(
            {
                "status": True,
                "message": "Staff Deleted Successfully"
            },
            status=status.HTTP_200_OK
        )


# CREATE
class StaffEmploymentStatusCreateAPIView(APIView):

    def post(self, request):

        serializer = StaffEmploymentStatusSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Employment Status Created Successfully",
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
class StaffEmploymentStatusListAPIView(ListAPIView):

    serializer_class = StaffEmploymentStatusSerializer

    def get_queryset(self):

        return StaffEmploymentStatus.objects.filter(
            is_delete=False
        ).order_by('-staff_employment_status_id')


# RETRIEVE
class StaffEmploymentStatusRetrieveAPIView(RetrieveAPIView):

    queryset = StaffEmploymentStatus.objects.filter(
        is_delete=False
    )

    serializer_class = StaffEmploymentStatusSerializer

    lookup_field = 'staff_employment_status_id'


# UPDATE
class StaffEmploymentStatusUpdateAPIView(UpdateAPIView):

    queryset = StaffEmploymentStatus.objects.filter(
        is_delete=False
    )

    serializer_class = StaffEmploymentStatusSerializer

    lookup_field = 'staff_employment_status_id'


# DELETE
class StaffEmploymentStatusDeleteAPIView(DestroyAPIView):

    queryset = StaffEmploymentStatus.objects.all()

    serializer_class = StaffEmploymentStatusSerializer

    lookup_field = 'staff_employment_status_id'

    def delete(self, request, *args, **kwargs):

        instance = self.get_object()

        instance.is_delete = True
        instance.save()

        return Response(
            {
                "status": True,
                "message": "Employment Status Deleted Successfully"
            },
            status=status.HTTP_200_OK
        )
# CREATE
class StaffDependentDetailsCreateAPIView(APIView):

    def post(self, request):

        serializer = StaffDependentDetailsSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Dependent Details Created Successfully",
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
class StaffDependentDetailsListAPIView(ListAPIView):

    serializer_class = StaffDependentDetailsSerializer

    def get_queryset(self):

        return StaffDependentDetails.objects.filter(
            is_delete=False
        ).order_by('-staff_dep_id')


# RETRIEVE
class StaffDependentDetailsRetrieveAPIView(RetrieveAPIView):

    queryset = StaffDependentDetails.objects.filter(
        is_delete=False
    )

    serializer_class = StaffDependentDetailsSerializer

    lookup_field = 'staff_dep_id'


# UPDATE
class StaffDependentDetailsUpdateAPIView(UpdateAPIView):

    queryset = StaffDependentDetails.objects.filter(
        is_delete=False
    )

    serializer_class = StaffDependentDetailsSerializer

    lookup_field = 'staff_dep_id'


# DELETE
class StaffDependentDetailsDeleteAPIView(DestroyAPIView):

    queryset = StaffDependentDetails.objects.all()

    serializer_class = StaffDependentDetailsSerializer

    lookup_field = 'staff_dep_id'

    def delete(self, request, *args, **kwargs):

        instance = self.get_object()

        instance.is_delete = True
        instance.save()

        return Response(
            {
                "status": True,
                "message": "Dependent Details Deleted Successfully"
            },
            status=status.HTTP_200_OK
        )

# CREATE
class StaffAccountDetailsCreateAPIView(APIView):

    def post(self, request):

        serializer = StaffAccountDetailsSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Staff Account Details Created Successfully",
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
class StaffAccountDetailsListAPIView(ListAPIView):

    serializer_class = StaffAccountDetailsSerializer

    def get_queryset(self):

        return StaffAccountDetails.objects.filter(
            is_delete=False
        ).order_by('-staff_acc_id')


# RETRIEVE
class StaffAccountDetailsRetrieveAPIView(RetrieveAPIView):

    queryset = StaffAccountDetails.objects.filter(
        is_delete=False
    )

    serializer_class = StaffAccountDetailsSerializer

    lookup_field = 'staff_acc_id'


# UPDATE
class StaffAccountDetailsUpdateAPIView(UpdateAPIView):

    queryset = StaffAccountDetails.objects.filter(
        is_delete=False
    )

    serializer_class = StaffAccountDetailsSerializer

    lookup_field = 'staff_acc_id'


# DELETE
class StaffAccountDetailsDeleteAPIView(DestroyAPIView):

    queryset = StaffAccountDetails.objects.all()

    serializer_class = StaffAccountDetailsSerializer

    lookup_field = 'staff_acc_id'

    def delete(self, request, *args, **kwargs):

        instance = self.get_object()

        instance.is_delete = True
        instance.save()

        return Response(
            {
                "status": True,
                "message": "Staff Account Details Deleted Successfully"
            },
            status=status.HTTP_200_OK
        )


# ========== TOGGLE ENDPOINTS ==========

# DEPARTMENT TOGGLE
class DepartmentToggleAPIView(APIView):
    """Toggle the active status of a department"""
    
    def patch(self, request, *args, **kwargs):
        try:
            department_id = kwargs.get('id')
            department = DepartmentCreation.objects.get(id=department_id, is_delete=False)
            
            # Toggle the is_active status
            department.is_active = not department.is_active
            # Also update active_status field if needed
            department.active_status = 'Active' if department.is_active else 'Inactive'
            department.save()
            
            serializer = DepartmentCreationSerializer(department)
            
            return Response(
                {
                    "status": True,
                    "message": f"Department status toggled successfully",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        except DepartmentCreation.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "Department not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )


# DESIGNATION TOGGLE
class DesignationToggleAPIView(APIView):
    """Toggle the active status of a designation"""
    
    def patch(self, request, *args, **kwargs):
        try:
            designation_id = kwargs.get('id')
            designation = DesignationCreation.objects.get(id=designation_id, is_delete=False)
            
            # Toggle the is_active status
            designation.is_active = not designation.is_active
            designation.save()
            
            serializer = DesignationCreationSerializer(designation)
            
            return Response(
                {
                    "status": True,
                    "message": "Designation status toggled successfully",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        except DesignationCreation.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "Designation not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )


# STAFF TOGGLE
class StaffToggleAPIView(APIView):
    """Toggle the active status of a staff member"""
    
    def patch(self, request, *args, **kwargs):
        try:
            staff_id = kwargs.get('staff_id')
            staff = StaffCreation.objects.get(staff_id=staff_id, is_delete=False)
            
            # Toggle the is_active status
            staff.is_active = not staff.is_active
            staff.save()
            
            serializer = StaffCreationSerializer(staff)
            
            return Response(
                {
                    "status": True,
                    "message": "Staff status toggled successfully",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        except StaffCreation.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "Staff not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )


# QUALIFICATION TOGGLE
class StaffQualificationToggleAPIView(APIView):
    """Toggle the active status of a qualification"""

    permission_classes = [AllowAny]
    authentication_classes = []

    def patch(self, request, *args, **kwargs):
        try:
            staff_qual_id = kwargs.get('staff_qual_id')
            qualification = StaffQualificationDetails.objects.get(
                staff_qual_id=staff_qual_id,
                is_delete=0
            )

            qualification.is_active = 0 if qualification.is_active else 1
            qualification.save()

            serializer = StaffQualificationSerializer(qualification)

            return Response(
                {
                    "status": True,
                    "message": "Qualification status toggled successfully",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        except StaffQualificationDetails.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "Qualification not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )


# CREATE
class StaffQualificationCreateAPIView(CreateAPIView):

    queryset = StaffQualificationDetails.objects.all()

    serializer_class = StaffQualificationSerializer

    permission_classes = [AllowAny]

    authentication_classes = []


# LIST
class StaffQualificationListAPIView(ListAPIView):

    serializer_class = StaffQualificationSerializer

    permission_classes = [AllowAny]

    authentication_classes = []

    def get_queryset(self):

        return StaffQualificationDetails.objects.filter(
            is_delete=0
        ).order_by('-staff_qual_id')


# RETRIEVE
class StaffQualificationRetrieveAPIView(RetrieveAPIView):

    queryset = StaffQualificationDetails.objects.all()

    serializer_class = StaffQualificationSerializer

    permission_classes = [AllowAny]

    authentication_classes = []

    lookup_field = 'staff_qual_id'


# UPDATE
class StaffQualificationUpdateAPIView(UpdateAPIView):

    queryset = StaffQualificationDetails.objects.all()

    serializer_class = StaffQualificationSerializer

    permission_classes = [AllowAny]

    authentication_classes = []

    lookup_field = 'staff_qual_id'


# DELETE
class StaffQualificationDeleteAPIView(DestroyAPIView):

    queryset = StaffQualificationDetails.objects.all()

    serializer_class = StaffQualificationSerializer

    permission_classes = [AllowAny]

    authentication_classes = []

    lookup_field = 'staff_qual_id'


# CREATE
class LwfEntryCreateAPIView(APIView):

    permission_classes = [AllowAny]

    authentication_classes = []

    def post(self, request):

        serializer = LwfEntrySerializer(
            data=request.data
        )

        if serializer.is_valid():
            try:
                serializer.save()

                return Response(
                    {
                        "status": True,
                        "message": "LWF Entry Created Successfully",
                        "data": serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
            except OperationalError as error:
                if not _is_lwf_schema_mismatch(error):
                    raise

                data = _create_lwf_entry_legacy(request.data)
                return Response(
                    {
                        "status": True,
                        "message": "LWF Entry Created Successfully",
                        "data": data,
                        "warning": "Saved using legacy LWF schema fallback."
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
class LwfEntryListAPIView(ListAPIView):

    permission_classes = [AllowAny]

    authentication_classes = []

    serializer_class = LwfEntrySerializer

    def get_queryset(self):

        return LwfEntry.objects.filter(
            is_delete=0
        ).order_by('-lwf_id')

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except OperationalError as error:
            if not _is_lwf_schema_mismatch(error):
                raise

            rows = [_serialize_lwf_legacy_row(row) for row in _fetch_lwf_legacy_rows()]
            return Response(rows)


# RETRIEVE
class LwfEntryRetrieveAPIView(RetrieveAPIView):

    permission_classes = [AllowAny]

    authentication_classes = []

    queryset = LwfEntry.objects.filter(
        is_delete=0
    )

    serializer_class = LwfEntrySerializer

    lookup_field = 'lwf_id'

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except OperationalError as error:
            if not _is_lwf_schema_mismatch(error):
                raise

            lwf_id = kwargs.get(self.lookup_field)
            rows = _fetch_lwf_legacy_rows(lwf_id)
            if not rows:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response(_serialize_lwf_legacy_row(rows[0]))


# UPDATE
class LwfEntryUpdateAPIView(UpdateAPIView):

    permission_classes = [AllowAny]

    authentication_classes = []

    queryset = LwfEntry.objects.filter(
        is_delete=0
    )

    serializer_class = LwfEntrySerializer

    lookup_field = 'lwf_id'

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)

            if serializer.is_valid():
                try:
                    serializer.save()
                    return Response(
                        {
                            "status": True,
                            "message": "LWF Entry Updated Successfully",
                            "data": serializer.data
                        }
                    )
                except OperationalError as error:
                    if not _is_lwf_schema_mismatch(error):
                        raise

                    data = _update_lwf_entry_legacy(kwargs.get(self.lookup_field), request.data)
                    return Response(
                        {
                            "status": True,
                            "message": "LWF Entry Updated Successfully",
                            "data": data,
                            "warning": "Updated using legacy LWF schema fallback."
                        }
                    )

            return Response(
                {
                    "status": False,
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except OperationalError as error:
            if not _is_lwf_schema_mismatch(error):
                raise

            data = _update_lwf_entry_legacy(kwargs.get(self.lookup_field), request.data)
            return Response(
                {
                    "status": True,
                    "message": "LWF Entry Updated Successfully",
                    "data": data,
                    "warning": "Updated using legacy LWF schema fallback."
                }
            )


# DELETE
class LwfEntryDeleteAPIView(DestroyAPIView):

    permission_classes = [AllowAny]

    authentication_classes = []

    queryset = LwfEntry.objects.all()

    serializer_class = LwfEntrySerializer

    lookup_field = 'lwf_id'

    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.is_delete = 1
            instance.save()
        except OperationalError as error:
            if not _is_lwf_schema_mismatch(error):
                raise
            _soft_delete_lwf_entry_legacy(kwargs.get(self.lookup_field))

        return Response(
            {
                "status": True,
                "message": "LWF Entry Deleted Successfully"
            },
            status=status.HTTP_200_OK
        )
