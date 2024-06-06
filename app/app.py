from flask import Flask, render_template
from flask_login import login_required, current_user

app = Flask(__name__)
application = app
app.config.from_pyfile("config.py")

from authorization import bp as authorization_bp, init_login_manager
app.register_blueprint(authorization_bp)
init_login_manager(app)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/schedule')
def schedule():
    return render_template("schedule.html")

@app.route('/tickets')
@login_required
def tickets():
    return render_template("tickets.html")