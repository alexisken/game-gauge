import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp

from helpers import apology, lookup, usd

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

# Custom filter
app.jinja_env.filters["usd"] = usd

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

    # Create dictionary of all data we'll need to serve to app
    game_data = []

    for game in game_list:

        #Get progress for each game in list
        copmletion =
        stock_price = (lookup(stock['symbol']))['price']
        stock_prices[stock['symbol']] = stock_price
        total_cash = total_cash + stock_price*stock['shares']

    # Example stock_prices format
    # {'ddog': 106.89, 'fb': 264.65}

    return render_template("index.html", stock_log=stock_log, stock_prices=stock_prices, user_cash=user_cash, total_cash=total_cash)


@app.route("/buy", methods=["GET", "POST"])
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Grab user inputs for repeated use
        symbol = request.form.get("symbol").upper()
        shares = int(request.form.get("shares"))

        # Ensure ticker was submitted
        if not symbol:
            return apology("must provide a stock symbol", 403)

        # Ensure # of shares was submitted
        if not shares:
            return apology("must provide desired # of shares", 403)

        # Ensure the stock can be found
        if lookup(symbol) == None:
            return apology("stock could not be found", 403)


        # Make API call for stock
        stock_info = lookup(symbol)
        price = float(stock_info["price"])

        # Calc cost of desired shares
        req_cash = price * shares

        # Check if user has sufficient funds
        cash = db.execute("SELECT cash FROM users WHERE id = :user_id",
                          user_id=session["user_id"])

        cash = cash[0]["cash"]

        if cash < req_cash:
            return apology("You can't afford to purchase that many shares")
        else:
            new_cash = cash - req_cash

            # Write new transaction to DB
            db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES(:user_id, :symbol, :shares, :price)",
                user_id=session["user_id"],
                symbol=symbol,
                shares=shares,
                price=price)

            # Check is user already owns shares of this stock
            shares_owned = db.execute("SELECT * FROM stocks WHERE user_id = :user_id AND symbol = :symbol",
                user_id=session["user_id"], symbol=symbol)

            # If no entry, insert new row into DB
            if not shares_owned:
                db.execute("INSERT INTO stocks (user_id, symbol, shares) VALUES(:user_id, :symbol, :shares)",
                user_id=session["user_id"],
                symbol=symbol,
                shares=shares)

            else:
                db.execute("UPDATE stocks SET shares = shares + :shares WHERE user_id = :user_id AND symbol = :symbol",
                    shares=shares, user_id=session["user_id"], symbol=symbol)

            # Update cash value for user in DB
            db.execute("UPDATE users SET cash = :new_cash WHERE id = :user_id",
                new_cash=new_cash, user_id=session["user_id"])

        return redirect("/")

    # User reached route via GET (as buy URL or redirect)
    return render_template("buy.html")


@app.route("/history")
def history():
    """Show history of transactions"""
    user_id = session['user_id']

    transactions = db.execute("SELECT * FROM transactions WHERE user_id=:user_id", user_id=user_id)

    return render_template("history.html", transactions=transactions)


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a lookup form)
    if request.method == "POST":

        # Make API lookup for submitted ticker
        quote_info = lookup(request.form.get("symbol"))

        # Handle failures to return a stock
        if quote_info == None:
            return apology("Could not find matching stock for that symbol", 400)

        # Otherwise return the template with stock info
        return render_template("quoted.html", quote_info=quote_info)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # Load the shares that a user owns
    user_id = session['user_id']

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Grab user inputs for repeated use
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Ensure ticker was submitted
        if not symbol:
            return apology("must choose a stock to sell", 403)

        # Ensure # of shares was submitted
        if not shares:
            return apology("must provide desired # of shares", 403)

        shares = int(shares)

        # Ensure the stock can be found
        if shares <= 0:
            return apology("must provide a valid # of shares", 403)

        # Check if user has sufficient funds
        shares_owned = db.execute("SELECT shares FROM stocks WHERE user_id = :user_id and symbol = :symbol ",
                          user_id=user_id, symbol=symbol)

        shares_owned = shares_owned[0]['shares']

        if shares > shares_owned:
            return apology("you don't own enough shares", 403)

        cash = (db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=user_id))[0]['cash']

        stock_price = lookup(symbol)['price']

        selling_value = stock_price*shares

        new_cash = cash + selling_value

        # Write new transaction to DB
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES(:user_id, :symbol, :shares, :price)",
            user_id=user_id,
            symbol=symbol,
            shares=shares,
            price=stock_price)

        # Report new shares to DB
        new_shares = shares_owned - shares

        db.execute("UPDATE stocks SET shares = :shares WHERE user_id = :user_id AND symbol = :symbol",
            shares=new_shares, user_id=user_id, symbol=symbol)

        # Update cash value for user in DB
        db.execute("UPDATE users SET cash = :cash WHERE id = :user_id",
            cash=new_cash, user_id=user_id)

        return redirect("/")


    # User reached route via GET (as buy URL or redirect)

    # Example response: [{'user_id': '3', 'symbol': 'DDOG', 'shares': 5}, {'user_id': '3', 'symbol': 'FB', 'shares': 2}]
    stocks = db.execute("SELECT * FROM stocks WHERE user_id = :user_id", user_id=user_id)

    return render_template("sell.html", stocks=stocks)



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
