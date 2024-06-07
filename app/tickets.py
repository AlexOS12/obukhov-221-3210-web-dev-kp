from flask import render_template, redirect, render_template, Blueprint, current_app, request, url_for
from flask_login import login_required
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

@bp.route('/buy/<int:trip_no>')
def buy_ticket(trip_no):
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(TRIP_SEARCH_QUERY, (trip_no, ))
        trip = cursor.fetchone()
    print(trip)
    return render_template("buy_ticket.html", trip=trip)