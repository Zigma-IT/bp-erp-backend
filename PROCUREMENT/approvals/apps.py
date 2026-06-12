"""Django app configuration for approval workflows."""

from django.apps import AppConfig


class ApprovalsConfig(AppConfig):
    name = 'approvals'

    def ready(self):
        """Sync auth users to procurement_db when the app starts."""
        self.sync_auth_users_to_procurement_db()

    @staticmethod
    def sync_auth_users_to_procurement_db():
        """
        Sync auth users from masters_db to procurement_db.
        
        This resolves the foreign key constraint issue where approval workflows
        try to reference users that don't exist in the procurement_db.
        
        Background: The database router routes auth models to masters_db, but PRs
        are stored in procurement_db. When saving an approval with level2_approved_by,
        Django needs the referenced user to exist in the same database as the PR.
        """
        from django.db import connections
        
        try:
            # Get all users from masters_db
            with connections['masters_db1'].cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email, password, is_staff, is_superuser, is_active, date_joined FROM auth_user"
                )
                users_data = cursor.fetchall()
            
            if not users_data:
                return  # No users to sync
            
            # Sync users to procurement_db
            with connections['procurement_db'].cursor() as cursor:
                for user_data in users_data:
                    user_id, username, email, password, is_staff, is_superuser, is_active, date_joined = user_data
                    # Use INSERT... ON DUPLICATE KEY UPDATE to handle existing records
                    cursor.execute(
                        """INSERT INTO auth_user 
                           (id, username, email, password, is_staff, is_superuser, is_active, last_login, date_joined) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, NULL, %s)
                           ON DUPLICATE KEY UPDATE 
                           email = VALUES(email),
                           password = VALUES(password),
                           is_staff = VALUES(is_staff),
                           is_superuser = VALUES(is_superuser),
                           is_active = VALUES(is_active),
                           date_joined = VALUES(date_joined)
                        """,
                        (user_id, username, email, password, is_staff, is_superuser, is_active, date_joined)
                    )
                connections['procurement_db'].commit()
        except Exception as e:
            # Silently fail on startup - the app can still work if auth sync fails
            # (though approvals will still fail until auth users are synced)
            pass
