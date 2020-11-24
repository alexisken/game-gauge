import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from helpers import apology
import time

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///games.db")

@app.route("/")
def index():
    """Show game records & progress"""

    # Grab games
    game_list = db.execute("SELECT * FROM games")

    # Example output:
    # [{
        # 'game_id': 1,
        # 'game_title': 'The Last of Us',
        # 'release_date': '2013-06-14',
        # 'playtime': '16:20:00',
        # 'complete': 'Y'
    # }]

    game_list_sorted = sorted(game_list, key = lambda i: (i['complete'], i['game_title']))


    return render_template("index.html", game_list=game_list_sorted)


@app.route("/input", methods=["GET", "POST"])
def input():
    """Input games not yet in the system"""

    # For when user submits the listed form
    if request.method == "POST":

        # Grab user inputs for repeated use
        game = request.form.get("Game")
        publisher = request.form.get("Publisher")
        developer = request.form.get("Developer")
        platform = request.form.get("Platform")
        completion = request.form.get("Completion")
        release = request.form.get("Release-date")
        minutes = int(request.form.get("Minutes"))
        hours = int(request.form.get("Hours"))
        seconds = 0

        if minutes:
            seconds = seconds + (minutes * 60)
        if hours:
            seconds = seconds + (hours * 60 * 60)

        playtime = time.strftime('%H:%M:%S', time.gmtime(seconds))

        if not game:
            return apology("please enter a game name", 403)


            # Write new transaction to DB
            db.execute("INSERT INTO games (game_title, release_date, playtime, complete, platform, publisher, developer) VALUES(:game, :release, :playtime, :completion, :platform, :publisher, :developer)",
                game = game,
                release = release,
                playtime = playtime,
                completion = completion,
                platform = platform,
                publisher = publisher,
                developer = developer)

        return redirect("/")

    # When user reaches the page via URL / nav bar
    return render_template("input.html")


@app.route("/manage")
def manage():
    """Manage games & progress previously input into system"""

    return render_template("manage.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
