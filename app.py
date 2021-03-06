# flask imports
from flask import Flask, render_template, request, make_response, jsonify, redirect, Blueprint, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user

# external dependencies
import os
import re
from random import randint
from datetime import datetime
import mysql.connector
from mysql.connector import Error
from twilio.twiml.messaging_response import MessagingResponse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from dotenv import load_dotenv
from typing import List, Dict, Tuple

# custom packages
import settings
from twilio_connectors import send_SMS, validate_twilio_request
from process_NBA_games import get_currently_exciting_games, games_to_text


# Basic config for Flask site
app = Flask(__name__, static_folder="templates/static")
bootstrap = Bootstrap(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

app.config['SECRET_KEY'] = b'z=\x19\xd5\xc2\xf0\x137\xc0\n\xdc\x9a*}\xd2\xd2'

TIMEOUT_VALUE = settings.TIMEOUT_VALUE

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
    inputPhone = '+1' + re.sub(r'\D', '', inputPhone) # keep digits only
    code = randint(10000,99999)
    if not valid:
        flash('The phone number you entered was invalid. Please try again', 'error')
        return redirect(url_for('home',_anchor='getstarted'))
    try:
        conn = mysql.connector.connect(host=settings.ENDPOINT, database=settings.DBNAME, user=settings.USER, password=settings.PW, connection_timeout=settings.TIMEOUT_VALUE)
        cur = conn.cursor()
        cur.execute(f"SELECT isVerified FROM {settings.DBNAME}.users WHERE phone={inputPhone}")
        results = cur.fetchall()
        if results and results[0][0] == 1:
            cur.close()
            conn.close()
            raise Exception
        else:
            cur.execute(f"DELETE FROM {settings.DBNAME}.users WHERE phone={inputPhone}")
            conn.commit()
            cur.execute(f"INSERT INTO {settings.DBNAME}.users (phone, verifyCode, verifyCodeTimeStamp, isVerified, wantsNotifications) VALUES ({inputPhone}, {code}, '{datetime.now()}', {0}, {1})")
            conn.commit()
            cur.close()
            conn.close()
    except:
        flash('The phone number you entered is already in our system', 'info')
        return redirect(url_for('home',_anchor='getstarted'))

    try:
        data = {'message_body': f"Your sportsalerts.io verification code is: {str(code)}"}
        send_SMS(data=data, phone_number=inputPhone)
        flash('A text message containing a 5 digit code has been sent to your number', 'info')
        flash('Verify', 'verify')
        return redirect(url_for('home',_anchor='getstarted'))
    except:
        conn = mysql.connector.connect(host=ENDPOINT, database=DBNAME, user=USER, password=PW, connection_timeout=TIMEOUT_VALUE)
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {settings.DBNAME}.users WHERE phone={inputPhone}")
        conn.commit()
        cur.close()
        conn.close()
        flash('We were unable to send a text message to the number you provided', 'error')
        return redirect(url_for('home',_anchor='getstarted'))


@app.route("/verify_phone", methods=["POST"])
def verifyPhone():
    verificationCode = request.form['verifyCode']
    if int(verificationCode) < 10000 or int(verificationCode) > 99999:
        flash('Please enter a 5 digit code', 'error')
        return redirect(url_for('home',_anchor='getstarted'))
    try:
        conn = mysql.connector.connect(host=settings.ENDPOINT, database=settings.DBNAME, user=settings.USER, password=settings.PW, connection_timeout=TIMEOUT_VALUE)
        cur = conn.cursor()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {settings.DBNAME}.users WHERE verifyCode={verificationCode}")
        results = cur.fetchall()
        if results:
            if (datetime.now()-results[0][3]).seconds < 120:
                cur.execute(f"UPDATE {settings.DBNAME}.users SET wantsNotifications=1, isVerified=1 WHERE verifyCode={verificationCode}")
                conn.commit()
                cur.close()
                conn.close()
                # send a welcome text upon successful verification.
                phone_number = results[0][1]
                print(f"Welcome {phone_number}!")
                welcome_message = "Welcome to sportsalerts.io! You will now receive messages as soon as a game becomes exciting. You may unsubscribe by replying 'STOP'. Msg&Data rates may apply."
                data = {'message_body': welcome_message}
                send_SMS(data, phone_number)
                # flash confirmation
                flash('Verification Complete! You will now receive notifications for all close games', 'success')
                return redirect(url_for('home',_anchor='getstarted'))
            else:
                cur.execute(f"DELETE FROM {settings.DBNAME}.users WHERE verifyCode={verificationCode}")
                conn.commit()
                cur.close()
                conn.close()
                flash('You must enter the code within 2 minutes. Please refresh & try again', 'error')
                return redirect(url_for('home',_anchor='getstarted'))
        else:
            flash('The code you entered was incorrect. Please try again', 'error')
            flash('Verify', 'verify')
            return redirect(url_for('home',_anchor='getstarted'))
    except:
        flash('We were unable to verify your number. Please refresh the page and try again', 'error')
        return redirect(url_for('home',_anchor='getstarted'))

@app.route("/receive_sms", methods=["POST"])
@validate_twilio_request
def process_incoming_SMS():
    message_body = request.values.get('Body', None)
    phone_number = request.values.get('From', None)
    message_body = re.sub(r'[\W_]+', '', message_body).lower() # remove all punctuation
    phone_number = re.sub(r'\D', '', phone_number).lower() # remove all punctuation
    print(f"Message from {phone_number}: {message_body}")
    resp = MessagingResponse()
    try:
        # get the latest verification and subscription status of the requesting phone number.
        conn = mysql.connector.connect(host=settings.ENDPOINT, database=settings.DBNAME, user=settings.USER, password=settings.PW, connection_timeout=settings.TIMEOUT_VALUE)
        cur = conn.cursor()
        cur.execute(f"SELECT isVerified, wantsNotifications from {settings.DBNAME}.users WHERE phone={phone_number} ORDER BY verifyCodeTimeStamp DESC LIMIT 1")
        response = cur.fetchall()
        is_verified = response[0][0]
        wants_notifications = response[0][1]

        # now rocess the request
        if len(response) > 0: # This phone number exists in our system.
            if message_body in ['unsubscribe','stop']:
                if is_verified and wants_notifications: # valid unsubscription request
                    try:
                        cur.execute(f"UPDATE {settings.DBNAME}.users SET wantsNotifications=0 WHERE phone={phone_number}")
                        conn.commit()
                        cur.close()
                        conn.close()
                        resp.message("You have been successfully unsubscribed. You may resubscribe by texting 'START'.")
                    except:
                        resp.message("Please try unsubscribing again in a few minutes.")
                else: # ignore this unsubscription request!
                    resp.message("")
            elif message_body in ['start','resubscribe']:
                if is_verified and not wants_notifications: # valid re-subscription request
                    try:
                        conn = mysql.connector.connect(host=settings.ENDPOINT, database=settings.DBNAME, user=settings.USER, password=settings.PW, connection_timeout=settings.TIMEOUT_VALUE)
                        cur = conn.cursor()
                        cur.execute(f"UPDATE {settings.DBNAME}.users SET wantsNotifications=1 WHERE phone={phone_number}")
                        conn.commit()
                        cur.close()
                        conn.close()
                        resp.message("Welcome back! You may not receive notifications for games that have already begun today.")
                    except:
                        resp.message("Please try re-subscribing again in a few minutes.")
                else: # ignore this resubscription request!
                    resp.message("")
            else: # ignore this request!
                resp.message("")
        else: # This phone number does not exist in our system. Ignore this request!!
            resp.message("")
    except: # probably a larger issue and we should take care of it
        raise

    return str(resp)


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
        cur.execute(f"SELECT phone FROM {settings.DBNAME}.users WHERE isVerified=1 AND wantsNotifications=1")
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
            query_str = f"INSERT INTO {settings.DBNAME}.game_data (game_date, home, away, clock_remaining, score_diff, sent_sms) VALUES " + query_game_data

            cur.execute(query_str)
            conn.commit()
            print(f"\tSuccess! Wrote {len(games)} new games to game_data")
        else:
            print(f"There were {len(games)} exciting games, but no verified active users.")
    except:
        raise

def update_users():
    '''
    This polling function checks for new games and determines if they are exciting. It then updates participating users and a database table game_data with all
    newly exciting games.
    '''
    print(f'Checked for newly exciting games: {datetime.now()}')
    triggers = {
        'score_diff': 8, # int
        'time': '4:00', # str (e.g. '05:00' is 5 mins remaining)
        'quarter': 4, # int (note that 5 is OT, 6 is 2OT)
        'score_time_ratio': 2,
        }
    cegs = get_currently_exciting_games(triggers)
    if cegs: # if there are currently exciting games
        try:
            conn = mysql.connector.connect(host=settings.ENDPOINT, database=settings.DBNAME, user=settings.USER, password=settings.PW, connection_timeout=settings.TIMEOUT_VALUE)
            cur = conn.cursor()

            # get previously processed games from today's date
            cur.execute(f"SELECT * FROM {settings.DBNAME}.game_data WHERE sent_sms=1 AND date_format(game_date, '%Y-%m-%d')=CURRENT_DATE()")
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
    scheduler = BackgroundScheduler(timezone=pytz.timezone('US/Pacific'))
    scheduler.add_job(update_users, CronTrigger.from_crontab('* * * * *'), timezone=pytz.timezone('US/Pacific'))
    # scheduler.add_job(refresh_games_db, 'interval', days=1, start_date='2020-09-10 00:00:00')
    scheduler.start()
    app.run()
