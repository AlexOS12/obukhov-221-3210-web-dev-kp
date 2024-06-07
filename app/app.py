from flask import Flask, render_template, request
from flask_login import login_required, current_user
from mysqldb import DBConnector
from mysql.connector.errors import DatabaseError

app = Flask(__name__)
application = app
app.config.from_pyfile("config.py")

db_connector = DBConnector(app)

TRIP_SEARCH_FIELDS = [
    "depart_city", "arrive_city",
    "depart_time_from", "depart_time_to",
    "arrive_time_from", "arrive_time_to",
    "travel_time_from", "travel_time_to"
]

#ВАЖНО!!! У КАЖДОГО ПОЛЯ ДОЛЖНО БЫТЬ УНИКАЛЬНОЕ ИМЯ!!!
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
    "WHERE depart_city.name = %(depart_city)s and arrive_city.name = %(arrive_city)s "
    "and trips.depart_time > %(depart_time_from)s and trips.depart_time < %(depart_time_to)s "
    # "and trips.arrive_time > '16:00:00' and trips.arrive_time < '18:00:00' "
)

from authorization import bp as authorization_bp, init_login_manager
app.register_blueprint(authorization_bp)
init_login_manager(app)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

def get_trip_params(form):
    trip_params = {}

    for param in TRIP_SEARCH_FIELDS:
            trip_params[param] = request.form.get(param) or None

    if not trip_params["depart_time_from"]:
        trip_params["depart_time_from"] = "00:00"
    if not trip_params["depart_time_to"]:
        trip_params["depart_time_to"] = "23:59"
    if not trip_params["arrive_time_from"]:
        trip_params["arrive_time_from"] = "00:00"
    if not trip_params["arrive_time_to"]:
        trip_params["arrive_time_to"] = "23:59"
    if not trip_params["travel_time_from"]:
        trip_params["travel_time_from"] = "00:00"
    if not trip_params["travel_time_to"]:
        trip_params["travel_time_to"] = "23:59"

    return trip_params


@app.route('/schedule', methods=["GET", "POST"])
def schedule():
    trips = {}
    if request.method == "POST":
        trip_params = get_trip_params(request.form)

        print(trip_params)

        with db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute(TRIP_SEARCH_QUERY, trip_params)
            trips = cursor.fetchall()

        print(cursor.statement)

    return render_template("schedule.html", form=request.form, trips=trips, post=request.method=="POST")


@app.route('/tickets')
@login_required
def tickets():
    return render_template("tickets.html")