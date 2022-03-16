from random import random

from bokeh.layouts import column, layout
from bokeh.models import Button, Slider, ColumnDataSource, HoverTool, DataTable, TableColumn, Paragraph, NumericInput
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure, curdoc
from bokeh.events import Tap
import cv2
import numpy as np
from segments_data import SegmentsData
from trajectories_data import TrajectoriesData
from trajectory_plot import TrajectoryPlot
from helpers import get_frame_from_cap, get_image_from_frame, update_sources

cap_w = 640
cap_h = 360

cap = cv2.VideoCapture('../videos/video.m4v')
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
trajectories = TrajectoriesData('../data/broken_trajectories.pkl')
segments = SegmentsData('../data/segments.pkl')
plot = TrajectoryPlot(trajectories, segments)

# ===============
# Helpers
# ===============
def clear_trajectories(trigger):
    table_source.data['traj_id'] = []
    trigger.update_selected_data([], [])

def update_stats():
    total = segments.get_data().shape[0]
    correct_count = segments.get_data()[segments.get_data()['correct']==True].shape[0]
    incorrect_count = segments.get_data()[segments.get_data()['correct']==False].shape[0]
    ratio = correct_count / total
    return f'''Correct: {correct_count}
    Incorrect: {incorrect_count}
    Ratio: {ratio}
    '''

# ===============
# Callbacks
# ===============

def update_frame(attr, old, new):
    frame_nr = new
    frame = get_frame_from_cap(cap, frame_nr)
    img = get_image_from_frame(frame)
    plot.update_img(img)
    update_sources([trajectories, segments], frame_nr)

def bind_cb_obj(trigger):
    def callback(_, old, new):
        trigger.get_source().selected._callbacks = {}
        tap_handler(trigger, old, new)
        trigger.get_source().selected.on_change('indices', bind_cb_obj(trigger))
    return callback

def tap_handler(trigger, old, new):
    if len(new) > 0:
        # The call below triggers the same callback hence the need for the lock
        trigger.update_selected_data(old, new)
        # TODO: Might not be necessary
        table_source.stream(dict(traj_id=[trigger.get_selected_trajectories()[-1]]))
    else:
        clear_trajectories(trigger)

# The lock prevents infinite callbacks as the callback itself changes the value of the trigger
# lock = False
# def tap_handler(trigger, old, new):
#     global lock
#     if not lock:
#         lock = True
#         if len(new) > 0:
#             # The call below triggers the same callback hence the need for the lock
#             trigger.update_selected_data(old, new)
#             # TODO: Might not be necessary
#             table_source.stream(dict(traj_id=[trigger.get_selected_trajectories()[-1]]))
#         else:
#             clear_trajectories(trigger)
#         lock = False

def connect_handler():
    # TODO: Make a connect method that connects a list of ids
    # Can't be part of segments as it doesn't have access to the whole data
    # Creates segments needed to connect the supplied trajectories (ids)
    # Connections will be done in the order of the supplied ids
    ids = trajectories.get_selected_trajectories()
    pairs = [tuple(map(int, x)) for x in zip(ids, ids[1:])]
    for t1_ID, t2_ID in pairs:
        # TODO: Replace the iloc call
        t1 = trajectories.get_trajectory_by_id(t1_ID)
        t2 = trajectories.get_trajectory_by_id(t2_ID)
        # TODO: Consider the append being an internal call. Possibly still return the segment
        segment = segments.create_segment(t1, t2)
        segments.append_segment(segment)
    segments_table_source.data = segments.get_data()
    clear_trajectories(trajectories)
    # TODO: Figure out if there's a better way to update the plot
    slider.trigger('value_throttled', 0, slider.value)

def forward_frames():
    old = slider.value
    slider.value += 30
    slider.trigger('value_throttled', old, slider.value)

def wrong_handler():
    global table_source
    segments.toggle_correct()
    # TODO: Figure out if there's a better way to update the plot
    slider.trigger('value_throttled', 0, slider.value)
    clear_trajectories(segments)
    stats.text = update_stats()
    segments_table_source.data['correct'] = segments.get_data()['correct']     

def jump_to_handler(attr, old, new):
    slider.value = new
    slider.trigger('value_throttled', 0, new)
    
def frame_button_handler(value):
    def callback():
        new = slider.value + value
        if new >= 0 and new <= slider.end:
            slider.value = new
            slider.trigger('value_throttled', 0, slider.value)
    return callback

# def jump_to_frame(frame_nr):
#     def callback(attr, old, new):
#         update_frame(attr, old, new)


# ===============
# Sources setup
# ===============

def setup_sources():
    table_source = ColumnDataSource(data=dict(traj_id=[]))
    segments_table_source = ColumnDataSource(segments.get_data())
    return (table_source, segments_table_source)

table_source, segments_table_source = setup_sources()

# Setup initial frame
update_frame('value', 0, 0)

# ===============
# Widgets / Layout
# ===============

# Slider
slider = Slider(start=0, end=total_frames-1, value=0, step=1)
slider.on_change('value_throttled', update_frame)

# Jump to frame
jump_to = NumericInput(low=1, high=total_frames, placeholder='Jump to specific frame')
jump_to.on_change('value', jump_to_handler)

# Buttons 
btn_size = 75
second_forward = Button(label='+1s', sizing_mode='fixed', height=btn_size, width=btn_size)
second_forward.on_click(frame_button_handler(30))

second_backward = Button(label='-1s', sizing_mode='fixed', height=btn_size, width=btn_size)
second_backward.on_click(frame_button_handler(-30))

next_frame = Button(label='+1 frame', sizing_mode='fixed', height=btn_size, width=btn_size)
next_frame.on_click(frame_button_handler(1))

previous_frame = Button(label='-1 frame', sizing_mode='fixed', height=btn_size, width=btn_size)
previous_frame.on_click(frame_button_handler(-1))

connect = Button(label='Connect')
connect.on_click(connect_handler)

wrong = Button(label='Wrong')
wrong.on_click(wrong_handler)

# Stats
stats = Paragraph(text=update_stats())

# Selection table
selection_table_cols = [TableColumn(field="traj_id", title="Trajectory id")]
selection_table = DataTable(source=table_source, columns=selection_table_cols)

# Segments table
segments_table_cols = [TableColumn(field=c, title=c) for c in segments.get_data().columns]
segments_table = DataTable(source=segments_table_source, columns=segments_table_cols)

# TODO: Find a good place for this 
# Selection callbacks
# trajectories.get_source().selected.on_change('indices', trajectory_tap_handler)
trajectories.get_source().selected.on_change('indices', bind_cb_obj(trajectories))
segments.get_source().selected.on_change('indices', bind_cb_obj(segments))

# Create layout
curdoc().add_root(layout([
    [plot.plot, [slider, jump_to, [second_backward, previous_frame, next_frame, second_forward], connect, wrong]],
    [stats],
    [selection_table, segments_table]
]))
