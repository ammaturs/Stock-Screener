import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    #gather up db data and store it in a dictionary, pass to index.html and display all that data as a table
    porty = [] #[{'symbol': 'AAPL', 'shares': 9, 'price': 173}, {'symbol': 'NFLX', 'shares': 10, 'price': 436}]
    symbol_list = db.execute("SELECT symbol FROM orders")  #[{'symbol': 'AAPL'}, {'symbol': 'NFLX'}]
    share_list = db.execute("SELECT shares FROM orders") #[{'shares': 9}, {'shares': 10}]

    current_share_price = [] #[{'symbol': 'AAPL', 'price': 173}, {'symbol': 'NFLX', 'price': 436}]

    for entry in symbol_list:
        current_share_price.append({"symbol":entry["symbol"], "price": (lookup(entry["symbol"]))["price"]})
        porty.append

    i=0
    while i<len(symbol_list):
        porty.append({"symbol": symbol_list[i]["symbol"], "shares":share_list[i]["shares"], "price": current_share_price[i]["price"]})
        i+=1
    for entry in porty:
        print(entry)

    return render_template("index.html", porty=porty)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol") #str
        shares = request.form.get("shares") #str
        cash = db.execute("SELECT cash FROM users WHERE id = ?", session.get("user_id"))
        cash_value = int(cash[0]["cash"])
        purchased = int(lookup(symbol)["price"]) * int(shares)


        #ensure symbol is a valid stock
        if lookup(symbol) == None:
            return apology("Incorrect symbol", 403)

        #ensure valid share amount
        elif int(shares)<=0:
            return apology("Incorrect share value", 403)

        #ensure user has enough cash for purchase
        elif (int(lookup(symbol)["price"]) * int(shares)) > cash_value:
            return apology("Not enough cash", 403)

        amount = (int(lookup(symbol)["price"]) * int(shares))

        #valid symbol, valid share amount, and user has enough cash for purchase
        db.execute("INSERT INTO orders (user_id, symbol, shares, amount, transaction) VALUES (?, ?, ?, ?, ?)", session.get("user_id"), symbol, int(shares), amount, 'BUY')
        new_cash = cash_value - purchased
        db.execute("UPDATE users SET cash = (?) WHERE id = (?)", new_cash, session.get("user_id"))
        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST": #user submitted a stock symbol
        symbol = request.form.get("symbol")
        info = lookup(symbol)
        if info == None:
            return render_template("quote.html")
        else:
            return render_template("quoted.html", info=info) #pass the stock info

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST": #they try submitting a user or pass

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        #no username submitted for registry
        if not username:
            return apology("must submit a username", 403)

        #user submitted, check to make sure it doesnt already exist
        elif username in db.execute("SELECT username FROM users"):
            return apology("username already exists", 403)

        #Ensure password was submitted
        if not password:
            return apology("must provide password", 403)
        else:
            if password != confirmation:
                return apology("password did not match", 403)
            else:
                db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, generate_password_hash(password))

        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    portfolio = [] #[{'Symbol': 'AAPL', 'Shares': 9}, {'Symbol': 'NFLX', 'Shares': 10}]
    symbol_list = db.execute("SELECT symbol FROM orders")  #[{'symbol': 'AAPL'}, {'symbol': 'NFLX'}]
    share_list = db.execute("SELECT shares FROM orders") #[{'shares': 9}, {'shares': 10}]

    i=0
    while i<len(symbol_list):
        portfolio.append({"Symbol": symbol_list[i]["symbol"], "Shares":share_list[i]["shares"]})
        i+=1

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        if not symbol:
            return apology("Wrong stock", 403)

        elif not shares or shares<=0:
            return apology("Wrong share count specified", 403)

        #check if specified share amount is fine
        for entry in portfolio:
            if entry["Symbol"] == symbol:
                if entry["Shares"]>=shares:
                    #update database tables (orders and users) and redirect to homepage
                    amount_sold = shares * int(lookup(symbol)["price"])

                    #how much cash user currently has
                    current_amount = (db.execute("SELECT cash FROM users WHERE id = (?)", session.get("user_id")))[0]["cash"]

                    #new cash amount after sale
                    new_cash_val = amount_sold + current_amount

                    db.execute("INSERT INTO orders (user_id, symbol, shares, amount, transaction) VALUES (?, ?, ?, ?, ?)",session.get("user_id"), symbol, shares, amount_sold, 'SELL')
                    db.execute("UPDATE users SET cash = (?) WHERE id = (?)", new_cash_val ,session.get("user_id"))

                    return redirect("/")

                else:
                    return apology("You dont have that many shares", 403)

    else:
        return render_template("sell.html", portfolio = portfolio)
