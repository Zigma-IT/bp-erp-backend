from django.urls import path, include

from MASTERS.api_router import ExtendedDefaultRouter
from collections import OrderedDict
from . import views

# Initialize router for ViewSets
router = ExtendedDefaultRouter()
router.register(r'main-screens', views.MainScreenViewSet)
router.extra_api_root_dict = OrderedDict ({
    "users-creation": "user-list",
    "users-creation-create": "user-create",
    "user-screens": "user-screen-list",
    "user-screens-create": "user-screen-create",
    "user-types": "user-type-list",
    "user-types-create": "user-type-create",
    "main-screens-list": "main-screen-list",
    "screen-sections": "screen-section-list",
    "user-permissions": "user-permission-list",
    "user-permissions-create": "user-permission-create",
})

# User Creation endpoints
user_patterns = [
    path('users_creation/', views.user_list, name='user-list'),
    path('users_creation/create/', views.create_user, name='user-create'),
    path('users_creation/<int:pk>/', views.update_user, name='user-update'),
    path('users_creation/<int:pk>/toggle/', views.toggle_user_status, name='user-toggle'),
]

# User Screen endpoints
user_screen_patterns = [
    path('user-screens/', views.user_screen_list, name='user-screen-list'),
    path('user-screens/create/', views.create_user_screen, name='user-screen-create'),
    path('user-screens/<int:pk>/', views.update_user_screen, name='user-screen-update'),
    path('user-screens/<int:pk>/toggle/', views.toggle_status, name='user-screen-toggle'),
]

# User Type endpoints
user_type_patterns = [
    path('user-types/', views.user_type_list, name='user-type-list'),
    path('user-types/create/', views.create_user_type, name='user-type-create'),
    path('user-types/<int:pk>/', views.update_user_type, name='user-type-update'),
    path('user-types/<int:pk>/toggle/', views.toggle_user_type, name='user-type-toggle'),
]

# Main Screen & Screen Section endpoints
screen_patterns = [
    path('main-screens/list/', views.main_screen_list, name='main-screen-list'),
    path('screen-sections/', views.screen_section_list, name='screen-section-list'),
]

# User Type Permission endpoints
permission_patterns = [
    path('user-permissions/', views.user_type_permission_list, name='user-permission-list'),
    path('user-permissions/create/', views.create_user_type_permission, name='user-permission-create'),
    path('user-permissions/<int:pk>/', views.update_user_type_permission, name='user-permission-update'),
    path('user-permissions/<int:pk>/toggle/', views.toggle_user_type_permission, name='user-permission-toggle'),
]

# Combine all patterns.
# Put explicit path routes first so they win over router detail routes like
# /user-types/<pk>/ and /main-screens/<pk>/, which would otherwise capture
# "create" or "list" as a pk and return 405/404 responses.
urlpatterns = (
    user_patterns +
    user_screen_patterns +
    user_type_patterns +
    screen_patterns +
    permission_patterns +
    [path('', include(router.urls))]
)
