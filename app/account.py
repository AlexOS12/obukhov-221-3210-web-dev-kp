from flask import render_template, redirect, render_template, Blueprint, current_app, request, url_for
from flask_login import login_required
from app import db_connector

bp = Blueprint('account', __name__, url_prefix='/account')

@bp.route('/')
def index():
    return render_template("account.html")