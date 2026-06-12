"""Django app configuration for procurement transaction entry screens."""

from django.apps import AppConfig


class PurchaseEntrysConfig(AppConfig):
    name = 'purchase_entrys'

    def ready(self):
        """Sync auth users and tokens to procurement_db when the app starts."""
        self.sync_auth_data_to_procurement_db()

    @staticmethod
    def sync_auth_data_to_procurement_db():
        """
        Sync auth users and tokens from masters_db to procurement_db.
        
        This resolves foreign key constraint issues in approval workflows.
        """
        from django.db import connections
        
        try:
            # Sync auth users
            with connections['masters_db1'].cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email, password, is_staff, is_superuser, is_active, date_joined FROM auth_user"
                )
                users_data = cursor.fetchall()
            
            if users_data:
                with connections['procurement_db'].cursor() as cursor:
                    for user_data in users_data:
                        user_id, username, email, password, is_staff, is_superuser, is_active, date_joined = user_data
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
            
            # Sync auth tokens
            with connections['masters_db1'].cursor() as cursor:
                cursor.execute("SELECT key, user_id, created FROM authtoken_token")
                tokens_data = cursor.fetchall()
            
            if tokens_data:
                with connections['procurement_db'].cursor() as cursor:
                    for token_data in tokens_data:
                        key, user_id, created = token_data
                        cursor.execute(
                            """INSERT INTO authtoken_token (key, user_id, created)
                               VALUES (%s, %s, %s)
                               ON DUPLICATE KEY UPDATE user_id = VALUES(user_id)
                            """,
                            (key, user_id, created)
                        )
                    connections['procurement_db'].commit()
        except Exception as e:
            # Silently fail on startup
            pass
