from flask import render_template, redirect, render_template, Blueprint, current_app, request, url_for, flash
from flask_login import login_required, current_user
from mysql.connector.errors import DatabaseError
from app import db_connector

bp = Blueprint('tickets', __name__, url_prefix='/tickets')

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

@bp.route('/buy/<int:trip_no>', methods=["GET", "POST"])
def buy_ticket(trip_no):
    if request.method == "POST":
        try:
            ticket_params = {
                "owner_id" : int(current_user.id),
                "trip_id" : int(trip_no),
                "amount" : int(request.form.get("amount"))
            }

            with db_connector.connect().cursor() as cursor:
                cursor.execute("SELECT price_per_person * %s FROM trips where id = %s", (ticket_params["amount"], trip_no))
                ticket_params["total_price"] = int(cursor.fetchone()[0])
                print(ticket_params)
                cursor.execute(INSERT_TICKET_QUERY, ticket_params)
                db_connector.connect().commit()

            flash("Билет был успешно приобретён!", category="success")
            return redirect(url_for("account.index"))
        except DatabaseError as e:
            db_connector.connect().rollback()
            print(e)

    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(TRIP_SEARCH_QUERY, (trip_no, ))
        trip = cursor.fetchone()  

    return render_template("buy_ticket.html", trip=trip)