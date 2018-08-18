import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime as dt
import chess_stats as ps
import json

app = dash.Dash('Chess Stats')

eco_names = ps.eco_labels('../data/eco_names.json')

app.layout = html.Div([
    html.H1('Chess Analysis'),
    dcc.Input(
        id='input-box',
        placeholder='Enter player name...',
        type='text',
        value='cesdaycart'
    ),
    html.Button('Submit', id='button'),

    dcc.Dropdown(id='my-dropdown'),

    html.Div([
        html.H2('Games Played'),
        dcc.Graph(id='game_count_graph')
    ], style={'width': '45%', 'display': 'inline-block'}),

    html.Div([
        html.H2('Elo'),
        dcc.Graph(id='elo_graph')
    ], style={'display': 'inline-block', 'width': '45%'}),

    html.H1('Opening Frequency per Week'),

    html.Div([
        dcc.Graph(id='opening_graph'),
        ]),

    #hidden div to store player data
    html.Div(id='player_data', style={'display': 'none'}),
])

#gets player username from input box then makes api call to chess.com
#for player data
@app.callback(Output('player_data', 'children'),
              [Input('button', 'n_clicks')],
              [State('input-box', 'value')])
def change_player_data(n_clicks, value):
    df = ps.game_stats_df(value)
    return df.to_json()

@app.callback(Output('my-dropdown', 'options'),
              [Input('player_data', 'children')])
def update_dropdown(player_data):
    dff = pd.read_json(player_data)
    time_controls = dff['time_class'].unique()
    return [{'label': time_control, 'value': time_control} for time_control in time_controls]

@app.callback(Output('elo_graph', 'figure'),
              [Input('my-dropdown', 'value'),
               Input('player_data', 'children')])
def update_ratings_graph(time_control_options, player_data):
    dff = pd.read_json(player_data).sort_values(by=['end_time'])
    filtered_df = dff[(dff['rules'] == 'chess') & (dff['time_class'] == time_control_options)]
    return {'data': [go.Scatter(
                                x=filtered_df['end_time'],
                                y=filtered_df['player_rating'].values,
                                text=filtered_df['player_color'],
                                mode='lines+markers',
                                marker={
                                    'size': 15,
                                    'color': filtered_df['rating_difference'],
                                    'line': {'width': 0.5, 'color': 'white'},
                                    'colorscale': 'Viridis',
                                    'showscale': True,
                                    'opacity': 0.5,})
                                    ],
        'layout': {'margin': {'l': 40, 'r': 40, 't': 70, 'b': 30}}
    }

@app.callback(Output('game_count_graph', 'figure'),
              [Input('my-dropdown', 'value'),
               Input('player_data', 'children')])
def update_games_graph(time_control_options, player_data):
    dff = pd.read_json(player_data)
    filtered_df = dff[(dff['rules'] == 'chess') & (dff['time_class'] == time_control_options)]
    number_of_games= filtered_df.resample('D', on='end_time').size().values
    dates =  filtered_df.resample('D', on='end_time').size().index
    return {
        'data': [{
            'x': dates,
            'y': number_of_games,
            'type': 'bar'
        }],
        'layout': {'margin': {'l': 40, 'r': 40, 't': 70, 'b': 30}}
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
        x = filtered_df.resample('W', on='end_time').mean().index
        y = filtered_df[filtered_df['eco'] == opening].resample('W', on='end_time').size()
        if y.sum() > 1:
            traces.append(go.Scatter(
                x=x,
                y=y,
                mode='lines+markers',
                marker={'opacity': 0.5},
                name=eco_names[opening]
        ))

    return {'data': traces,
            'layout': go.Layout(
                    xaxis={'title': 'Date'},
                    yaxis={'title': 'Number of Games'},
                    hovermode='closest'
                )}

app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

if __name__ == '__main__':
    app.run_server(debug=True)
