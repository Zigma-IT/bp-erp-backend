"""
Reusable permission decorator for DRF api_view functions.

Usage:
    @api_view(['GET'])
    @require_permission('rate-order', 'can_list')
    def my_view(request):
        ...

The folder_name must match UserScreen.folder_name in the database.
If the logged-in user has no UserCreation record (super admin), access is granted.
"""

from functools import wraps

from rest_framework.response import Response


def require_permission(folder_name: str, action: str = 'can_view'):
    """
    Check that the logged-in user's UserType has the given action on folder_name.
    Grants full access when the user has no UserCreation entry (Django superuser).
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            from admin_master.models import UserCreation, UserScreen, UserTypePermission

            if not request.user.is_authenticated:
                return Response({"error": "Authentication required."}, status=401)

            try:
                user_creation = UserCreation.objects.select_related('user_type').get(
                    username=request.user.username
                )
            except UserCreation.DoesNotExist:
                return view_func(request, *args, **kwargs)

            if not user_creation.user_type:
                return view_func(request, *args, **kwargs)

            try:
                user_screen = UserScreen.objects.get(folder_name=folder_name, is_active=True)
            except UserScreen.DoesNotExist:
                return Response({"error": "Screen not configured."}, status=404)

            try:
                perm = UserTypePermission.objects.get(
                    user_type=user_creation.user_type,
                    user_screen=user_screen,
                    status=True,
                )
            except UserTypePermission.DoesNotExist:
                return Response({"error": "Permission denied."}, status=403)

            if not getattr(perm, action, False):
                return Response(
                    {"error": f"You don't have '{action}' permission for this screen."},
                    status=403,
                )

            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
