from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
    DestroyAPIView,

)

from .models import DepartmentCreation, DesignationCreation, StaffCreation, StaffEmploymentStatus,StaffDependentDetails,StaffAccountDetails
from .serializers import DepartmentCreationSerializer, DesignationCreationSerializer, StaffCreationSerializer , StaffEmploymentStatusSerializer,StaffDependentDetailsSerializer,StaffAccountDetailsSerializer


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