from flask import Flask, render_template, request, make_response, jsonify, redirect, Blueprint, url_for, flash
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from twilio.rest import Client
import os
import re
from random import randint
from datetime import datetime
import mysql.connector
from mysql.connector import Error

# Basic config for Flask site
app = Flask(__name__)
Bootstrap(app)
nav = Nav(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

app.config['SECRET_KEY'] = b'z=\x19\xd5\xc2\xf0\x137\xc0\n\xdc\x9a*}\xd2\xd2'

account_sid   = os.getenv("TWILIO_ACCOUNT_SID")
auth_token    = os.getenv("TWILIO_AUTH_TOKEN")
service_sid   = os.getenv("TWILIO_SERVICE_ID")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

ENDPOINT="database-nba-1.clh7xmakjgjd.us-east-1.rds.amazonaws.com"
PORT="3306"
DBNAME="dev"
REGION="us-east-1"
USER=os.getenv("DB_USER")
PW=os.getenv("DB_PW")

# blueprint for auth routes in our app
auth = Blueprint('auth', __name__)

# login route
@auth.route('/login')
def login():
    return render_template('login.html',pageClass="login")

# login POST (entered credentials to login)
@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    print(email)
    password = request.form.get('password')
    return redirect(url_for('home'))

# logout route
@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

# register blueprint
app.register_blueprint(auth)

@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return

# create navigation bar for site
@nav.navigation('loggedoutnavbar')
def create_navbar():
    home_view = View('Home', 'home')
    return Navbar(home_view)

@nav.navigation('loggedinnavbar')
def create_loggedinnavbar():
    logout_view = View('Logout', 'home')
    profile_view = View('Profile', 'home')
    return Navbar(home_view, profile_view, logout_view)

# home page
@app.route('/')
def home():
    return render_template('home.html')

# signup route
@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route("/validate_phone", methods=["POST"])
def validatePhone():
    inputPhone = str(request.form['phone'])
    valid = re.match("^\(?([0-9]{3})\)?[-.●]?([0-9]{3})[-.●]?([0-9]{4})$", inputPhone)
    inputPhone = '+1' + inputPhone
    code = randint(10000,99999)
    if not valid:
        flash('Invalid Phone Number', 'error')
        return redirect(url_for('home'))

    try:
        conn = mysql.connector.connect(host=ENDPOINT, database=DBNAME, user=USER, password=PW)
        cur = conn.cursor()
        cur.execute(f"INSERT INTO dev.users (phone, verifyCode, verifyCodeTimeStamp, isVerified, wantsNotifications) VALUES ({inputPhone}, {code}, '{datetime.now()}', {0}, {1})")
        conn.commit()
        cur.close()
        conn.close()
    except:
        flash('DB Commit Failed', 'error')
        return redirect(url_for('home'))

    try:
        client = Client(account_sid, auth_token)
        message = client.messages \
                        .create(
                             body=str(code),
                             # messaging_service_sid=service_sid,
                             from_=twilio_number,
                             to=inputPhone
                         )
        flash('Verify', 'verify')
        return redirect(url_for('home'))
    except:
        flash('SMS Failed', 'error')
        return redirect(url_for('home'))

@app.route("/verify_phone", methods=["POST"])
def verifyPhone():
    verificationCode = request.form['verifyCode']
    try:
        conn = mysql.connector.connect(host=ENDPOINT, database=DBNAME, user=USER, password=PW)
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM dev.users WHERE verifyCode={verificationCode}")
        results = cur.fetchall()
        if results:
            cur.execute(f"UPDATE dev.users SET wantsNotifications=1, isVerified=1 WHERE verifyCode={verificationCode}")
            conn.commit()
            cur.close()
            conn.close()
            flash('Verification Complete!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Incorrect Code Entered', 'error')
            flash('Verify', 'verify')
            return redirect(url_for('home'))
    except:
        flash('Verification Failed', 'error')
        return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
