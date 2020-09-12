from flask import Flask, render_template, request, make_response, jsonify, redirect, Blueprint, url_for, flash
from flask_bootstrap import Bootstrap
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from twilio.rest import Client
import os
import re
from random import randint
from datetime import datetime
import mysql.connector
from mysql.connector import Error

# Basic config for Flask site
app = Flask(__name__, static_folder="templates/static")
bootstrap = Bootstrap(app)
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
TIMEOUT_VALUE=7

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
    inputPhone = '+1' + inputPhone.replace("-","").replace("(","").replace(")","")
    code = randint(10000,99999)
    if not valid:
        print('invalid')
        flash('The phone number you entered was invalid. Please try again', 'error')
        return redirect(url_for('home'))
    try:
        conn = mysql.connector.connect(host=ENDPOINT, database=DBNAME, user=USER, password=PW, connection_timeout=TIMEOUT_VALUE)
        cur = conn.cursor()
        cur.execute(f"SELECT isVerified FROM dev.users WHERE phone={inputPhone}")
        results = cur.fetchall()
        if results and results[0][0] == 1:
            cur.close()
            conn.close()
            raise Exception
        else:
            cur.execute(f"DELETE FROM dev.users WHERE phone={inputPhone}")
            conn.commit()
            cur.execute(f"INSERT INTO dev.users (phone, verifyCode, verifyCodeTimeStamp, isVerified, wantsNotifications) VALUES ({inputPhone}, {code}, '{datetime.now()}', {0}, {1})")
            conn.commit()
            cur.close()
            conn.close()
    except:
        flash('The phone number you entered is already in our system', 'info')
        return redirect(url_for('home'))

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(body=str(code),from_=twilio_number,to=inputPhone)
        flash('A text message containing a 5 digit code has been sent to your number', 'info')
        return redirect(url_for('home'))
    except:
        conn = mysql.connector.connect(host=ENDPOINT, database=DBNAME, user=USER, password=PW, connection_timeout=TIMEOUT_VALUE)
        cur = conn.cursor()
        cur.execute(f"DELETE FROM dev.users WHERE phone={inputPhone}")
        conn.commit()
        cur.close()
        conn.close()
        flash('We were unable to send a text message to the number you provided', 'error')
        return redirect(url_for('home'))

@app.route("/verify_phone", methods=["POST"])
def verifyPhone():
    verificationCode = request.form['verifyCode']
    if int(verificationCode) < 10000 or int(verificationCode) > 99999:
        flash('Please enter a 5 digit code', 'error')
        return redirect(url_for('home'))
    try:
        conn = mysql.connector.connect(host=ENDPOINT, database=DBNAME, user=USER, password=PW)
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM dev.users WHERE verifyCode={verificationCode}")
        results = cur.fetchall()
        print(results)
        if results:
            if (datetime.now()-results[0][3]).seconds < 120:
                cur.execute(f"UPDATE dev.users SET wantsNotifications=1, isVerified=1 WHERE verifyCode={verificationCode}")
                conn.commit()
                cur.close()
                conn.close()
                flash('Verification Complete! You will now receive notifications for all close games', 'success')
                return redirect(url_for('home'))
            else:
                cur.execute(f"DELETE FROM dev.users WHERE verifyCode={verificationCode}")
                conn.commit()
                cur.close()
                conn.close()
                flash('You must enter the code within 2 minutes. Please refresh & try again', 'error')
                return redirect(url_for('home'))
        else:
            flash('The code you entered was incorrect. Please try again', 'error')
            flash('Verify', 'verify')
            return redirect(url_for('home'))
    except:
        flash('We were unable to verify your number. Please refresh the page and try again', 'error')
        return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
