from flask import Flask, render_template, request, make_response, jsonify, redirect, Blueprint, url_for, flash
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from twilio.rest import Client
import os
import re
from random import randint
import datetime

# Basic config for Flask site
app = Flask(__name__)
Bootstrap(app)
nav = Nav(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
account_sid   = os.getenv("TWILIO_ACCOUNT_SID")
auth_token    = os.getenv("TWILIO_AUTH_TOKEN")
service_sid   = os.getenv("TWILIO_SERVICE_ID")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
VERIFY_SID = "VA442eaff8b7200bde1797269cd28eb572"

app.config['SECRET_KEY'] = b'z=\x19\xd5\xc2\xf0\x137\xc0\n\xdc\x9a*}\xd2\xd2'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

# User object
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    phone = db.Column(db.String(15), unique=True)
    verifyCode = db.Column(db.Integer())
    verifyCodeTimestamp = db.Column(db.DateTime())
    isVerified = db.Column(db.Boolean())
    wantsNotifications = db.Column(db.Boolean())
    def get_phone(self):
        return self.phone
    def get_id(self):
        return self.id
    def get_verify_code(self):
        return self.verifyCode
    def get_verify_code_timestamp(self):
        return self.verifyCodeTimestamp
    def get_is_verified(self):
        return self.isVerified

# blueprint for auth routes in our app
auth = Blueprint('auth', __name__)

# login route
@auth.route('/login')
def login():
    return render_template('login.html',pageClass="login")

# signup for account route
@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    print(email)
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first()

    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if user:
        flash('An account already exists with this email.')
        return redirect(url_for('auth.login')) # if user doesn't exist or password is wrong, reload the page

    # if the user doesn't exist, we will make a User and sign them in.
    newUser = User(email=email, password=generate_password_hash(password))
    db.session.add(newUser)
    db.session.commit()
    login_user(newUser)
    return redirect(url_for('home'))

# login POST (entered credentials to login)
@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    print(email)
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first()
    print(user)
    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if not user  or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login')) # if user doesn't exist or password is wrong, reload the page

    login_user(user)

    return redirect(url_for('home'))

# logout route
@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

# profile route
@auth.route('/profile')
def profile():
    em = current_user.get_email()
    return render_template('profile.html')

# register blueprint
app.register_blueprint(auth)

@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.get(int(user_id))

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

@app.route("/verify_phone", methods=["POST"])
def verifyPhone():
    inputPhone = request.form['phone']
    valid = re.match("^\(?([0-9]{3})\)?[-.●]?([0-9]{3})[-.●]?([0-9]{4})$", inputPhone)
    if not valid:
        flash('Invalid Phone Number', 'error')
        return redirect(url_for('home'))

    try:
        newUser = User(phone=inputPhone,
                       verifyCode=random(5),
                       verifyCodeTimestamp=datetime.datetime.now())
        db.session.add(newUser)
        db.session.commit()
    except:
        flash('DB Commit Failed', 'error')
        return redirect(url_for('home'))

    flash('Validated!', 'success')
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
