from format_utils import *

def to_NBAAPI_format(d):
    game={
        'hTeam': {
            'triCode': d['home_name'],
            'score': d['home_score'],
        },
        'vTeam': {
            'triCode': d['away_name'],
            'score': d['away_score'],
        },
        'clock': d['clock'],
        'period': {
            'current': d['quarter'],
        },
        'isGameActivated': d['isGameActivated']
    }
    return game

def inject_no_games():
    return []

def inject_no_exciting_games():
    game0={
        'home_name': 'PHO',
        'away_name': 'SAS',
        'home_score': '',
        'away_score': '',
        'clock': '',
        'quarter': '',
        'isGameActivated': False,
    }
    game1={
        'home_name': 'MIN',
        'away_name': 'MKE',
        'home_score': 76,
        'away_score': 45,
        'clock': '8:44',
        'quarter': '3',
        'isGameActivated': True,
    }
    return [to_NBAAPI_format(game) for game in [game0, game1]]

def inject_1_newly_exciting_1_unactivated_game():
    game0={
        'home_name': 'LAC',
        'away_name': 'DAL',
        'home_score': 110,
        'away_score': 112,
        'clock': "04:20",
        'quarter': 4,
        'isGameActivated': True,
    }
    game1={
        'home_name': 'PHO',
        'away_name': 'SAS',
        'home_score': '',
        'away_score': '',
        'clock': '',
        'quarter': '',
        'isGameActivated': False,
    }

    return [to_NBAAPI_format(game) for game in [game0, game1]]

def inject_2_unexciting_1_old_2_newly_exciting_games():
    game0 = {
        'home_name': 'BOS',
        'away_name': 'TOR',
        'home_score': 98,
        'away_score': 100,
        'clock': "06:22", # not in trigger range
        'quarter': 4,
        'isGameActivated': True,

    }
    game1 = {
        'home_name': 'IND',
        'away_name': 'MIA',
        'home_score': 98,
        'away_score': 100,
        'clock': "04:22",
        'quarter': 3, # not in trigger range
        'isGameActivated': True,
    }
    game2={ # game already exists
        'home_name': 'LAC',
        'away_name': 'DAL',
        'home_score': 113,
        'away_score': 112,
        'clock': "03:37",
        'quarter': 4,
        'isGameActivated': True,
    }
    game3={
        'home_name': 'LAL',
        'away_name': 'POR',
        'home_score': 100,
        'away_score': 92,
        'clock': "2.6",
        'quarter': 4,
        'isGameActivated': True,

    }
    game4 = {
        'home_name': 'DEN',
        'away_name': 'UTA',
        'home_score': 98,
        'away_score': 93,
        'score_diff': 5,
        'clock': "22.7",
        'quarter': 4,
        'isGameActivated': True,
    }
    return [to_NBAAPI_format(game) for game in [game0, game1, game2, game3, game4]]