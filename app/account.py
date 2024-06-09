from flask import render_template, redirect, render_template, Blueprint, current_app, request, url_for, flash
from flask_login import login_required, current_user, login_user
from app import db_connector
from mysql.connector.errors import DatabaseError
from authorization import can_user, User
from admin import USER_INFO_QUERY, UPDATE_USER_INFO_QUERY, GET_ROLES_QUERY, get_roles, get_form_fields, UPDATE_USER_FIELDS, CREATE_USER_QUERY, DELETE_USER_QUERY

bp = Blueprint('account', __name__, url_prefix='/account')

TICKET_SEARCH_QUERY = (
    "SELECT tickets.id as 'ticket_no', trips.id as 'trip_no', tickets.total_price as 'price', "
    "trips.depart_time as 'dep_time', trips.arrive_time as 'arr_time', "
    "TIMEDIFF(trips.arrive_time, trips.depart_time) as 'travel_time', "
    "tickets.amount as 'amount', depart_city.name as 'dep_city', arrive_city.name as 'arr_city' "
    "FROM tickets JOIN trips on trips.id = tickets.trip_id "
    "JOIN routes on routes.id = trips.route_id "
    "JOIN stations as depart_station on depart_station.id = routes.depart_station_id "
    "JOIN stations as arrive_station on arrive_station.id = routes.arrive_station_id "
    "JOIN cities as depart_city on depart_city.id = depart_station.city_id "
    "JOIN cities as arrive_city on arrive_city.id = arrive_station.city_id "
    "WHERE tickets.owner_id = %s "
)

COMPARE_PASS_QUERY = (
    "SELECT pass_hash = SHA2(%(old_pass)s, 256) "
    "FROM users "
    "WHERE id = %(user_id)s"
)

CHANGE_PASS_QUERY = (
    "UPDATE `users` set pass_hash = SHA2(%(new_pass)s, 256) "
    "WHERE id = %(user_id)s "
)

CHANGE_PASS_FIELDS = (
    "old_pass", "new_pass", "new_pass_conf"
)

CREATE_USER_FIELDS = (
    "login", "password", "pass_conf", "last_name", "first_name", "mid_name", "role", "passport"
)

CHECK_IF_LOGIN_EXISTS_QUERY = (
    "SELECT COUNT(*) FROM users WHERE login = %s "
)

GET_USER_ID_QUERY = (
    "SELECT id FROM users WHERE login = %s "
)


@bp.route('/edit_self', methods=["POST"])
@login_required
@can_user('edit_self')
def edit_self():
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(USER_INFO_QUERY, (current_user.id, ))
        user = cursor.fetchone()

    roles = {}
    form_fields = get_form_fields(request.form, UPDATE_USER_FIELDS)

    print(form_fields)

    if current_user.can('assign_roles'):
        roles = get_roles()
    else:
        form_fields["role"] = current_user.role_id

    form_fields["user_id"] = current_user.id

    print(form_fields)

    try:
        with db_connector.connect().cursor() as cursor:
            cursor.execute(UPDATE_USER_INFO_QUERY, form_fields)
            db_connector.connect().commit()
            flash("Данные пользователя были успешно обновлены", category="success")
            return redirect(url_for('account.index'))
    except DatabaseError as error:
        db_connector.connect().rollback()
        flash(error, category="danger")
        flash("Произошла ошибка изменения данных пользователя", category="danger")
        return render_template("account.html", user=user, roles=roles)


@bp.route('change_pass', methods=["POST"])
@login_required
def change_pass():
    form_fields = get_form_fields(request.form, CHANGE_PASS_FIELDS)
    form_fields["user_id"] = current_user.id

    with db_connector.connect().cursor() as cursor:
        cursor.execute(COMPARE_PASS_QUERY, form_fields)
        old_pass_eq = cursor.fetchone()[0]

    if not old_pass_eq:
        flash("Неверно введен старый пароль!", category="warning")
    elif form_fields["new_pass"] != form_fields["new_pass_conf"]:
        flash("Новые пароли не совпадают!", category="warning")
    else:
        try:
            with db_connector.connect().cursor() as cursor:
                cursor.execute(CHANGE_PASS_QUERY, form_fields)
            db_connector.connect().commit()
            flash("Пароль был успешно изменён!", category="success")
        except DatabaseError:
            flash("Во время смены пароля произошла ошибка!", category="danger")

    return redirect(url_for("account.index"))


@bp.route('/create', methods=["GET", "POST"])
def create():
    if request.method == "POST":
        form_fields = get_form_fields(request.form, CREATE_USER_FIELDS)
        form_fields["role"] = 2

        with db_connector.connect().cursor() as cursor:
            cursor.execute(CHECK_IF_LOGIN_EXISTS_QUERY,
                           (form_fields["login"], ))
            login_exists = cursor.fetchone()[0]

        if login_exists:
            flash("Выбранный логин уже используется другим пользователем",
                  category="warning")
        elif form_fields["password"] != form_fields["pass_conf"]:
            flash("Пароли должны совпадать!", category="warning")
        else:
            try:
                with db_connector.connect().cursor() as cursor:
                    cursor.execute(CREATE_USER_QUERY, form_fields)
                db_connector.connect().commit()
                with db_connector.connect().cursor() as cursor:
                    cursor.execute(GET_USER_ID_QUERY, (form_fields["login"], ))
                    user_id = cursor.fetchone()[0]
                if user_id:
                    login_user(
                        User(user_id, form_fields["login"], form_fields["role"]))
                    return redirect(url_for('index'))
            except DatabaseError as error:
                db_connector.connect().rollback()
                flash(error, category="danger")
                flash("Не удалось создать учётную запись", category="danger")

    return render_template("account_create.html")


@bp.route('/delete_self', methods=["POST"])
@login_required
def delete_self():
    try:
        with db_connector.connect().cursor() as cursor:
            cursor.execute(DELETE_USER_QUERY, (current_user.id, ))
        db_connector.connect().commit()
        flash("Учётная запись была успешно удалена", category="success")
        return redirect(url_for("index"))
    except DatabaseError as error:
        flash(error, category="danger")
        flash("Во время удаления учётной записи произошла ошибка", category="danger")
        return redirect(url_for("account.index"))


@bp.route('/')
@login_required
def index():
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(USER_INFO_QUERY, (current_user.id, ))
        user = cursor.fetchone()
        cursor.execute(GET_ROLES_QUERY)
        roles = cursor.fetchall()
    return render_template("account.html", user=user, roles=roles)


@bp.route('/tickets')
@login_required
def tickets():
    tickets = ()
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(TICKET_SEARCH_QUERY, (current_user.id, ))
        tickets = cursor.fetchall()
        print(tickets)

    return render_template("account_tickets.html", tickets=tickets)
