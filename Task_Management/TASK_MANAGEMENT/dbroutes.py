class AuthRouter:
    """
    Route shared auth/master apps to masters database.
    """

    route_app_labels = {
        'auth',
        'contenttypes',
        'sessions',
        'admin',
        'authtoken',
        'common_master',
        'login_home',
    }

    def db_for_read(self, model, **hints):

        if model._meta.app_label in self.route_app_labels:
            return 'masters_db'

        return 'task_management_db'

    def db_for_write(self, model, **hints):

        if model._meta.app_label in self.route_app_labels:
            return 'masters_db'

        return 'task_management_db'

    def allow_relation(self, obj1, obj2, **hints):

        if (
            obj1._state.db in {'masters_db', 'task_management_db'}
            and
            obj2._state.db in {'masters_db', 'task_management_db'}
        ):
            return True

        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):

        if app_label in self.route_app_labels:
            return db == 'masters_db'

        if db == 'masters_db':
            return False

        return db == 'task_management_db'