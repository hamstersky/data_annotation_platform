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
import os
import settings
import session
import state
from event import subscribe, emit
from navigation import create_navigation
from tables import create_tabs, get_active_tab

cap = cv2.VideoCapture("./videos/video.m4v")
trajectories = state.trajectories
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
    clear_trajectories()


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
    table = get_active_tab()
    indices = table.source.selected.indices
    ids = []
    for i in indices:
        ids.append(table.source.data["id"][i])
    segments.set_status(status=None, comments="", ids=ids)
    emit("label_changed", new_frame=state.current_frame)


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


def update_reset_btn_state(state):
    reset_label_btn.visible = state


subscribe("tab_switched", update_reset_btn_state)

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

# TODO: Find a good place for this
# Selection callbacks
# trajectories.get_source().selected.on_change('indices', trajectory_tap_handler)
trajectories.get_source().selected.on_change("indices", handle_tap(trajectories))
segments.get_source().selected.on_change("indices", handle_tap(segments))

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
table_tabs = column(*create_tabs())
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
