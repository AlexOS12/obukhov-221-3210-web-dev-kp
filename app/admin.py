from flask import render_template, redirect, render_template, Blueprint, current_app, request, url_for, flash, send_file
from flask_login import login_required, current_user
from mysql.connector.errors import DatabaseError
from app import db_connector

bp = Blueprint('admin', __name__, url_prefix='/admin')

USER_SEARCH_QUERY = (
    "SELECT users.id, users.login, CONCAT (users.last_name, ' ', users.first_name, ' ', users.mid_name) as fio, "
    "roles.name as role_name "
    "FROM users join roles on users.role_id = roles.id"
)

USER_INFO_QUERY = (
    "SELECT id, role_id, login, pass_hash, last_name, first_name, mid_name, passport "
    "FROM users WHERE id = %s"
)

UPDATE_USER_INFO_QUERY = (
    "UPDATE users "
    "SET role_id = %(role)s, login = %(login)s, last_name = %(last_name)s, first_name = %(first_name)s, "
    "mid_name = %(mid_name)s "
    "WHERE users.id = %(user_id)s"
)

CREATE_USER_QUERY = (
    "INSERT INTO users "
    "(role_id, login, pass_hash, last_name, first_name, mid_name, passport) "
    "VALUES (%(role)s, %(login)s, SHA2(%(password)s, 256), %(last_name)s, %(first_name)s, "
    "%(mid_name)s, %(passport)s) "
)

UPDATE_USER_FIELDS = (
    "login", "last_name", "first_name", "mid_name", "role", "passport"
)

CREATE_USER_FIELDS = (
    "login", "password", "last_name", "first_name", "mid_name", "role", "passport"
)

DELETE_USER_QUERY = (
    "DELETE FROM users WHERE id = %s "
)

GET_ROLES_QUERY = (
    "SELECT id, name FROM roles "
)


def get_roles():
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(GET_ROLES_QUERY)
        return cursor.fetchall()


def get_form_fields(form, required_fields):
    fields = {}

    for field in required_fields:
        fields[field] = form.get(field, None)

    return fields


@bp.route('/')
@login_required
def index():
    return redirect(url_for('admin.users'))


@bp.route('/user/<int:user_id>/edit', methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(USER_INFO_QUERY, (user_id, ))
        user = cursor.fetchone()

    roles = get_roles()

    if request.method == "GET":
        return render_template("edit_user.html", user=user, roles=roles)

    form_fields = get_form_fields(request.form, UPDATE_USER_FIELDS)
    form_fields["user_id"] = user_id

    try:
        with db_connector.connect().cursor() as cursor:
            cursor.execute(UPDATE_USER_INFO_QUERY, form_fields)
            db_connector.connect().commit()
            flash("Данные пользователя были успешно обновлены", category="success")
            return redirect(url_for('admin.users'))
    except DatabaseError as error:
        db_connector.connect().rollback()
        flash(error, category="danger")
        flash("Произошла ошибка изменения данных пользователя", category="danger")
        return render_template("edit_user.html", user=user, roles=roles)


@bp.route('/user/<int:user_id>/view')
def view_user(user_id):
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(USER_INFO_QUERY, (user_id, ))
        user = cursor.fetchone()

    roles = get_roles()

    return render_template("view_user.html", user=user, roles=roles)


@bp.route('/user/<int:user_id>/delete', methods=["POST"])
def delete_user(user_id):
    try:
        with db_connector.connect().cursor() as cursor:
            cursor.execute(DELETE_USER_QUERY, (user_id, ))
            db_connector.connect().commit()
            flash("Пользователь был успешно удалён", category="success")
    except DatabaseError as error:
        db_connector.connect().rollback()
        flash("Произошла ошибка во время удаления пользователя", category="danger")
    return redirect(url_for("admin.users"))

@bp.route('/create_user', methods=["GET", "POST"])
def create_user():
    roles = get_roles()
    if request.method == "GET":
        return render_template("create_user.html", user={}, roles=roles)
    
    form_fields = get_form_fields(request.form, CREATE_USER_FIELDS)

    try:
        with db_connector.connect().cursor() as cursor:
            cursor.execute(CREATE_USER_QUERY, form_fields)
            db_connector.connect().commit()
        flash("Пользователь был успешно создан", category="success")
        return redirect(url_for("admin.users"))
    except DatabaseError as error:
        db_connector.connect().rollback()
        flash(error, category="danger")
        flash("Во время создания пользователя произошла ошибка", category="danger")
        return render_template("create_user.html", user=form_fields, roles=roles)
    

@bp.route('/users')
@login_required
def users():
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(USER_SEARCH_QUERY)
        users = cursor.fetchall()

    return render_template("admin_users.html", users=users)


@bp.route('/tickets')
@login_required
def tickets():
    return render_template("admin_tickets.html")


@bp.route('/routes')
@login_required
def routes():
    return render_template("admin_routes.html")


@bp.route('/trips')
@login_required
def trips():
    return render_template("admin_trips.html")
