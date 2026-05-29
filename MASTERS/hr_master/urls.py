from django.urls import path

from .views import (
    DepartmentCreateAPIView,
    DepartmentListAPIView,
    DepartmentRetrieveAPIView,
    DepartmentDeleteAPIView,
    DepartmentToggleAPIView,
    DesignationCreateAPIView,
    DesignationListAPIView,
    DesignationRetrieveAPIView,
    DesignationDeleteAPIView,
    DesignationToggleAPIView,
    StaffCreateAPIView,
    StaffListAPIView,
    StaffRetrieveAPIView,
    StaffDeleteAPIView,
    StaffToggleAPIView,
    StaffEmploymentStatusCreateAPIView,
    StaffEmploymentStatusListAPIView,
    StaffEmploymentStatusRetrieveAPIView,
    StaffEmploymentStatusDeleteAPIView,
    StaffDependentDetailsCreateAPIView,
    StaffDependentDetailsListAPIView,
    StaffDependentDetailsRetrieveAPIView,
    StaffDependentDetailsDeleteAPIView,     
    StaffAccountDetailsCreateAPIView,
    StaffAccountDetailsListAPIView,
    StaffAccountDetailsRetrieveAPIView,
    StaffAccountDetailsDeleteAPIView,
    
    StaffQualificationCreateAPIView,
    StaffQualificationListAPIView,
    StaffQualificationRetrieveAPIView,
    StaffQualificationUpdateAPIView,
    StaffQualificationDeleteAPIView,
    StaffQualificationToggleAPIView,
     LwfEntryCreateAPIView,
    LwfEntryListAPIView,
    LwfEntryRetrieveAPIView,
    LwfEntryUpdateAPIView,
    LwfEntryDeleteAPIView,


    ProfessionalTaxCreateAPIView,
    ProfessionalTaxListAPIView,
    ProfessionalTaxRetrieveAPIView,
    ProfessionalTaxUpdateAPIView,
    ProfessionalTaxDeleteAPIView,

    LeaveMasterCreateAPIView,
    LeaveMasterListAPIView,
    LeaveMasterRetrieveAPIView,
    LeaveMasterUpdateAPIView,
    LeaveMasterDeleteAPIView,

      ReasonCreateAPIView,
    ReasonListAPIView,
    ReasonRetrieveAPIView,
    ReasonUpdateAPIView,
    ReasonDeleteAPIView,

)


urlpatterns = [
    # DEPARTMENT URLs - RESTful Pattern
    # List: GET, Create: POST
    path('departments/', DepartmentListAPIView.as_view(), name='department-list'),
    # Create POST only
    path('departments/create/', DepartmentCreateAPIView.as_view(), name='department-create'),
    # Retrieve: GET, Update: PUT/PATCH
    path('departments/<int:id>/', DepartmentRetrieveAPIView.as_view(), name='department-detail'),
    # Delete: DELETE (soft delete)
    path('departments/<int:id>/delete/', DepartmentDeleteAPIView.as_view(), name='department-delete'),
    # Toggle Status: PATCH
    path('departments/<int:id>/toggle/', DepartmentToggleAPIView.as_view(), name='department-toggle'),

    # DESIGNATION URLs - RESTful Pattern
    # List: GET, Create: POST
    path('designations/', DesignationListAPIView.as_view(), name='designation-list'),
    # Create POST only
    path('designations/create/', DesignationCreateAPIView.as_view(), name='designation-create'),
    # Retrieve: GET, Update: PUT/PATCH
    path('designations/<int:id>/', DesignationRetrieveAPIView.as_view(), name='designation-detail'),
    # Delete: DELETE (soft delete)
    path('designations/<int:id>/delete/', DesignationDeleteAPIView.as_view(), name='designation-delete'),
    # Toggle Status: PATCH
    path('designations/<int:id>/toggle/', DesignationToggleAPIView.as_view(), name='designation-toggle'),

    # STAFF URLs - RESTful Pattern
    # List: GET, Create: POST
    path('staff/', StaffListAPIView.as_view(), name='staff-list'),
    # Create POST only
    path('staff/create/', StaffCreateAPIView.as_view(), name='staff-create'),
    # Retrieve: GET, Update: PUT/PATCH
    path('staff/<int:staff_id>/', StaffRetrieveAPIView.as_view(), name='staff-detail'),
    # Delete: DELETE (soft delete)
    path('staff/<int:staff_id>/delete/', StaffDeleteAPIView.as_view(), name='staff-delete'),
    # Toggle Status: PATCH
    path('staff/<int:staff_id>/toggle/', StaffToggleAPIView.as_view(), name='staff-toggle'),

    # EMPLOYMENT STATUS URLs
    path('employment-status/', StaffEmploymentStatusListAPIView.as_view(), name='employment-status-list'),
    path('employment-status/create/', StaffEmploymentStatusCreateAPIView.as_view(), name='employment-status-create'),
    path('employment-status/<int:staff_employment_status_id>/', StaffEmploymentStatusRetrieveAPIView.as_view(), name='employment-status-detail'),
    path('employment-status/<int:staff_employment_status_id>/delete/', StaffEmploymentStatusDeleteAPIView.as_view(), name='employment-status-delete'),

    # DEPENDENT DETAILS URLs
    path('dependent-details/', StaffDependentDetailsListAPIView.as_view(), name='dependent-details-list'),
    path('dependent-details/create/', StaffDependentDetailsCreateAPIView.as_view(), name='dependent-details-create'),
    path('dependent-details/<int:staff_dep_id>/', StaffDependentDetailsRetrieveAPIView.as_view(), name='dependent-details-detail'),
    path('dependent-details/<int:staff_dep_id>/delete/', StaffDependentDetailsDeleteAPIView.as_view(), name='dependent-details-delete'),

    # STAFF ACCOUNT URLs
    path('staff-account/', StaffAccountDetailsListAPIView.as_view(), name='staff-account-list'),
    path('staff-account/create/', StaffAccountDetailsCreateAPIView.as_view(), name='staff-account-create'),
    path('staff-account/<int:staff_acc_id>/', StaffAccountDetailsRetrieveAPIView.as_view(), name='staff-account-detail'),
    path('staff-account/<int:staff_acc_id>/delete/', StaffAccountDetailsDeleteAPIView.as_view(), name='staff-account-delete'),


    # CREATE
    path(
        'qualification/create/',
        StaffQualificationCreateAPIView.as_view(),
        name='qualification-create'
    ),

    # LIST
    path(
        'qualification/list/',
        StaffQualificationListAPIView.as_view(),
        name='qualification-list'
    ),

    # RETRIEVE
    path(
        'qualification/retrieve/<int:staff_qual_id>/',
        StaffQualificationRetrieveAPIView.as_view(),
        name='qualification-retrieve'
    ),

    # UPDATE
    path(
        'qualification/update/<int:staff_qual_id>/',
        StaffQualificationUpdateAPIView.as_view(),
        name='qualification-update'
    ),

    # DELETE
    path(
        'qualification/delete/<int:staff_qual_id>/',
        StaffQualificationDeleteAPIView.as_view(),
        name='qualification-delete'
    ),
    path(
        'qualification/toggle/<int:staff_qual_id>/',
        StaffQualificationToggleAPIView.as_view(),
        name='qualification-toggle'
    ),
     # CREATE
    path(
        'lwf-entry/create/',
        LwfEntryCreateAPIView.as_view(),
        name='lwf-entry-create'
    ),

    # LIST
    path(
        'lwf-entry/list/',
        LwfEntryListAPIView.as_view(),
        name='lwf-entry-list'
    ),

    # RETRIEVE
    path(
        'lwf-entry/retrieve/<int:lwf_id>/',
        LwfEntryRetrieveAPIView.as_view(),
        name='lwf-entry-retrieve'
    ),

    # UPDATE
    path(
        'lwf-entry/update/<int:lwf_id>/',
        LwfEntryUpdateAPIView.as_view(),
        name='lwf-entry-update'
    ),

    # DELETE
    path(
        'lwf-entry/delete/<int:lwf_id>/',
        LwfEntryDeleteAPIView.as_view(),
        name='lwf-entry-delete'
    ),
      # CREATE
    path(
        'prof-tax/create/',
        ProfessionalTaxCreateAPIView.as_view(),
        name='prof-tax-create'
    ),

    # LIST
    path(
        'prof-tax/list/',
        ProfessionalTaxListAPIView.as_view(),
        name='prof-tax-list'
    ),

    # RETRIEVE
    path(
        'prof-tax/retrieve/<int:id>/',
        ProfessionalTaxRetrieveAPIView.as_view(),
        name='prof-tax-retrieve'
    ),

    # UPDATE
    path(
        'prof-tax/update/<int:id>/',
        ProfessionalTaxUpdateAPIView.as_view(),
        name='prof-tax-update'
    ),

    # DELETE
    path(
        'prof-tax/delete/<int:id>/',
        ProfessionalTaxDeleteAPIView.as_view(),
        name='prof-tax-delete'
    ),

    # CREATE
    path(
        'leave-master/create/',
        LeaveMasterCreateAPIView.as_view(),
        name='leave-master-create'
    ),

    # LIST
    path(
        'leave-master/list/',
        LeaveMasterListAPIView.as_view(),
        name='leave-master-list'
    ),

    # RETRIEVE
    path(
        'leave-master/retrieve/<int:id>/',
        LeaveMasterRetrieveAPIView.as_view(),
        name='leave-master-retrieve'
    ),

    # UPDATE
    path(
        'leave-master/update/<int:id>/',
        LeaveMasterUpdateAPIView.as_view(),
        name='leave-master-update'
    ),

    # DELETE
    path(
        'leave-master/delete/<int:id>/',
        LeaveMasterDeleteAPIView.as_view(),
        name='leave-master-delete'
    ),
    # REASON
    path(
        'reason/create/',
        ReasonCreateAPIView.as_view(),
        name='reason-create'
    ),
    path(
        'reason/list/',
        ReasonListAPIView.as_view(),
        name='reason-list'
    ),
    path(
        'reason/retrieve/<int:pk>/',
        ReasonRetrieveAPIView.as_view(),
        name='reason-retrieve'
    ),
    path(
        'reason/update/<int:pk>/',
        ReasonUpdateAPIView.as_view(),
        name='reason-update'
    ),
    path(
        'reason/delete/<int:pk>/',
        ReasonDeleteAPIView.as_view(),
        name='reason-delete'
    ),
]
