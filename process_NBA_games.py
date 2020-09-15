import requests
import datetime
from format_utils import *
from typing import List, Dict, Tuple

from test_polling import *


def request_NBA_scoreboard() -> List[Dict]:
    '''
    Get all daily NBA game data.
    
    Returns
    -------
    scoreboard: List[Dict] (json)
    '''
    try:
        NBA_BASE='https://data.nba.net/10s/'
        r = requests.get(NBA_BASE + '/prod/v2/today.json')
        r.raise_for_status()
        todayScoreboard = r.json()['links']['todayScoreboard']
        s = requests.get(NBA_BASE + todayScoreboard)
        s.raise_for_status()
        scoreboard = s.json()
        return scoreboard
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def get_currently_exciting_games(triggers) -> List[Dict]:
    '''
    Get specific information for games that are currently exciting

    Parameters
    ----------
    triggers: Dict

    Returns
    -------
    exciting_games: List[Dict]
        games that are found to be exciting based on the triggers provided
    '''

    ##### TESTS #####
    scoreboard = request_NBA_scoreboard()
    games = scoreboard['games']
    # games = inject_no_games()
    # games = inject_no_exciting_games()
    # games = inject_1_newly_exciting_1_unactivated_game()
    # games = inject_2_unexciting_1_old_2_newly_exciting_games()
    #################



    exciting_games=[]
    for game in games:

       # Make sure this game has started
        if not game['isGameActivated']:
             continue

        # Parse game info
        home = game['hTeam']
        away = game['vTeam']
        
        home_name = home['triCode']
        away_name = away['triCode']
        home_score = int(home['score'])
        away_score = int(away['score'])
        score_diff = abs(int(home['score'])-int(away['score']))
        clock = format_datetime(game['clock'])
        quarter = game['period']['current']
        
        # If it's an interesting game, return the game info
        triggers_time = format_datetime(triggers['time'])
        if score_diff <= triggers['score_diff'] and clock <= triggers_time and quarter >= triggers['quarter']:
            exciting_games.append({
                'home_name': home_name,
                'away_name': away_name,
                'home_score': home_score,
                'away_score': away_score,
                'score_diff': score_diff,
                'clock': format_clock(game['clock']),
                'quarter': quarter,
                })
    return exciting_games


def games_to_text(games: List[Dict]) -> str:
    '''
    convert list of game dicts to human-readable text to be sent via SMS

    Parameters
    ----------
    games: List[Dict]

    Returns
    -------
    text: str
    '''
    text = ''
    for game in games:
        text += " \n" +\
        f"{game['home_name']} {game['home_score']} - {game['away_name']} {game['away_score']} " +\
        f"{format_quarter(game['quarter'])}Q {game['clock']}"
    return text
