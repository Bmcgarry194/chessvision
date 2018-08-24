import pandas as pd
import json
import requests
import numpy as np
import chess
import chess.uci
import chess.pgn
import matplotlib.pyplot as plt
from io import StringIO

def get_monthly_archives(username):
    '''Returns a list of months in which the user played a game'''
    
    headers={'user-agent': '''ChessVision App, Author: Brian Mcgarry, GitHub: https://github.com/Bmcgarry194/chessvision, Email: bmcgarry816@gmail.com'''
    }
        
    try:
        response = requests.get(f'https://api.chess.com/pub/player/{username}/games/archives', headers=headers)
        return json.loads(response.content.decode('utf-8'))['archives'] 
    except:
        return []
        
def get_player_games(username):
    '''return a list of all games played'''
    headers={
        'user-agent': '''ChessVision App, Author: Brian Mcgarry, GitHub: https://github.com/Bmcgarry194/chessvision, Email: bmcgarry816@gmail.com'''
    }
    
    months = get_monthly_archives(username)
    games = []
    if not months:
        return games
    
    for month in months:
        response = requests.get(month, headers=headers)
        for game in json.loads(response.content.decode('utf-8'))['games']:
            games.append(game)
    return games

def game_stats_df(username):
    '''Returns a pandas dataframe containing stats for every game played'''
    
    game_list = get_player_games(username)
    
    player_rating = []
    rating_difference = []
    player_result = []
    opponent_result = []
    player_username = []
    opponent_username = []
    end_time = []
    pgn = []
    eco = []
    time_class = []
    rules = []
    player_color = []
    pieces_diff = []
    pieces_total = []
    pieces_black = []
    pieces_white = []
    url = []

    for i, game in enumerate(game_list):
        
        starting_position = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -'
        
        if (game['rules'] == 'chess') and (game['fen'] != starting_position):
            pgn_data = game['pgn'].split('\n')
            pgn.append(pgn_data[-1])
            eco.append(pgn_data[7].split('"')[-2])
            counts = piece_count(pgn_data[-1])
            pieces_diff.append(counts[0])
            pieces_total.append(counts[1])
            pieces_black.append(counts[2])
            pieces_white.append(counts[3])

        else:
            pgn.append(None)
            eco.append(None)
            pieces_diff.append(None)
            pieces_total.append(None)
            pieces_black.append(None)
            pieces_white.append(None)
            
        if game['black']['username'].lower() == username.lower():
            player_rating.append(game['black']['rating'])
            rating_difference.append(game['black']['rating'] - game['white']['rating'])
            player_result.append(game['black']['result'])
            opponent_result.append(game['white']['result'])
            player_username.append(game['black']['username'])
            player_color.append('black')
            opponent_username.append(game['white']['username'])
        else:
            player_rating.append(game['white']['rating'])
            rating_difference.append(game['white']['rating'] - game['black']['rating'])
            player_result.append(game['white']['result'])
            opponent_result.append(game['black']['result'])
            player_username.append(game['white']['username'])
            player_color.append('white')
            opponent_username.append(game['black']['username'])
            
        end_time.append(pd.to_datetime(game['end_time'], unit='s'))
        time_class.append(game['time_class'])
        rules.append(game['rules'])
        url.append(game['url'])

    df = pd.DataFrame({'player_username': player_username,
                       'player_color': player_color,
                       'player_rating': player_rating,
                       'rating_difference': rating_difference,
                       'player_result': player_result,
                       'opponent_result': opponent_result,
                       'end_time': end_time,
                       'time_class': time_class,
                       'rules': rules,
                       'pgn': pgn,
                       'eco': eco,
                       'opponent_username': opponent_username,
                       'pieces_diff': pieces_diff,
                       'pieces_total': pieces_total,
                       'pieces_black': pieces_black,
                       'pieces_white': pieces_white,})
    
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

def piece_count(pgn_string):
    '''Returns piece value balance for every move of the game.
    each piece has a value: pawns(p) = 1, bishops(b)/knights(n) = 3, rooks(r) = 5, queen(q) = 9,
    For every move the difference in piece value is calculate by white piece value - black piece value.
    So a positive number means you are ahead in material and and negitive number indicates you are down in material.
    
    Arg: 
        pgn_string: Takes a string of a chess game in pgn notation
    Returns:
        A tuple of lists of numbers corresponding to piece value at each move: (diff, total, black, white)
            diff = Difference in piece value, white adv is a positive int and black adv is a negitive int
            total = Total piece value for both players
            black = black piece value
            white = white piece value'''
    
    if not pgn_string:
        return (None, None, None, None)
    
    pgn = StringIO(pgn_string)
    game = chess.pgn.read_game(pgn)
    board = game.board()

    diff = []
    total = []
    black = []
    white = []
    for move in game.main_line():
        board.push(move)
        board_state = board.fen().split()[0]
        
        black_score = (board_state.count('p')*1 +
                       board_state.count('b')*3 +
                       board_state.count('r')*5 +
                       board_state.count('n')*3 +
                       board_state.count('q')*9
                      )
        white_score = (board_state.count('P')*1 +
                       board_state.count('R')*5 +
                       board_state.count('B')*3 +
                       board_state.count('N')*3 +
                       board_state.count('Q')*9
                      )
        diff.append(white_score - black_score)
        total.append(black_score + white_score)
        black.append(black_score)
        white.append(white_score)
    
    return (diff, total, black, white)

def move_evaluation(pgn_string, engine_path, evaluation_time=5000, output='list'):
    '''Takes pgn and returns engine evaluation
    Params:
        pgn_string: A string of the pgn
        engine_path: A string of the path to your engine
        evaluation_time: How long the engine will spend evaluating each move (in ms), default is 5000 ms (5 seconds)
        output: either 'list' (list of evaluation values) or 'graph' (graph of evaluation values)
    Returns: 
        If output == list: A list of numbers corresponding to the engine evaluation at each move of the game, positive favors white and negitive favors black
        If output == graph'''
        
    pgn = StringIO(pgn_string)
    game = chess.pgn.read_game(pgn)

    board = game.board()

    centipawn_eval = []
    #Loop over all game nodes:
    while not game.is_end():
        node = game.variations[0]
        board = game.board() 
        game = node

        #load your engine:
        handler = chess.uci.InfoHandler()
        engine = chess.uci.popen_engine(engine_path) 
        engine.info_handlers.append(handler)

        #give position to the engine:
        engine.position(board)

        #Set your evaluation time, in ms:
        evaluation = engine.go(movetime=evaluation_time)

        if handler.info["score"][1][0]:
            centipawn_eval.append(handler.info["score"][1][0])
        else:
            # mate in 1 = 6000 and is discounted(1/moves to mate) as the mate goes up as there as a high chance of not seeing the mate. This is not a great solution...
            mate_in = (1 / handler.info["score"][1][1]) * 6000 
            centipawn_eval.append(mate_in)
            
    eval_list = [eval_ * -1 if idx % 2 != 0 else eval_ for idx, eval_ in enumerate(centipawn_eval)] 
    
    if output == 'list':
        return eval_list
    
    elif output == 'graph':
        fig, ax = plt.subplots()
        x = list(range(len(eval_list)))
        y = eval_list
        ax.plot(x, y)
        ax.fill_between(x, 0, y, alpha=0.2)
        ax.axhline(0, ls='dashed', color='black')