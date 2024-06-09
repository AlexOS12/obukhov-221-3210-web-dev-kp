from flask import render_template, redirect, render_template, Blueprint, current_app, request, url_for, flash, send_file
from flask_login import login_required, current_user
from mysql.connector.errors import DatabaseError
from app import db_connector
from authorization import can_user

bp = Blueprint('admin', __name__, url_prefix='/admin')

USER_SEARCH_QUERY = (
    "SELECT users.id, users.login, CONCAT (users.last_name, ' ', users.first_name, ' ', users.mid_name) as fio, "
    "roles.name as role_name "
    "FROM users join roles on users.role_id = roles.id "
    "ORDER by id "
)

USER_INFO_QUERY = (
    "SELECT id, role_id, login, pass_hash, last_name, first_name, mid_name, passport "
    "FROM users WHERE id = %s"
)

UPDATE_USER_INFO_QUERY = (
    "UPDATE users "
    "SET role_id = %(role)s, login = %(login)s, last_name = %(last_name)s, first_name = %(first_name)s, "
    "mid_name = %(mid_name)s, passport = %(passport)s"
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

GET_TRIPS_QUERY = (
    "SELECT trips.id as trip_id, trips.route_id as route_id, "
    "depart_city.name as dep_city_name, arrive_city.name as arr_city_name, "
    "depart_station.id as dep_station_id, depart_station.name as dep_station_name, "
    "arrive_station.id as arr_station_id, arrive_station.name as arr_station_name, "
    "trips.depart_time as dep_time, trips.arrive_time as arr_time, "
    "trips.price_per_person as price_per_person, trips.available_places "
    "FROM trips join routes on trips.route_id = routes.id "
    "JOIN stations as depart_station on depart_station.id = routes.depart_station_id "
    "JOIN stations as arrive_station on arrive_station.id = routes.arrive_station_id "
    "JOIN cities as depart_city on depart_city.id = depart_station.city_id "
    "JOIN cities as arrive_city on arrive_city.id = arrive_station.city_id "
)

GET_TRIP_INFO = (
    "SELECT id, route_id, TIME_FORMAT(depart_time, '%H:%i') as dep_time, "
    "TIME_FORMAT(arrive_time, '%H:%i') as arr_time, price_per_person, available_places "
    "FROM trips "
    "WHERE id = %s "
)

UPDATE_TRIP_QUERY = (
    "UPDATE trips set route_id = %(route_id)s, depart_time = %(dep_time)s, "
    "arrive_time = %(arr_time)s, available_places = %(available_places)s, "
    "price_per_person = %(price_per_person)s "
    "WHERE id = %(trip_id)s"
)

UPDATE_TRIP_FIELDS = (
    "route_id", "dep_time", "arr_time", "available_places", "price_per_person"
)

DELETE_TRIP_QUERY = (
    "DELETE FROM trips WHERE id = %s "
)

CREATE_TRIP_QUERY = (
    "INSERT INTO trips "
    "(route_id, arrive_time, depart_time, available_places, price_per_person) "
    "VALUES (%(route_id)s, %(arr_time)s, %(dep_time)s, %(available_places)s, %(price_per_person)s) "
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
@can_user('see_admin_panel')
def index():
    return redirect(url_for('admin.users'))


@bp.route('/user/<int:user_id>/edit', methods=["GET", "POST"])
@login_required
@can_user('edit_users')
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
@can_user('view_users')
def view_user(user_id):
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(USER_INFO_QUERY, (user_id, ))
        user = cursor.fetchone()

    roles = get_roles()

    return render_template("view_user.html", user=user, roles=roles)


@bp.route('/user/<int:user_id>/delete', methods=["POST"])
@can_user('delete_users')
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
@can_user('create_users')
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
@can_user('see_admin_panel')
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
@can_user('see_admin_panel')
def routes():
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(GET_ROUTES_QUERY)
        routes = cursor.fetchall()

    return render_template("admin_routes.html", routes=routes)


@bp.route('/route/<int:route_id>/view')
@can_user('view_routes')
def view_route(route_id):
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(GET_ROUTE_INFO_QUERY, (route_id, ))
        route = cursor.fetchone()
    stations_and_cities = get_stations_and_cities()

    return render_template("view_route.html", route=route, stations_and_cities=stations_and_cities)


@bp.route('/route/<int:route_id>/edit', methods=["GET", "POST"])
@can_user('edit_routes')
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
@can_user('delete_routes')
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
@can_user('create_routes')
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
        flash("Во время создания маршрута произошла ошибка", category="danger")
        return render_template("create_route.html", stations_and_cities=stations_and_cities)


@bp.route('/trips')
@login_required
@can_user('see_admin_panel')
def trips():
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(GET_TRIPS_QUERY)
        trips = cursor.fetchall()
    return render_template("admin_trips.html", trips=trips)

@bp.route('/trip/<int:trip_id>/view')
@can_user('view_trips')
def view_trip(trip_id):
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(GET_TRIP_INFO, (trip_id, ))
        trip = cursor.fetchone()
        cursor.execute(GET_ROUTES_QUERY)
        routes = cursor.fetchall()

    return render_template("view_trip.html", trip=trip, routes=routes)

@bp.route('/trip/<int:trip_id>/edit', methods=["GET", "POST"])
@can_user('edit_trips')
def edit_trip(trip_id):
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(GET_TRIP_INFO, (trip_id, ))
        trip = cursor.fetchone()
        cursor.execute(GET_ROUTES_QUERY)
        routes = cursor.fetchall()

    if request.method == "GET":
        return render_template("edit_trip.html", trip=trip, routes=routes)
    
    fields = get_form_fields(request.form, UPDATE_TRIP_FIELDS)
    fields["trip_id"] = trip_id

    try:
        with db_connector.connect().cursor() as cursor:
            cursor.execute(UPDATE_TRIP_QUERY, fields)
        db_connector.connect().commit()
        flash("Рейс был успешно обновлён", category="success")
        return redirect(url_for("admin.trips"))
    except DatabaseError as error:
        db_connector.connect().rollback()
        flash(error, category="danger")
        flash("Произошла ошибка во время изменения рейса", category="danger")
    return render_template("edit_trip.html", trip=trip, routes=routes)

@bp.route('/trip/<int:trip_id>/delete', methods=["POST"])
@can_user('delete_trips')
def delete_trip(trip_id):
    try:
        with db_connector.connect().cursor() as cursor:
            cursor.execute(DELETE_TRIP_QUERY, (trip_id, ))
        print(request.url)  
        db_connector.connect().commit()
        flash("Маршрут был успешно удалён", category="success")
    except DatabaseError as error:
        db_connector.connect().rollback()
        flash(error, category="danger")
        flash("Во время удаления рейса произошла ошибка", category="danger")
    return redirect(url_for("admin.trips"))

@bp.route('trips/create', methods=["GET", "POST"])
@can_user('create_trips')
def create_trip():
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(GET_ROUTES_QUERY)
        routes = cursor.fetchall()

    if request.method == "GET":
        return render_template("edit_trip.html", trip={}, routes=routes)
    
    fields = get_form_fields(request.form, UPDATE_TRIP_FIELDS)

    try:
        with db_connector.connect().cursor() as cursor:
            cursor.execute(CREATE_TRIP_QUERY, fields)
        db_connector.connect().commit()
        flash("Рейс был успешно создан", category="success")
        return redirect(url_for("admin.trips"))
    except DatabaseError as error:
        db_connector.connect().rollback()
        flash(error, category="danger")
        flash("Произошла ошибка во время создания рейса", category="danger")
    return render_template("create_trip.html", trip=fields, routes=routes)
