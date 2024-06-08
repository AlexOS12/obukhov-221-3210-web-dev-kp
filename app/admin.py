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

GET_ROUTES_QUERY = (
    "SELECT routes.id as route_id, depart_city.name as dep_city_name, "
    "depart_station.name as dep_station_name, arrive_city.name as arr_city_name, "
    "arrive_station.name as arr_station_name "
    "FROM routes JOIN stations as depart_station on depart_station.id = routes.depart_station_id "
    "JOIN stations as arrive_station on arrive_station.id = routes.arrive_station_id "
    "JOIN cities as depart_city on depart_city.id = depart_station.city_id "
    "JOIN cities as arrive_city on arrive_city.id = arrive_station.city_id "
)

GET_STATION_CITIES_INFO = (
    "SELECT stations.id as station_id, stations.name as station_name, cities.name as city_name "
    "FROM stations "
    "JOIN cities on stations.city_id = cities.id "
    "ORDER BY station_id"
)

GET_ROUTE_INFO_QUERY = (
    "SELECT id, depart_station_id, arrive_station_id FROM routes "
    "WHERE id = %s"
)

UPDATE_ROUTE_QUERY = (
    "UPDATE routes "
    "SET depart_station_id = %(depart_station)s, arrive_station_id = %(arrive_station)s "
    "WHERE id = %(route_id)s"
)

UPDATE_ROUTE_FIELDS = (
    "depart_station", "arrive_station"
)

CREATE_ROUTE_QUERY = (
    "INSERT INTO routes (depart_station_id, arrive_station_id) "
    "VALUES (%(depart_station)s, %(arrive_station)s) "
)

DELETE_ROUTE_QUERY = (
    "DELETE FROM routes WHERE id = %s "
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
        flash("Во время создания пользователя произошла ошибка", category="danger")
        return render_template("create_user.html", user=form_fields, roles=roles)


@bp.route('/users')
@login_required
def users():
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(USER_SEARCH_QUERY)
        users = cursor.fetchall()

    return render_template("admin_users.html", users=users)


def get_stations_and_cities():
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(GET_STATION_CITIES_INFO)
        return cursor.fetchall()


@bp.route('/routes')
@login_required
def routes():
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(GET_ROUTES_QUERY)
        routes = cursor.fetchall()

    return render_template("admin_routes.html", routes=routes)


@bp.route('/route/<int:route_id>/view')
def view_route(route_id):
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(GET_ROUTE_INFO_QUERY, (route_id, ))
        route = cursor.fetchone()
    stations_and_cities = get_stations_and_cities()

    return render_template("view_route.html", route=route, stations_and_cities=stations_and_cities)


@bp.route('/route/<int:route_id>/edit', methods=["GET", "POST"])
def edit_route(route_id):
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(GET_ROUTE_INFO_QUERY, (route_id, ))
        route = cursor.fetchone()
    stations_and_cities = get_stations_and_cities()

    if request.method == "GET":
        return render_template("edit_route.html", route=route, stations_and_cities=stations_and_cities)

    fields = get_form_fields(request.form, UPDATE_ROUTE_FIELDS)
    fields["route_id"] = route_id

    try:
        with db_connector.connect().cursor() as cursor:
            cursor.execute(UPDATE_ROUTE_QUERY, fields)
        db_connector.connect().commit()
        flash("Маршрут был успешно обновлён", category="success")
        return redirect(url_for("admin.routes"))
    except DatabaseError as error:
        db_connector.connect().rollback()
        flash("Во время изменения маршрута произошла ошибка", category="danger")
        return render_template("edit_route.html", route=route, stations_and_cities=stations_and_cities)


@bp.route('/route/<int:route_id>/delete', methods=["POST"])
def delete_route(route_id):
    try:
        with db_connector.connect().cursor() as cursor:
            cursor.execute(DELETE_ROUTE_QUERY, (route_id, ))
        db_connector.connect().commit()
        flash("Маршрут был успешно удалён", category="success")
    except DatabaseError as error:
        db_connector.connect().rollback()
        flash("Произошла ошибка во время удаления маршрута", category="danger")

    return redirect(url_for("admin.routes"))


@bp.route('route/create', methods=["GET", "POST"])
def create_route():
    stations_and_cities = get_stations_and_cities()

    if request.method == "GET":
        return render_template("create_route.html", stations_and_cities=stations_and_cities)

    fields = get_form_fields(request.form, UPDATE_ROUTE_FIELDS)

    try:
        with db_connector.connect().cursor() as cursor:
            cursor.execute(CREATE_ROUTE_QUERY, fields)
        db_connector.connect().commit()
        flash("Маршрут был успешно создан", category="success")
        return redirect(url_for("admin.routes"))
    except DatabaseError as error:
        db_connector.connect().rollback()
        flash(error, category="danger")
        flash("Во время создания маршрута произошла ошибка", category="danger")
        return render_template("create_route.html", stations_and_cities=stations_and_cities)


@bp.route('/trips')
@login_required
def trips():
    return render_template("admin_trips.html")
