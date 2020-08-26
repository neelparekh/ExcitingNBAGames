from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from typing import List, Dict, Tuple
from send_sms import send_SMS
from ExcitingNBAGames import get_exciting_games

app = Flask(__name__)
Bootstrap(app)
nav = Nav(app)

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
