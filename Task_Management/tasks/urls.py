from django.urls import path

from .views import (

    TaskCreationCreateAPIView,
    TaskCreationListAPIView,
    TaskCreationRetrieveAPIView,
    TaskCreationUpdateAPIView,
    TaskCreationDeleteAPIView,
     SelfTaskCreateAPIView,
    SelfTaskListAPIView,
    SelfTaskRetrieveAPIView,
    SelfTaskUpdateAPIView,
    SelfTaskDeleteAPIView,
)

urlpatterns = [

    # CREATE
    path(
        'task/create/',
        TaskCreationCreateAPIView.as_view(),
        name='task-create'
    ),

    # LIST
    path(
        'task/list/',
        TaskCreationListAPIView.as_view(),
        name='task-list'
    ),

    # RETRIEVE
    path(
        'task/<int:id>/',
        TaskCreationRetrieveAPIView.as_view(),
        name='task-retrieve'
    ),

    # UPDATE
    path(
        'task/update/<int:id>/',
        TaskCreationUpdateAPIView.as_view(),
        name='task-update'
    ),

    # DELETE
    path(
        'task/delete/<int:id>/',
        TaskCreationDeleteAPIView.as_view(),
        name='task-delete'
    ),

    # CREATE
    path(
        'self-task/create/',
        SelfTaskCreateAPIView.as_view(),
        name='self-task-create'
    ),

    # LIST
    path(
        'self-task/list/',
        SelfTaskListAPIView.as_view(),
        name='self-task-list'
    ),

    # RETRIEVE
    path(
        'self-task/<int:id>/',
        SelfTaskRetrieveAPIView.as_view(),
        name='self-task-retrieve'
    ),

    # UPDATE
    path(
        'self-task/update/<int:id>/',
        SelfTaskUpdateAPIView.as_view(),
        name='self-task-update'
    ),

    # DELETE
    path(
        'self-task/delete/<int:id>/',
        SelfTaskDeleteAPIView.as_view(),
        name='self-task-delete'
    ),
]