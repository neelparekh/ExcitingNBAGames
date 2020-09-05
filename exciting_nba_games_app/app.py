from flask import Flask, render_template, request, make_response, jsonify, redirect, Blueprint, send_from_directory, url_for, flash
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from typing import List, Dict, Tuple
from send_sms import send_SMS
from ExcitingNBAGames import get_exciting_games

# Basic config for Flask site
app = Flask(__name__)
Bootstrap(app)
nav = Nav(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

app.config['SECRET_KEY'] = b'z=\x19\xd5\xc2\xf0\x137\xc0\n\xdc\x9a*}\xd2\xd2'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

# User object
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(500), unique=True)
    password = db.Column(db.String(100))

    def get_email(self):
        return self.email
    def get_id(self):
        return self.id

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
    test_view = View('Test', 'testNotifs')
    return Navbar(home_view, test_view)

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

@app.route("/testNotifs")
def testNotifs():
    exciting_games = get_exciting_games()
    if exciting_games != '':
        print(exciting_games)
        data = {'message_body': exciting_games + '\n\n And Remember: Always double back!'}
        result = send_SMS(data, '+14084807564')
        return result
    else:
        return "No exciting NBA games found."



if __name__ == "__main__":
    app.run(debug=True)
