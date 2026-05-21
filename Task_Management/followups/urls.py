from django.urls import path

from .views import (

    TaskFollowupsCreateAPIView,
    TaskFollowupsListAPIView,
    TaskFollowupsRetrieveAPIView,
    TaskFollowupsUpdateAPIView,
    TaskFollowupsDeleteAPIView,
)

urlpatterns = [

    # CREATE
    path(
        'task-followups/create/',
        TaskFollowupsCreateAPIView.as_view(),
        name='task-followups-create'
    ),

    # LIST
    path(
        'task-followups/list/',
        TaskFollowupsListAPIView.as_view(),
        name='task-followups-list'
    ),

    # RETRIEVE
    path(
        'task-followups/<int:id>/',
        TaskFollowupsRetrieveAPIView.as_view(),
        name='task-followups-retrieve'
    ),

    # UPDATE
    path(
        'task-followups/update/<int:id>/',
        TaskFollowupsUpdateAPIView.as_view(),
        name='task-followups-update'
    ),

    # DELETE
    path(
        'task-followups/delete/<int:id>/',
        TaskFollowupsDeleteAPIView.as_view(),
        name='task-followups-delete'
    ),
]