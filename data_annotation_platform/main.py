import cv2, uuid
import numpy as np
import pandas as pd
from bokeh.events import Tap
from bokeh.layouts import column, layout, row
from bokeh.models import (
    Button,
    ColumnDataSource,
    CustomJS,
    DataTable,
    MultiChoice,
    NumericInput,
    Panel,
    Paragraph,
    PreText,
    Slider,
    TableColumn,
    Tabs,
)
from bokeh.palettes import RdYlBu3
from bokeh.plotting import curdoc, figure

from helpers import get_frame_from_cap, get_image_from_frame, update_sources
from segments_data import SegmentsData
from trajectories_data import TrajectoriesData
from trajectory_plot import TrajectoryPlot
from handle_jump_to_frame import handle_jump_to_frame
import os
import settings
import session
import state
from event import subscribe, emit
from navigation import create_navigation

cap = cv2.VideoCapture("./videos/video.m4v")
trajectories = TrajectoriesData("./data/broken_trajectories.pkl")
segments = state.segments
plot = TrajectoryPlot(trajectories, segments)
capture_width = int(cap.get(3))
state.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
FRAME_INTERVAL = 1800
active_traj_type = None

# ===============
# Helpers
# ===============
def clear_trajectories():
    trajectories.update_selected_data([], [])
    segments.update_selected_data([], [])
    for table in TABLES.values():
        table.source.selected.indices = []


def update_stats():
    return f"""
Number of correct segments: {segments.get_correct_segment_count()}
Number of incorrect segments: {segments.get_incorrect_segment_count()}
Accuracy: {"{:.2f}".format(segments.get_correct_incorrect_ratio() * 100)}%
    """


def update_tables():
    # TODO: Find better way for keeping track of the original index
    # At least remove the direct access to the index
    incorrect_segments_table_source.data = segments.get_segments_by_status(False)
    incorrect_segments_table_source.data[
        "original_index"
    ] = segments.get_segments_by_status(False).index
    correct_segments_table_source.data = segments.get_segments_by_status(True)
    new_segments_table_source.data = segments.get_new_segments()


def update_slider_limits():
    max_minute = state.total_frames // 60 // 30
    slider.start = state.current_minute * FRAME_INTERVAL
    if state.current_minute == max_minute:
        slider.end = state.total_frames - 1
    else:
        slider.end = (state.current_minute + 1) * FRAME_INTERVAL


def update_state():
    if len(trajectories.get_selected_trajectories()) > 1:
        connect_btn.disabled = False
        incorrect_btn.disabled = True
        incorrect_comment.visible = False
        correct_btn.disabled = True
    elif segments.get_selected_trajectories():
        connect_btn.disabled = True
        incorrect_btn.disabled = False
        incorrect_comment.visible = True
        correct_btn.disabled = False
    else:
        connect_btn.disabled = True
        incorrect_btn.disabled = True
        incorrect_comment.visible = False
        correct_btn.disabled = True


# ===============
# Callbacks
# ===============


def handle_label_changed(new_frame):
    update_frame("", 0, new_frame)
    update_tables()
    clear_trajectories()
    # TODO: Remove dependency on stats
    stats.text = update_stats()


def update_frame(attr, old, frame_nr):
    frame = get_frame_from_cap(cap, frame_nr)
    img = get_image_from_frame(frame)
    plot.update_img(img)
    update_sources([trajectories, segments], frame_nr)


def handle_tap(trigger):
    def callback(_, old, new):
        # Temporarily remove callback to prevent infinite triggers as the
        # callback itself changes the value of the trigger
        trigger.get_source().selected._callbacks = {}
        if len(new) > 0:
            selected_traj_id = trigger.get_id_of_selected_trajectory(new[0])
            if (
                isinstance(trigger, TrajectoriesData)
                and not trigger.get_selected_trajectories()
            ):
                trigger.update_source_candidates(selected_traj_id)
                # Needed so that the first trajectory remains the selected one
                trigger.update_selected_data(old, [0])
            else:
                trigger.update_selected_data(old, new)
        else:
            clear_trajectories()
            # TODO: Other way to get the slider value? Maybe consider the current
            # frame to be some global variable or instance variable of plot class or
            # some other new class?
            # Restores state without candidate trajectories
            update_sources([trajectories], state.current_frame)
        update_state()
        # Restore the callback
        trigger.get_source().selected.on_change("indices", handle_tap(trigger))

    return callback


def handle_connect():
    # TODO: Make a connect method that connects a list of ids
    # Can't be part of segments as it doesn't have access to the whole data
    # Creates segments needed to connect the supplied trajectories (ids)
    # Connections will be done in the order of the supplied ids
    ids = trajectories.get_selected_trajectories()
    pairs = [tuple(map(int, x)) for x in zip(ids, ids[1:])]
    new_frame = 0
    for t1_ID, t2_ID in pairs:
        t1 = trajectories.get_trajectory_by_id(t1_ID)
        t2 = trajectories.get_trajectory_by_id(t2_ID)
        # TODO: Consider the append being an internal call. Possibly still return the segment
        segment = segments.create_segment(t1, t2)
        segments.append_segment(segment)
        new_frame = int(segment["frame_out"])
    emit("label_changed", new_frame=new_frame)


subscribe("label_changed", handle_label_changed)


def handle_label_btn_click(label):
    def callback():
        segments.set_status(status=label, comments=incorrect_comment.value)
        emit("label_changed", new_frame=state.current_frame)

    return callback


def handle_reset_label():
    table = TABLES[tabs.tabs[tabs.active].name]
    indices = table.source.selected.indices
    ids = []
    for i in indices:
        ids.append(table.source.data["id"][i])
    segments.set_status(status=None, comments="", ids=ids)
    table.source.selected._callbacks = {}
    table.source.selected.indices = []
    table.source.selected.on_change("indices", handle_table_row_clicked(table))
    emit("label_changed", new_frame=state.current_frame)


def handle_table_row_clicked(table):
    def callback(_, old, new):
        if new:
            frame = table.source.data["frame_in"][new[0]]
            handle_jump_to_frame("", 0, frame)

    return callback


def handle_tab_switched(attr, old, new):
    reset_tables = ["wrong_segments", "correct_segments", "new_segments"]
    reset_label_btn.visible = tabs.tabs[new].name in reset_tables
    tab_description.text = descriptions[tabs.tabs[new].name]


def handle_minute_changed(value):
    def callback():
        max_minute = state.total_frames // 60 // 30
        next_minute = state.current_minute + value
        if next_minute >= 0 and next_minute <= max_minute:
            state.current_minute += value
            update_slider_limits()
            slider.value = slider.end if value < 0 else slider.start

    return callback


def update_slider():
    update_slider_limits()
    slider.value = state.current_frame
    update_frame("", 0, state.current_frame)


# ===============
# Widgets / Layout
# ===============


# Slider
# For preventing going over the last frame
slider = Slider(
    start=0,
    end=FRAME_INTERVAL,
    value=1,
    step=1,
    width=plot.plot.width - 150,
    margin=(0, 15, 0, 15),
)
slider.on_change("value", update_frame)
next_min_btn = Button(label="+1min", width=50)
next_min_btn.on_click(handle_minute_changed(1))
prev_min_btn = Button(label="-1min", width=50)
prev_min_btn.on_click(handle_minute_changed(-1))

slider_component = [
    Paragraph(text="Use the slider to change frames:"),
    [prev_min_btn, slider, next_min_btn],
]
subscribe("frame_updated", update_slider)

btn_settings = {"disabled": True}
connect_btn = Button(label="Connect", **btn_settings)
connect_btn.on_click(handle_connect)

# Restore segment button
reset_label_btn = Button(label="Reset label", visible=False)
reset_label_btn.on_click(handle_reset_label)

# Wrong connection component
incorrect_btn = Button(label="Incorrect segment", **btn_settings)
incorrect_btn.on_click(handle_label_btn_click(False))
incorrect_options = ["reason1", "reason2"]
incorrect_comment = MultiChoice(
    options=incorrect_options,
    visible=False,
    title="Select the reason(s) why the connection is incorrect by clicking on the input box.",
)

correct_btn = Button(label="Correct segment", **btn_settings)
correct_btn.on_click(handle_label_btn_click(True))

reset_select_btn = Button(label="Reset selection")
reset_select_btn.on_click(clear_trajectories)

labeling_controls = [
    reset_select_btn,
    connect_btn,
    correct_btn,
    incorrect_btn,
    incorrect_comment,
]

# Stats
stats = PreText(text=update_stats())

# Settings for all tables
columns = [
    TableColumn(field=c, title=c) for c in ["id", "frame_in", "frame_out", "class"]
]
table_params = {
    "columns": columns,
    "index_position": None,
    "height": 250,
    "width": 550,
}

# Incorrect segments component
incorrect_segments_table_source = ColumnDataSource(
    segments.get_segments_by_status(False)
)
incorrect_segments_table = DataTable(
    source=incorrect_segments_table_source,
    **{key: table_params[key] for key in table_params if key != "columns"},
    columns=[*columns, TableColumn(field="comments", title="comments")],
)
incorrect_segments_table_source.selected.on_change(
    "indices", handle_table_row_clicked(incorrect_segments_table)
)

# Candidates table
# TODO: Add euclidean distance
trajectories_table = DataTable(source=trajectories.get_source(), **table_params)

# New segments table
new_segments_table_source = ColumnDataSource(segments.get_new_segments())
new_segments_table = DataTable(source=new_segments_table_source, **table_params)
new_segments_table_source.selected.on_change(
    "indices", handle_table_row_clicked(new_segments_table)
)

# Correct segments table
correct_segments_table_source = ColumnDataSource(segments.get_segments_by_status(True))
correct_segments_table = DataTable(source=correct_segments_table_source, **table_params)
correct_segments_table_source.selected.on_change(
    "indices", handle_table_row_clicked(correct_segments_table)
)

descriptions = {
    "trajectories": "Trajectories/candidates on current frame. Click a trajectory to select it:",
    "wrong_segments": "Wrong segments:",
    "correct_segments": "Correct segments:",
    "new_segments": "Manually created segments:",
    "current_selection": "Currently selected trajectories:",
    "stats": "",
}
trajectories_tab = Panel(
    child=trajectories_table, title="Current frame", name="trajectories"
)
wrong_segments_tab = Panel(
    child=incorrect_segments_table, title="Wrong segments", name="wrong_segments"
)
correct_segments_tab = Panel(
    child=correct_segments_table, title="Correct segments", name="correct_segments"
)
new_segments_tab = Panel(
    child=new_segments_table, title="New segments", name="new_segments"
)

stats_tab = Panel(child=stats, title="Statistics", name="stats")
tab_description = Paragraph(text=descriptions["trajectories"])
tabs = Tabs(
    tabs=[
        trajectories_tab,
        correct_segments_tab,
        wrong_segments_tab,
        new_segments_tab,
        stats_tab,
    ],
    height=280,
)
tabs.on_change("active", handle_tab_switched)

# TODO: Find a good place for this
# Selection callbacks
# trajectories.get_source().selected.on_change('indices', trajectory_tap_handler)
trajectories.get_source().selected.on_change("indices", handle_tap(trajectories))
segments.get_source().selected.on_change("indices", handle_tap(segments))


TABLES = {
    "trajectories": trajectories_table,
    "wrong_segments": incorrect_segments_table,
    "correct_segments": correct_segments_table,
    "new_segments": new_segments_table,
}

BUTTONS = [reset_select_btn, connect_btn, incorrect_btn, correct_btn]

for btn in BUTTONS:
    btn.on_click(update_state)

# Setup initial frame
update_frame("", 1, 1)

slider_row = row(prev_min_btn, slider, next_min_btn)
jump_to, *btns = create_navigation()
navigation_btns = row(
    *btns,
    session.save_progress(),
)
navigation = column(slider_row, jump_to, navigation_btns)
table_tabs = column(
    tab_description,
    tabs,
)
labeling_controls = column(
    table_tabs,
    reset_label_btn,
    reset_select_btn,
    connect_btn,
    correct_btn,
    incorrect_btn,
    incorrect_comment,
)
curdoc().add_root(row(plot.plot, labeling_controls))
curdoc().add_root(navigation)


# Create layout
# curdoc().add_root(
#     layout(
#         [
#             [
#                 plot.plot,
#                 [
#                     tab_description,
#                     tabs,
#                     reset_label_btn,
#                     *labeling_controls,
#                 ],
#             ],
#             *slider_component,
#             jump_to,
#             [
#                 second_backward,
#                 previous_frame,
#                 next_frame,
#                 second_forward,
#                 next_interest,
#                 save_btn,
#             ],
#             store_cookie_trigger,
#         ]
#     )
# )
