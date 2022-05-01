from turtle import update
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

from helpers import clear_trajectories, update_state, update_frame, update_sources
from segments_data import SegmentsData
from trajectories_data import TrajectoriesData
from trajectory_plot import TrajectoryPlot
import os
import settings
import session
import state
from event import subscribe, emit
from navigation import create_navigation
from tables import create_tabs
from labeling import create_labeling_controls
from slider import create_slider


def initialize_state():
    state.segments = SegmentsData(settings.segments_path)
    state.trajectories = TrajectoriesData(settings.trajectories_path)
    state.current_frame = 0
    state.current_minute = 0
    state.cap = cv2.VideoCapture("./videos/video.m4v")
    state.total_frames = int(state.cap.get(cv2.CAP_PROP_FRAME_COUNT))
    state.plot = TrajectoryPlot(state.trajectories, state.segments)


initialize_state()

trajectories = state.trajectories
segments = state.segments

# ===============
# Callbacks
# ===============


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


# TODO: Find a good place for this
# Selection callbacks
# trajectories.get_source().selected.on_change('indices', trajectory_tap_handler)
trajectories.get_source().selected.on_change("indices", handle_tap(trajectories))
segments.get_source().selected.on_change("indices", handle_tap(segments))

# Setup initial frame
update_frame("", 1, 1)

slider_row = row(create_slider())
jump_to, *btns = create_navigation()
navigation_btns = row(
    *btns,
    session.save_progress(),
)
navigation = column(slider_row, jump_to, navigation_btns)
table_tabs = column(*create_tabs())
labeling_controls = column(table_tabs, *create_labeling_controls())
curdoc().add_root(row(state.plot.plot, labeling_controls))
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
