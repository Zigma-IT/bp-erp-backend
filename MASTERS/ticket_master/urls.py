from django.urls import path

from .views import (
    TaskCategoryCreateAPIView,
    TaskCategoryListAPIView,
    TaskCategoryRetrieveAPIView,
    TaskCategoryUpdateAPIView,
    TaskCategoryDeleteAPIView,
    TaskCategoryToggleAPIView,

    TaskSubCategoryCreateAPIView,
    TaskSubCategoryListAPIView,
    TaskSubCategoryRetrieveAPIView,
    TaskSubCategoryUpdateAPIView,
    TaskSubCategoryDeleteAPIView,
    TaskSubCategoryToggleAPIView,

    PriorityCreationCreateAPIView,
    PriorityCreationListAPIView,
    PriorityCreationRetrieveAPIView,
    PriorityCreationUpdateAPIView,
    PriorityCreationDeleteAPIView,
    PriorityCreationToggleAPIView,

    ProblemTypeCreateAPIView,
    ProblemTypeListAPIView,
    ProblemTypeRetrieveAPIView,
    ProblemTypeUpdateAPIView,
    ProblemTypeDeleteAPIView,
    ProblemTypeToggleAPIView,

    RemarkCreationCreateAPIView,
    RemarkCreationListAPIView,
    RemarkCreationRetrieveAPIView,
    RemarkCreationUpdateAPIView,
    RemarkCreationDeleteAPIView,
    RemarkCreationToggleAPIView,
)

urlpatterns = [

    # ================= TASK CATEGORY =================

    path(
        'task-category/create/',
        TaskCategoryCreateAPIView.as_view(),
        name='task-category-create'
    ),

    path(
        'task-category/list/',
        TaskCategoryListAPIView.as_view(),
        name='task-category-list'
    ),

    path(
        'task-category/<int:id>/',
        TaskCategoryRetrieveAPIView.as_view(),
        name='task-category-retrieve'
    ),

    path(
        'task-category/update/<int:id>/',
        TaskCategoryUpdateAPIView.as_view(),
        name='task-category-update'
    ),

    path(
        'task-category/delete/<int:id>/',
        TaskCategoryDeleteAPIView.as_view(),
        name='task-category-delete'
    ),

    path(
        'task-category/toggle/<int:id>/',
        TaskCategoryToggleAPIView.as_view(),
        name='task-category-toggle'
    ),

    # ================= TASK SUB CATEGORY =================

    path(
        'task-sub-category/create/',
        TaskSubCategoryCreateAPIView.as_view(),
        name='task-sub-category-create'
    ),

    path(
        'task-sub-category/list/',
        TaskSubCategoryListAPIView.as_view(),
        name='task-sub-category-list'
    ),

    path(
        'task-sub-category/<int:id>/',
        TaskSubCategoryRetrieveAPIView.as_view(),
        name='task-sub-category-retrieve'
    ),

    path(
        'task-sub-category/update/<int:id>/',
        TaskSubCategoryUpdateAPIView.as_view(),
        name='task-sub-category-update'
    ),

    path(
        'task-sub-category/delete/<int:id>/',
        TaskSubCategoryDeleteAPIView.as_view(),
        name='task-sub-category-delete'
    ),

    path(
        'task-sub-category/toggle/<int:id>/',
        TaskSubCategoryToggleAPIView.as_view(),
        name='task-sub-category-toggle'
    ),

    # ================= PRIORITY =================

    path(
        'priority/create/',
        PriorityCreationCreateAPIView.as_view(),
        name='priority-create'
    ),

    path(
        'priority/list/',
        PriorityCreationListAPIView.as_view(),
        name='priority-list'
    ),

    path(
        'priority/<int:id>/',
        PriorityCreationRetrieveAPIView.as_view(),
        name='priority-retrieve'
    ),

    path(
        'priority/update/<int:id>/',
        PriorityCreationUpdateAPIView.as_view(),
        name='priority-update'
    ),

    path(
        'priority/delete/<int:id>/',
        PriorityCreationDeleteAPIView.as_view(),
        name='priority-delete'
    ),

    path(
        'priority/toggle/<int:id>/',
        PriorityCreationToggleAPIView.as_view(),
        name='priority-toggle'
    ),

    # ================= PROBLEM TYPE =================

    path(
        'problem-type/create/',
        ProblemTypeCreateAPIView.as_view(),
        name='problem-type-create'
    ),

    path(
        'problem-type/list/',
        ProblemTypeListAPIView.as_view(),
        name='problem-type-list'
    ),

    path(
        'problem-type/<int:id>/',
        ProblemTypeRetrieveAPIView.as_view(),
        name='problem-type-retrieve'
    ),

    path(
        'problem-type/update/<int:id>/',
        ProblemTypeUpdateAPIView.as_view(),
        name='problem-type-update'
    ),

    path(
        'problem-type/delete/<int:id>/',
        ProblemTypeDeleteAPIView.as_view(),
        name='problem-type-delete'
    ),

    path(
        'problem-type/toggle/<int:id>/',
        ProblemTypeToggleAPIView.as_view(),
        name='problem-type-toggle'
    ),

    # ================= REMARK CREATION =================

    path(
        'remark/create/',
        RemarkCreationCreateAPIView.as_view(),
        name='remark-create'
    ),

    path(
        'remark/list/',
        RemarkCreationListAPIView.as_view(),
        name='remark-list'
    ),

    path(
        'remark/<int:id>/',
        RemarkCreationRetrieveAPIView.as_view(),
        name='remark-retrieve'
    ),

    path(
        'remark/update/<int:id>/',
        RemarkCreationUpdateAPIView.as_view(),
        name='remark-update'
    ),

    path(
        'remark/delete/<int:id>/',
        RemarkCreationDeleteAPIView.as_view(),
        name='remark-delete'
    ),

    path(
        'remark/toggle/<int:id>/',
        RemarkCreationToggleAPIView.as_view(),
        name='remark-toggle'
    ),

]
