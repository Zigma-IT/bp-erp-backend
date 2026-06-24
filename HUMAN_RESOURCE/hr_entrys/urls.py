from django.urls import path

from .views import (
    ShiftCreationCreateAPIView,
    ShiftCreationListAPIView,
    ShiftCreationRetrieveAPIView,
    ShiftCreationUpdateAPIView,
    ShiftCreationDeleteAPIView,

    ShiftRosterListCreateAPIView,
    ShiftRosterBulkUpsertAPIView,
    ShiftRosterRetrieveAPIView,
    ShiftRosterUpdateAPIView,
    ShiftRosterDeleteAPIView,

    WeekoffCreationListCreateAPIView,
    WeekoffCreationRetrieveAPIView,
    WeekoffCreationUpdateAPIView,
    WeekoffCreationDeleteAPIView,

    HolidayCreationListCreateAPIView,
    HolidayCreationRetrieveAPIView,
    HolidayCreationUpdateAPIView,
    HolidayCreationDeleteAPIView,

     LeaveEntryListCreateAPIView,
    LeaveEntryRetrieveAPIView,
    LeaveEntryUpdateAPIView,
    LeaveEntryDeleteAPIView,

)

urlpatterns = [

    path(
        'shift/create/',
        ShiftCreationCreateAPIView.as_view(),
        name='shift-create'
    ),

    path(
        'shift/list/',
        ShiftCreationListAPIView.as_view(),
        name='shift-list'
    ),

    path(
        'shift/<int:pk>/',
        ShiftCreationRetrieveAPIView.as_view(),
        name='shift-detail'
    ),

    path(
        'shift/update/<int:pk>/',
        ShiftCreationUpdateAPIView.as_view(),
        name='shift-update'
    ),

    path(
        'shift/delete/<int:pk>/',
        ShiftCreationDeleteAPIView.as_view(),
        name='shift-delete'
    ),

    # LIST + CREATE
    path(
        "shift-roster/",
        ShiftRosterListCreateAPIView.as_view(),
        name="shift-roster-list-create",
    ),

    path(
        "shift-roster/bulk-update/",
        ShiftRosterBulkUpsertAPIView.as_view(),
        name="shift-roster-bulk-update",
    ),

    # RETRIEVE
    path(
        "shift-roster/<int:pk>/",
        ShiftRosterRetrieveAPIView.as_view(),
        name="shift-roster-detail",
    ),

    # UPDATE
    path(
        "shift-roster/update/<int:pk>/",
        ShiftRosterUpdateAPIView.as_view(),
        name="shift-roster-update",
    ),

    # DELETE
    path(
        "shift-roster/delete/<int:pk>/",
        ShiftRosterDeleteAPIView.as_view(),
        name="shift-roster-delete",
    ),

    # LIST + CREATE
    path(
        "weekoff-creation/",
        WeekoffCreationListCreateAPIView.as_view(),
        name="weekoff-list-create",
    ),

    # RETRIEVE
    path(
        "weekoff-creation/<int:pk>/",
        WeekoffCreationRetrieveAPIView.as_view(),
        name="weekoff-detail",
    ),

    # UPDATE
    path(
        "weekoff-creation/update/<int:pk>/",
        WeekoffCreationUpdateAPIView.as_view(),
        name="weekoff-update",
    ),

    # DELETE
    path(
        "weekoff-creation/delete/<int:pk>/",
        WeekoffCreationDeleteAPIView.as_view(),
        name="weekoff-delete",
    ),

        # LIST + CREATE
    path(
        "holiday-creation/",
        HolidayCreationListCreateAPIView.as_view(),
        name="holiday-list-create",
    ),

    # RETRIEVE
    path(
        "holiday-creation/<int:pk>/",
        HolidayCreationRetrieveAPIView.as_view(),
        name="holiday-detail",
    ),

    # UPDATE
    path(
        "holiday-creation/update/<int:pk>/",
        HolidayCreationUpdateAPIView.as_view(),
        name="holiday-update",
    ),

    # DELETE (Soft Delete)
    path(
        "holiday-creation/delete/<int:pk>/",
        HolidayCreationDeleteAPIView.as_view(),
        name="holiday-delete",
    ),
      # LIST + CREATE
    path(
        "leave-entry/",
        LeaveEntryListCreateAPIView.as_view(),
        name="leave-entry-list-create",
    ),

    # RETRIEVE
    path(
        "leave-entry/<int:pk>/",
        LeaveEntryRetrieveAPIView.as_view(),
        name="leave-entry-detail",
    ),

    # UPDATE
    path(
        "leave-entry/update/<int:pk>/",
        LeaveEntryUpdateAPIView.as_view(),
        name="leave-entry-update",
    ),

    # DELETE
    path(
        "leave-entry/delete/<int:pk>/",
        LeaveEntryDeleteAPIView.as_view(),
        name="leave-entry-delete",
    ),
]





















