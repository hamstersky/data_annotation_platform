from dash import Dash, html, dcc, dash_table, callback_context
import plotly.express as px
import cv2
from PIL import Image
import plotly.express as px
from dash import dcc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
from dash.exceptions import PreventUpdate

app = Dash(__name__)
frames = []
cap = cv2.VideoCapture("./video/video.m4v")
ret = True
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
data = pd.read_pickle("./data/broken_trajectories.pkl")
data.reset_index(inplace=True)
colors = [
    "red",
    "magenta",
    "green",
    "orange",
    "cyan",
    "yellow",
    "blue",
    "black",
    "navy",
]
classes = ["person", "bicycle", "car", "motorcycle", "", "bus", "", "truck"]


@app.callback(
    [Output("test", "figure"), Output("cur-frame", "children")],
    [Input("slider", "value")],
)
def update_frame(frame_nr):
    if frame_nr is None:
        frame_nr = 0
    return get_frame(frame_nr)


def get_frame(frame_nr=0):
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_nr)
    _, frame = cap.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    im = Image.fromarray(frame)
    width, height = im.size
    subset = data[
        (frame_nr >= data["frame_in"]) & (frame_nr <= data["frame_out"] + 900)
    ]
    subset = subset[["xs", "ys", "class", "id"]].to_numpy()
    fig = go.Figure()
    fig.update_layout(width=width, height=height)
    for row in subset:
        cls = int(row[[2]])
        cls_str = classes[cls]
        ids = [row[3] for _ in row[0]]
        fig.add_scatter(
            x=row[0],
            y=row[1],
            mode="lines",
            marker={"color": colors[cls]},
            hovertemplate="test<extra>{cls_str}</extra>",
            ids=ids,
        )
    fig.add_layout_image(
        dict(
            source=im,
            xref="x",
            yref="y",
            x=0,
            y=360,
            sizex=width,
            sizey=height,
            opacity=1,
            layer="below",
        )
    )
    fig.update_xaxes(visible=False, range=(0, width))
    fig.update_yaxes(visible=False, range=(0, height))
    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
    return (fig, frame_nr)


@app.callback(Output("slider", "value"), [Input("frame-nr", "value")])
def test(v):
    return v


@app.callback(
    [Output("connections", "data"), Output("data-table", "data")],
    [Input("test", "clickData"), Input("connect", "n_clicks")],
    State("connections", "data"),
)
def click_data(traj_data, _, connection_data):
    ctx = callback_context

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger == "test":
        return update_connections(traj_data, connection_data)
    else:
        return [], []


def update_connections(traj_data, connection_data):
    if traj_data is None:
        raise PreventUpdate
    traj_id = traj_data["points"][0]["id"]
    connection_data = connection_data or []
    connection_data.append({"id": traj_id})
    return (connection_data, connection_data)


app.layout = html.Div(
    children=[
        dcc.Store(id="connections", storage_type="session"),
        html.H1(children="Data annotation"),
        dcc.Graph(id="test", figure=get_frame()[0]),
        html.P(id="cur-frame", children=""),
        dcc.Slider(0, total_frames, 1, marks=None, id="slider"),
        dcc.Input(id="frame-nr", type="number", placeholder=0),
        dash_table.DataTable(id="data-table", columns=[{"name": "id", "id": "id"}]),
        html.Button("Connect", id="connect"),
    ]
)


if __name__ == "__main__":
    app.run_server(debug=True, threaded=False)
