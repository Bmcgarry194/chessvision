import pandas as pd
import json
import random
import datetime
import requests
import numpy as np
import re

def get_monthly_archives(username):
    '''Returns a list of months in which the user played a game'''
    try:
        response = requests.get(f'https://api.chess.com/pub/player/{username}/games/archives')
        months_played = json.loads(response.content.decode('utf-8'))['archives']
        return [month[-7:].split('/') for month in months_played]
    except:
        return []
        
def get_player_games(username):
    '''return a list of all games played'''
    
    months = get_monthly_archives(username)
    games = []
    if months:
        for month in months:
            year = month[0]
            month_ = month[1]
            response = requests.get(f'https://api.chess.com/pub/player/{username}/games/{year}/{month_}')
            for game in json.loads(response.content.decode('utf-8'))['games']:
                games.append(game)
    return games

def game_stats_df(username):
    '''Returns a pandas dataframe containing stats for every game played'''
    
    game_list = get_player_games(username)
    
    player_rating = []
    rating_difference = []
    player_result = []
    player_username = []
    end_time = []
    pgn = []
    eco = []
    rated = []
    time_class = []
    rules = []
    game_length = []
    player_color = []

    for i, game in enumerate(game_list):
        
        starting_position = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -'
        
        if (game['rules'] == 'chess') and (game['fen'] != starting_position):
            pgn_data = game['pgn'].split('\n')
            pgn.append(pgn_data[-1])
            eco.append(pgn_data[7].split('"')[-2])
            game_length.append(int(re.split("(\d+)\.+", game['pgn'])[-2]))

        else:
            pgn.append(None)
            eco.append(None)
            game_length.append(None)
            
        if game['black']['username'].lower() == username.lower():
            player_rating.append(game['black']['rating'])
            rating_difference.append(game['black']['rating'] - game['white']['rating'])
            player_result.append(game['black']['result'])
            player_username.append(game['black']['username'])
            player_color.append('black')
        else:
            player_rating.append(game['white']['rating'])
            rating_difference.append(game['white']['rating'] - game['black']['rating'])
            player_result.append(game['white']['result'])
            player_username.append(game['white']['username'])
            player_color.append('white')
            
        end_time.append(pd.to_datetime(game['end_time'], unit='s'))
        rated.append(game['rated'])
        time_class.append(game['time_class'])
        rules.append(game['rules'])

    df = pd.DataFrame({'player_username': player_username,
                       'player_color': player_color,
                       'player_rating': player_rating,
                       'rating_difference': rating_difference,
                       'player_result': player_result,
                       'end_time': end_time,
                       'rated': rated,
                       'time_class': time_class,
                       'rules': rules,
                       'pgn': pgn,
                       'eco': eco,
                       'game_length':game_length})
    
#Create three columns in the data frame indicating a win, draw, or loss with a True or False
    df['win'] = df['player_result'] == 'win'

    draw = {'agreed', 'repetition', 'stalemate',
            'insufficient', '50move', 'timevsinsufficient'}
    
    df['draw'] = df['player_result'].isin(draw)

    lose = {'checkmated', 'timeout', 'resigned', 'lose', 'abandoned',
           'kingofthehill', 'threecheck'}

    df['lose'] = df['player_result'].isin(lose)
    
    return df

#open dict of eco labels and names
def eco_labels(filepath):
    with open(filepath) as infile:
        eco_names = json.load(infile)
    return eco_names
