from flask import render_template, redirect, render_template, Blueprint, current_app, request, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

bp = Blueprint('auth', __name__, url_prefix='/auth')

class User(UserMixin):
    def __init__(self, user_id, login, role_id):
        self.id = user_id
        self.login = login
        self.role_id = role_id

    def is_admin(self):
        return self.role_id == current_app.config['ADMIN_ROLE_ID']
    
def init_login_manager(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Войдите, чтобы просматривать содержимое данной страницы"
    login_manager.login_message_category = "warning"
    login_manager.user_loader(load_user)

def load_user(user_id):
    return User(1, "test", 1)
    # query = "SELECT id, login, role_id FROM users WHERE id=%s"

    # with db_connector.connect().cursor(named_tuple=True) as cursor:

    #     cursor.execute(query, (user_id,))
        
    #     user = cursor.fetchone()

    # if user:
    #     return User(user_id, user.login, user.role_id)
    
    # return None

@bp.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("auth.html")
    
    login_user(User(1, "test", 1))
    target_page = request.args.get("next", url_for("index"))
    return redirect(target_page)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("index"))