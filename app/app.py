from flask import Flask, render_template

app = Flask(__name__)
#app.config.from_pyfile("config.py")

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
def tickets():
    return render_template("tickets.html")