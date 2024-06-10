from flask import render_template, redirect, render_template, Blueprint, current_app, request, url_for, flash, send_file
from flask_login import login_required, current_user
from mysql.connector.errors import DatabaseError
from app import db_connector
from io import BytesIO
import pdfkit

bp = Blueprint('tickets', __name__, url_prefix='/tickets')

pdfkit_config = pdfkit.configuration(
    wkhtmltopdf=r'/usr/local/bin/wkhtmltopdf')

TRIP_SEARCH_QUERY = (
    "SELECT trips.id as 'trip_no', trips.arrive_time as 'arr_time', trips.depart_time as 'dep_time', "
    "trips.price_per_person as 'price', "
    "depart_station.name as 'dep_station', depart_city.name as 'dep_city', "
    "arrive_station.name as 'arr_station', arrive_city.name as 'arr_city' "
    "FROM trips join routes on trips.route_id = routes.id "
    "JOIN stations as depart_station on depart_station.id = routes.depart_station_id "
    "JOIN cities as depart_city on depart_station.city_id = depart_city.id "
    "JOIN stations as arrive_station on arrive_station.id = routes.arrive_station_id "
    "JOIN cities as arrive_city on arrive_station.city_id = arrive_city.id "
    "WHERE trips.id = %s"
)

INSERT_TICKET_QUERY = (
    "INSERT INTO tickets (owner_id, trip_id, amount, total_price) "
    "VALUES (%(owner_id)s, %(trip_id)s, %(amount)s, %(total_price)s)"
)

TICKET_INFO_QUERY = (
    "SELECT tickets.id as 'ticket_no', tickets.owner_id as 'owner_id', tickets.amount as 'amount', tickets.total_price as 'price', "
    # "SELECT tickets.id as 'ticket_no', tickets.amount as 'amount', tickets.total_price as 'price', "
    "trips.depart_time as 'dep_time', trips.arrive_time as 'arr_time', TIMEDIFF(trips.arrive_time, trips.depart_time) as 'travel_time', "
    "depart_station.name as 'dep_station_name', depart_city.name as 'dep_city_name', "
    "arrive_station.name as 'arr_station_name', arrive_city.name as 'arr_city_name', "
    "trips.id as 'trip_no', users.passport as 'passport', "
    "CONCAT(users.last_name, ' ', users.first_name, ' ', users.mid_name) as 'fio' "
    "FROM tickets join trips on tickets.trip_id = trips.id "
    "JOIN routes on trips.route_id = routes.id "
    "JOIN stations as depart_station on depart_station.id = routes.depart_station_id "
    "JOIN stations as arrive_station on arrive_station.id = routes.arrive_station_id "
    "JOIN cities as depart_city on depart_city.id = depart_station.city_id "
    "JOIN cities as arrive_city on arrive_city.id = arrive_station.city_id "
    "JOIN users on users.id = tickets.owner_id "
    "WHERE tickets.id = %s"
)

CHECK_TICKET_OWNER_QUERY = (
    "SELECT %(user_id)s = owner_id FROM tickets "
    "WHERE id = %(ticket_no)s "
)

UPDATE_TICKET_QUERY = (
    "UPDATE tickets set amount = %(amount)s "
    "WHERE id = %(ticket_no)s "
)

DELETE_TICKET_QUERY = (
    "DELETE FROM tickets WHERE id = %s "
)


@bp.route('/edit/<int:ticket_no>', methods=["GET", "POST"])
@login_required
def edit_ticket(ticket_no):
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(TICKET_INFO_QUERY, (ticket_no, ))
        ticket = cursor.fetchone()

    with db_connector.connect().cursor() as cursor:
        cursor.execute(CHECK_TICKET_OWNER_QUERY, {
            "user_id": current_user.id,
            "ticket_no": ticket_no
        })
        result = cursor.fetchone()[0]
        if not result:
            flash("Вы не можете изменить этот билет, поскольку не являетесь его владельцем",
                  category="warning")
            return redirect(url_for("account.tickets"))

    if request.method == "POST":
        try:
            with db_connector.connect().cursor() as cursor:
                cursor.execute(UPDATE_TICKET_QUERY, {
                    "ticket_no": ticket_no,
                    "amount": request.form.get("amount")
                })
            db_connector.connect().commit()
            flash("Билет был успешно изменён", category="success")
            return redirect(url_for("account.tickets"))
        except DatabaseError as error:
            db_connector.connect().rollback()
            flash(error, category="danger")
            flash("Во время изменения билета произошла ошибка", category="danger")

    return render_template("edit_ticket.html", ticket=ticket)


@bp.route('delete/<int:ticket_no>', methods=["POST"])
@login_required
def delete_ticket(ticket_no):
    with db_connector.connect().cursor() as cursor:
        cursor.execute(CHECK_TICKET_OWNER_QUERY, {
            "user_id": current_user.id,
            "ticket_no": ticket_no
        })
        result = cursor.fetchone()[0]

    if not result:
        flash("Вы не можете удалить этот билет, поскольку не являетесь его владельцем",
              category="warning")
        return redirect(url_for("account.tickets"))

    try:
        with db_connector.connect().cursor() as cursor:
            cursor.execute(DELETE_TICKET_QUERY, (ticket_no, ))
        db_connector.connect().commit()
        flash("Билет был успешно удалён", category="success")
        return redirect(url_for("account.tickets"))
    except DatabaseError as error:
        db_connector.connect().rollback()
        flash(error, category="danger")
        flash("Во время удаления билета произошла ошибка", category="danger")
        return redirect(url_for("account.tickets"))


@bp.route('/buy/<int:trip_no>', methods=["GET", "POST"])
@login_required
def buy_ticket(trip_no):
    if request.method == "POST":
        try:
            ticket_params = {
                "owner_id": int(current_user.id),
                "trip_id": int(trip_no),
                "amount": int(request.form.get("amount"))
            }

            with db_connector.connect().cursor() as cursor:
                cursor.execute(
                    "SELECT price_per_person * %s FROM trips where id = %s", (ticket_params["amount"], trip_no))
                ticket_params["total_price"] = int(cursor.fetchone()[0])
                print(ticket_params)
                cursor.execute(INSERT_TICKET_QUERY, ticket_params)
                db_connector.connect().commit()

            flash("Билет был успешно приобретён!", category="success")
            return redirect(url_for("account.tickets"))
        except DatabaseError as e:
            db_connector.connect().rollback()
            print(e)

    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(TRIP_SEARCH_QUERY, (trip_no, ))
        trip = cursor.fetchone()

    return render_template("buy_ticket.html", trip=trip)


def html_to_pdf(html):
    # pdf = bytes()
    options = {
        'page-size': 'A5',
        'margin-top': '0.25in',
        'margin-right': '0.25in',
        'margin-bottom': '0.25in',
        'margin-left': '0.25in',
        'encoding': "UTF-8",
        'no-outline': None
    }
    pdf = pdfkit.from_string(
        html, configuration=pdfkit_config, options=options)
    return pdf


@bp.route('/dowload/<int:ticket_no>')
@login_required
def download_ticket(ticket_no):
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(TICKET_INFO_QUERY, (ticket_no, ))
        ticket = cursor.fetchone()

    print(ticket)
    if not ticket:
        flash(f"Билет №{ticket_no} не был найден", category="warning")
        return redirect(url_for("account.tickets"))
    if str(ticket.owner_id) != current_user.id:
        flash(f"Вы не можете скачать этот билет, поскольку не являетесь его владельцем",
              category="warning")
        return redirect(url_for("account.tickets"))

    html_ticket = render_template("ticket_pdf.html", ticket=ticket)
    file = BytesIO()

    pdf_ticket = html_to_pdf(html_ticket)

    file.write(pdf_ticket)
    file.seek(0)

    return send_file(file, mimetype='application/pdf', as_attachment=True, download_name=f"Билет №{ticket_no}.pdf")
    # return html_ticket
