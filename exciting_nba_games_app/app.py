# flask imports
from flask import Flask, render_template, request, make_response, jsonify, redirect, Blueprint, url_for, flash
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user

# external dependencies
import os
import re
from random import randint
from datetime import datetime
import mysql.connector
from mysql.connector import Error
from twilio.rest import Client
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from typing import List, Dict, Tuple

# custom functions
from process_NBA_games import get_currently_exciting_games, games_to_text
from send_sms import send_SMS


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
    inputPhone = '+1' + inputPhone.replace("-","").replace("(","").replace(")","")
    code = randint(10000,99999)
    if not valid:
        flash('Invalid Phone Number', 'error')
        return redirect(url_for('home'))

    try:
        conn = mysql.connector.connect(host=ENDPOINT, database=DBNAME, user=USER, password=PW, connection_timeout=TIMEOUT_VALUE)
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
        flash('A text message containing a 5 digit code has been sent to your number')
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
            flash('Verification Complete! You will now receive notifications for all close games', 'success')
            return redirect(url_for('home'))
        else:
            flash('Incorrect Code Entered', 'error')
            flash('Verify', 'verify')
            return redirect(url_for('home'))
    except:
        flash('Verification Failed', 'error')
        return redirect(url_for('home'))


def newly_exciting_games(cur, conn, games: List[Dict]):
    '''
    Find users who want to be sent SMS about newly exciting games and send them an SMS with game information.

    Paramters
    ---------
    cur: sqlite3.Cursor
        cursor object from the connection to our databse
    conn: mysql.connector
        connection to our database
    exc_games: List[Dict]
        list of game info dicts

    '''
    try:
        # get all user verified consenting phone numbers 
        cur.execute(f"SELECT phone FROM users WHERE isVerified=1 AND wantsNotifications=1")
        results = cur.fetchall()
        if results: # make sure we have users before trying anything!
            user_numbers = [row[0] for row in results]

            # convert all game data into single text message
            data = {'message_body': games_to_text(games)}
            
            # send an individual text to each phone number
            for phone_number in user_numbers:
                send_SMS(data, phone_number)
            
            # update the db with newly sent games
            query_game_data = ", ".join(f"(CURRENT_TIMESTAMP(), '{game['home_name']}', '{game['away_name']}', '{game['clock']}', {game['score_diff']}, 1)" for game in games)
            query_str = f"INSERT INTO dev.game_data (game_date, home, away, clock_remaining, score_diff, sent_sms) VALUES " + query_game_data

            cur.execute(query_str)
            conn.commit()
            print(f"\tSuccess! Wrote {len(games)} new games to game_data")
    except:
        raise

def update_users():
    '''
    This polling function checks for new games and determines if they are exciting. It then updates participating users and a database table game_data with all
    newly exciting games.
    '''
    print(f'Checked for newly exciting games: {datetime.now()}')
    triggers = {
        'score_diff': 10, # int
        'time': '6:00', # str (e.g. '05:00' is 5 mins remaining)
        'quarter': 4, # int (note that 5 is OT, 6 is 2OT)
        }
    cegs = get_currently_exciting_games(triggers)
    if cegs: # if there are currently exciting games
        try:
            conn = mysql.connector.connect(host=ENDPOINT, database=DBNAME, user=USER, password=PW)
            cur = conn.cursor()
            
            # get previously processed games from today's date
            cur.execute(f"SELECT * FROM dev.game_data WHERE sent_sms=1 AND date_format(game_date, '%Y-%m-%d')=CURRENT_DATE()")
            sent_games = cur.fetchall()

            if sent_games:
                # check if we have already sent an SMS for any of our currently exciting games and exclude those.
                sent_home_names = [row[2] for row in sent_games]
                newly_cegs = [ceg for ceg in cegs if ceg['home_name'] not in sent_home_names]

                # if any remain, try sending a text with all newly exciting games
                if len(newly_cegs)>0:
                    newly_exciting_games(cur, conn, newly_cegs)
                else:
                    print("\tNo newly exciting games.")
            else:
                # send a text for all currently exciting games
                # using this might be an issue if the write to db for game_data fails even after successfully sending the message
                newly_exciting_games(cur, conn, cegs)
            
            # close our connection to db
            cur.close()
            conn.close()

        except:
            # Probably a db connection error
            raise
    else:
        print("\tNo games are currently exciting. :(")



if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_users, 'interval', minutes=1)
    # scheduler.add_job(refresh_games_db, 'interval', days=1, start_date='2020-09-10 00:00:00')
    scheduler.start()
    app.run(debug=True)
