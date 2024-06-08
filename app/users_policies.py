from flask_login import current_user


class UsersPolicy:
    def __init__(self, user=None):
        self.user = user

    def see_admin_panel(self):
        return current_user.is_admin()

    def assing_roles(self):
        return current_user.is_admin()

    def view_users(self):
        return current_user.is_admin()

    def edit_self(self):
        return True

    def edit_users(self):
        return current_user.is_admin()

    def create_users(self):
        return current_user.is_admin()

    def delete_users(self):
        return current_user.is_admin()

    def view_routes(self):
        return current_user.is_admin()

    def edit_routes(self):
        return current_user.is_admin()

    def create_routes(self):
        return current_user.is_admin()

    def delete_routes(self):
        return current_user.is_admin()

    def view_trips(self):
        return current_user.is_admin()

    def edit_trips(self):
        return current_user.is_admin()

    def create_trips(self):
        return current_user.is_admin()

    def delete_trips(self):
        return current_user.is_admin()
