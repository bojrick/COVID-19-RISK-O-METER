import os
import pathlib
import re

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output, State
import cufflinks as cf
from urllib.request import urlopen
import json
import plotly.graph_objects as go
from datetime import date

# Initialize app

today = date.today().strftime("%B %d, %Y")

mapbox_access_token = "pk.eyJ1IjoieXBhdGVsNTMiLCJhIjoiY2tlM3RyNTA4MDlydjJybW5sNTByZnpndSJ9.VCsPyg4mTUCTZ4WqnCvMNA"
mapbox_style = "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz"

app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)
server = app.server

# Load data

APP_PATH = str(pathlib.Path(__file__).parent.resolve())

df_lat_lon = pd.read_csv(
    os.path.join(APP_PATH, os.path.join("data", "final.csv"))
)
df_lat_lon["FIPS "] = df_lat_lon["FIPS "].apply(lambda x: str(x).zfill(5))

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

fig = go.Figure(go.Choroplethmapbox(geojson=counties, 
                                    locations=df_lat_lon['FIPS '], 
                                    z=df_lat_lon['max_risk'],
                                    colorscale="reds",
                                    marker_line_width=0, 
                                    hovertext = df_lat_lon['Hover'],
                                    hoverinfo='text',
                                    colorbar=dict(bgcolor='#000000',tickfont=dict(color='#FFFFFF'))))

fig = fig.update_layout(mapbox_style='light', 
                        mapbox_accesstoken=mapbox_access_token,
                        mapbox_zoom=3, 
                        mapbox_center = {"lat": 37.0902, "lon": -95.7129})
fig = fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

# App layout

app.layout = html.Div(
    id="root",
    children=[
        html.Div(
            id="header",
            children=[
                html.H4(children="COVID-19 RISK-O-METER"),
                html.P(
                    id="description",
                    children="† Estimation of max people getting infected is calculated using daily number of cases and CDC provided guidance to measure spread of COVID-19 among communities",
                ),
            ],
        ),
        html.Div(
            id="app-container",
            children=[
                html.Div(
                    id="left-column",
                    children=[
                        html.Div(
                            id="heatmap-container",
                            children=[
                                html.P(id="heatmap-title",
                                    children="Estimated Maximum Number of People who can get infected on "+today
                                ),
                                dcc.Graph(
                                    id="county-choropleth",
                                    figure=fig
                                    ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

if __name__ == "__main__":
    app.run_server(debug=True)
