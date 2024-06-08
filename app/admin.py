from flask import render_template, redirect, render_template, Blueprint, current_app, request, url_for, flash, send_file
from flask_login import login_required, current_user
from mysql.connector.errors import DatabaseError
from app import db_connector

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/')
def index():
    return redirect(url_for('admin.users'))

@bp.route('/users')
def users():
    return render_template("admin_users.html")

@bp.route('/tickets')
def tickets():
    return render_template("admin_tickets.html")

@bp.route('/routes')
def routes():
    return render_template("admin_routes.html")

@bp.route('/trips')
def trips():
    return render_template("admin_trips.html")