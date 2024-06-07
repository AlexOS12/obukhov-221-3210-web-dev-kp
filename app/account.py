from flask import render_template, redirect, render_template, Blueprint, current_app, request, url_for
from flask_login import login_required
from app import db_connector

bp = Blueprint('account', __name__, url_prefix='/account')

TICKET_SEARCH_QUERY = (
    "SELECT trips.id as 'trip_no', tickets.total_price as 'price', "
    "trips.depart_time as 'dep_time', trips.arrive_time as 'arr_time', "
    "TIMEDIFF(trips.arrive_time, trips.depart_time) as 'travel_time', "
    "tickets.amount as 'amount', depart_city.name as 'dep_city', arrive_city.name as 'arr_city' "
    "FROM tickets JOIN trips on trips.id = tickets.trip_id "
    "JOIN routes on routes.id = trips.route_id "
    "JOIN stations as depart_station on depart_station.id = routes.depart_station_id "
    "JOIN stations as arrive_station on arrive_station.id = routes.arrive_station_id "
    "JOIN cities as depart_city on depart_city.id = depart_station.city_id "
    "JOIN cities as arrive_city on arrive_city.id = arrive_station.city_id "
    "WHERE tickets.owner_id = 2 "
)

@bp.route('/')
@login_required
def index():
    tickets = ()
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(TICKET_SEARCH_QUERY)
        tickets = cursor.fetchall()
        print(tickets)

    return render_template("account.html", tickets=tickets)