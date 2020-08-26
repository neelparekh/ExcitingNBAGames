import requests
import datetime
from typing import List, Dict, Tuple

# Hardcoding triggers for now
triggers = {
    'score_diff': 10, # int
    'time': '5:00', # str (e.g. '05:00' is 5 mins remaining)
    'quarter': 4, # int (note that 5 is OT, 6 is 2OT)
}
triggers['time'] = datetime.datetime.strptime(triggers['time'], '%M:%S')



def NBAScoreboard() -> List[Dict]:
    '''
    Get list of dictionary of daily NBA game data. 
    '''
    NBA_BASE='https://data.nba.net/10s/'
    r = requests.get(NBA_BASE + '/prod/v2/today.json').json()
    todayScoreboard = r['links']['todayScoreboard']
    return requests.get(NBA_BASE + todayScoreboard).json()

def format_datetime(t) -> datetime.datetime:
    if t == '': # e.g. halftime or end of quarter/game
        t = '00:00'
    if len(t.split(':')) == 1: # e.g. 2.6 seconds remaining
        t = f"00:{int(t.split('.')[0]):02}"
    return datetime.datetime.strptime(t, '%M:%S')

def format_quarter(q) -> str:
    if q > 4:
        return str(q%4) + 'OT'
    else:
        return str(q)


def get_exciting_games():
    scoreboard = NBAScoreboard()
    games = scoreboard['games']

    output = ''
    for game in games:
        # Make sure this game has started
        # if not game['isGameActivated']:
        #     continue

        # Parse game info
        home = game['hTeam']
        away = game['vTeam']
        score_diff = abs(int(home['score'])-int(away['score']))
        clock = format_datetime(game['clock']) 
        quarter = game['period']['current']

        # If it's an interesting game, show us the game info!
        if score_diff <= triggers['score_diff'] and clock <= triggers['time'] and quarter >= triggers['quarter']:
            print(f"Game Alert! ID#{game['gameId']}")
            output += " \n" +\
                f"{home['triCode']} {home['score']} - {away['triCode']} {away['score']} " +\
                f"{format_quarter(quarter)}Q {game['clock']}"

        else: # PURELY FOR TESTING
            output += "\n" + f"{home['triCode']} {home['score']} - {away['triCode']} {away['score']}"
        
    return output