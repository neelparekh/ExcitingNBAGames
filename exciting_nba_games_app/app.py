from flask import Flask
from typing import List, Dict, Tuple
from send_sms import send_SMS
from ExcitingNBAGames import get_exciting_games 

app = Flask(__name__)

@app.route("/")
def hello():
    exciting_games = get_exciting_games()
    if exciting_games != '':
        print(exciting_games)
        data = {'message_body': exciting_games + '\n\n And Remember: Always double back!'}
        result = send_SMS(data, '+14084807564')
        return result
    else:
        return "No exciting NBA games found."

if __name__ == "__main__":
    app.run()
