import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime as dt
import chess_stats as cs
import json

app = dash.Dash('Chess Vision')

eco_names = cs.eco_labels('../data/eco_names.json')

#Layout of App

app.layout = html.Div([
    html.H1('Chess Vision'),
    
    dcc.Markdown('''
>
> “You may learn much more from a game you lose than from a game you win. You will have to lose hundreds of games before becoming a good player.” – José Raúl Capablanca
>
'''),
    
    dcc.Markdown('''To begin, type in your Chess.com username and hit submit (If you do not have a Chess.com account but would like to see the graphs, feel free to check out my games with my username: cesdaycart). This may take several seconds if you have a lot of games. Next, use the dropdown menu to select which time control you would like to view. Once this is done the graphs will begin to populate. You can select individual games from the Elo graph to show the piece value difference over the course of that game. All graphs are interactive and can be panned, zoomed, and selected to get a better look at your data. Good luck!'''),
                 
    #User name Input box
    dcc.Input(
        id='input-box',
        placeholder='Enter player name...',
        type='text',
    ),
    
    #Submit button
    html.Button('Submit', id='button'),
    
    #Dropdown menu to select a time control after inputing username
    html.Div([
        dcc.Dropdown(id='my-dropdown'),
    ], style={'width': '20%', 'marginBottom': 50, 'marginTop': 25}),
    
    #Graph of difference in piece values over the course of a selected game
    html.Div([
        html.H2('Piece Value Difference'),
        dcc.Graph(style={'height': '70vh'}, id='piece_difference_graph')
    ], style={'width': '50%', 'display': 'inline-block', 'height': '90vh'}),
    
    #Graph of games played with time played on the y and rating on x axis
    html.Div([
        html.H2('Elo'),
        dcc.Graph(style={'height': '70vh'}, id='elo_graph')
    ], style={'display': 'inline-block', 'width': '50%','height': '90vh'}),

    #Graph of the amount of times an opening was used by day
    html.Div([
    html.H1('Opening Frequency'),
    dcc.Graph(style={'width': '90vw', 'height': '80vh'}, id='opening_graph'),
    ], style={'height': '90vh'}),
    
    #Graph of games played per week
    html.Div([
        html.H1('Games Played'),
        dcc.Graph(style={'width': '90vw', 'height': '80vh'}, id='game_count_graph')
    ], style={'height': '90vh'}),
    
    html.Div([
        html.H1('Piece Count'),
        dcc.Markdown('''
        * This graph is more visually interesting than anything
            * Each line represents one game you have played. Its ups and downs corresponding with the ebb and flow of material on the board
            * Purple lines are games that you have lost while blue lines are games that you won
        *The first dropdown lets you pick if you want to view games you played as white or black
        *Pieces are given a numerical value:
            *Pawns = 1
            *Bishops and Knights = 3
            *Rooks = 5
            *Queen = 9
        *The second dropdown lets you indicate how you would like to calculate the material value
            *Difference takes the difference in material where a negitve number means that material favors black, while a positive number indicates white is up in material
            *Total takes the total material value of all pieces on the board
            *Black just gives the black material count
            *White gives the white material count'''),
        html.Div([
        dcc.Dropdown(id='color_dropdown',
                     placeholder='Select games you played as white or black...',
                     options=[{'label': color, 'value': color} for color in ['black', 'white']],),
        dcc.Dropdown(id='kind_dropdown',
                     placeholder='Select type of piece value evaluation...',
                    options=[{'label': label, 'value': value} for label, value in [('Difference in Piece Value', 0),
                                                                                   ('Total piece value', 1),
                                                                                   ('Black piece value', 2),
                                                                                   ('White piece value', 3)]],)
        
        ], style={'width': '40%', 'marginBottom': 25, 'marginTop': 25}),
        
        dcc.Graph(style={'width': '90vw', 'height': '80vh'}, id='piece_count_graph')
    ], style={'height': '90vh'}),

    #hidden div to store player data
    html.Div(id='player_data', style={'display': 'none'}),
])

#Updating graphs with new data

#gets player username from input box then makes api call to chess.com for player data
@app.callback(Output('player_data', 'children'),
              [Input('button', 'n_clicks')],
              [State('input-box', 'value')])
def change_player_data(n_clicks, value):
    df = cs.game_stats_df(value)
    return df.to_json()

@app.callback(Output('my-dropdown', 'options'),
              [Input('player_data', 'children')])
def update_dropdown(player_data):
    dff = pd.read_json(player_data)
    time_controls = dff['time_class'].unique()
    return [{'label': time_control, 'value': time_control} for time_control in time_controls]

@app.callback(Output('piece_difference_graph', 'figure'),
              [Input('elo_graph', 'clickData')])
def update_piece_difference_graph(game_data):
    x = list(range(len(game_data['points'][0]['customdata'])))
    y = game_data['points'][0]['customdata']
    return {'data': [go.Scatter(x=x,
                                y=y,
                                fill='tonexty',
                                line={'shape': 'spline'})
                    ]}

@app.callback(Output('elo_graph', 'figure'),
              [Input('my-dropdown', 'value'),
               Input('player_data', 'children')])
def update_elo_graph(time_control_options, player_data):
    dff = pd.read_json(player_data).sort_values(by=['end_time'])
    filtered_df = dff[(dff['rules'] == 'chess') & (dff['time_class'] == time_control_options)]
    return {'data': [go.Scatter(
                                x=filtered_df['end_time'],
                                y=filtered_df['player_rating'].values,
                                text=filtered_df['player_color'],
                                customdata=filtered_df['pieces_diff'],
                                mode='lines+markers',
                                marker={'size': 5}),
                                    ],
            'layout': go.Layout(hovermode = 'closest')
    }

@app.callback(Output('game_count_graph', 'figure'),
              [Input('my-dropdown', 'value'),
               Input('player_data', 'children')])
def update_game_count_graph(time_control_options, player_data):
    dff = pd.read_json(player_data)
    filtered_df = dff[(dff['rules'] == 'chess') & (dff['time_class'] == time_control_options)]
    number_of_games= filtered_df.resample('D', on='end_time').size().values
    dates =  filtered_df.resample('D', on='end_time').size().index
    return {
        'data': [{
            'x': dates,
            'y': number_of_games,
            'type': 'bar'
        }]
    }

@app.callback(Output('opening_graph', 'figure'),
              [Input('my-dropdown', 'value'),
              Input('player_data', 'children')])
def update_openings_graph(time_control_options, player_data):
    dff = pd.read_json(player_data)
    dff['end_time'] = pd.to_datetime(dff['end_time'])
    filtered_df = dff[(dff['rules'] == 'chess') & (dff['time_class'] == time_control_options)]
                          
    openings = filtered_df['eco'].unique()

    traces = []
    for opening in openings:
        x = filtered_df[filtered_df['eco'] == opening].resample('D', on='end_time').mean().index
        y = filtered_df[filtered_df['eco'] == opening].resample('D', on='end_time').size()
        traces.append(go.Bar(x=x, y=y, name=opening))

    return {'data': traces,
            'layout': go.Layout(
                    xaxis={'title': 'Date'},
                    yaxis={'title': 'Number of Games'},
                    barmode='stack',
                    hovermode = 'closest'
                )}

@app.callback(Output('piece_count_graph', 'figure'),
             [Input('my-dropdown', 'value'),
              Input('player_data', 'children'),
              Input('color_dropdown', 'value'),
              Input('kind_dropdown', 'value')])
def update_piece_count_graph(time_control_options, player_data, color, kind):
    df = pd.read_json(player_data)
    win_color_df = df[(df['player_color'] == color) & (df['win'] == True)]
    lose_color_df = df[(df['player_color'] == color) & (df['lose'] == True)]
    
    traces = []
    
    win_games = win_color_df['pgn'].values
    for game in win_games:
        if not game:
            continue
        score = cs.piece_count(game)
        x = list(range(len(score[kind])))
        y = score[kind]
        traces.append(go.Scatter(x=x,
                                 y=y,
                                 mode = 'lines',
                                 opacity = .12,
                                 showlegend = False,
                                 hoverinfo='none',
                                 line = {'color': 'steelblue',
                                         'shape': 'spline'}))
        
    lose_games = lose_color_df['pgn'].values
    for game in lose_games:
        if not game:
            continue
        score = cs.piece_count(game)
        x = list(range(len(score[kind])))
        y = score[kind]
        traces.append(go.Scatter(x=x,
                                 y=y,
                                 mode = 'lines',
                                 showlegend = False,
                                 hoverinfo='none',
                                 opacity = .1,
                                 line = {'color': 'purple',
                                         'shape': 'spline'}))
        
    return {'data': traces,
        'layout': go.Layout(
                xaxis={'title': 'Number of Moves'},
                yaxis={'title': 'Piece Value'},
            )}
app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

if __name__ == '__main__':
    app.run_server(debug=True)
