from bokeh.layouts import column, layout
from bokeh.models import Button, Slider, ColumnDataSource, Paragraph, DataTable, TableColumn, PreText, NumericInput, CustomJS, MultiSelect
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure, curdoc
from bokeh.events import Tap
import cv2
import numpy as np
from segments_data import SegmentsData
from trajectories_data import TrajectoriesData
from trajectory_plot import TrajectoryPlot
from helpers import get_frame_from_cap, get_image_from_frame, update_sources

cap = cv2.VideoCapture('../videos/video.m4v')
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
    return f"""
Number of correct segments: {segments.get_correct_segment_count()}
Number of incorrect segments: {segments.get_incorrect_segment_count()}
Accuracy: {"{:.2f}".format(segments.get_correct_incorrect_ratio() * 100)}%
    """

def update_tables():
    segments_table_source.data = segments.get_data()
    # TODO: Find better way for keeping track of the original index
    # At least remove the direct access to the index
    incorrect_segments_table_source.data = segments.get_incorrect_segments()
    incorrect_segments_table_source.data['original_index'] = segments.get_incorrect_segments().index
    new_segments_table_source.data = segments.get_new_segments()

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
        # Temporarily remove callback to prevent infinite triggers as the
        # callback itself changes the value of the trigger
        trigger.get_source().selected._callbacks = {}
        tap_handler(trigger, old, new)
        trigger.get_source().selected.on_change('indices', bind_cb_obj(trigger))
    return callback

def tap_handler(trigger, old, new):
    if len(new) > 0:
        selected_traj_id = trigger.get_id_of_selected_trajectory(new[0])
        if isinstance(trigger, TrajectoriesData) and not trigger.get_selected_trajectories():
            trigger.update_source_candidates(selected_traj_id)
            # Needed so that the first trajectory remains the selected one
            trigger.update_selected_data(old, [0])
        else:
            trigger.update_selected_data(old, new)
        table_source.stream(dict(traj_id=[selected_traj_id]))
    else:
        clear_trajectories(trigger)
        # TODO: Other way to get the slider value? Maybe consider the current
        # frame to be some global variable or instance variable of plot class or
        # some other new class?
        # Restores state without candidate trajectories
        update_sources([trajectories], slider.value)

def connect_handler():
    # TODO: Make a connect method that connects a list of ids
    # Can't be part of segments as it doesn't have access to the whole data
    # Creates segments needed to connect the supplied trajectories (ids)
    # Connections will be done in the order of the supplied ids
    ids = trajectories.get_selected_trajectories()
    pairs = [tuple(map(int, x)) for x in zip(ids, ids[1:])]
    new_frame = 0
    for t1_ID, t2_ID in pairs:
        # TODO: Replace the iloc call
        t1 = trajectories.get_trajectory_by_id(t1_ID)
        t2 = trajectories.get_trajectory_by_id(t2_ID)
        # TODO: Consider the append being an internal call. Possibly still return the segment
        segment = segments.create_segment(t1, t2)
        segments.append_segment(segment)
        new_frame = segment['frame_out']
    update_tables()
    clear_trajectories(trajectories)
    # TODO: Figure out if there's a better way to update the plot
    # Jump to the frame_out value of the added segment
    slider.trigger('value_throttled', 0, int(new_frame))

def forward_frames():
    old = slider.value
    slider.value += 30
    slider.trigger('value_throttled', old, slider.value)

def wrong_handler():
    global table_source
    segments.toggle_correct(incorrect_comment.value)
    # TODO: Figure out if there's a better way to update the plot
    slider.trigger('value_throttled', 0, slider.value)
    clear_trajectories(segments)
    stats.text = update_stats()
    update_tables()

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

def restore_connection(attr, old, new):
    ids = [incorrect_segments_table_source.data['original_index'][new[0]]]
    segments.toggle_correct([], ids)
    incorrect_segments_table_source.selected._callbacks = {}
    incorrect_segments_table_source.selected.indices = []
    incorrect_segments_table_source.selected.on_change('indices', restore_connection)
    update_tables()
    stats.text = update_stats()
    slider.trigger('value_throttled', 0, slider.value)

def table_click_handler(table):
    def callback(_, old, new):
        frame = table.source.data['frame_in'][new[0]]
        slider.value = frame
        slider.trigger('value_throttled', 0, slider.value)
    return callback


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
# For preventing going over the last frame
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
slider = Slider(start=0, end=total_frames-1, value=0, step=1)
slider.on_change('value_throttled', update_frame)
slider_component = [
    Paragraph(text="Use the slider to change frames:"),
    slider
]

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
connect_component = [
    Paragraph(text='Select one or more trajectories to connect them with the button below:'),
    connect
]

# Wrong connection component
incorrect_btn = Button(label='Incorrect segment')
incorrect_btn.on_click(wrong_handler)
incorrect_options = ['none of the below', 'reason1', 'reason2']
incorrect_comment = MultiSelect(options=incorrect_options, value=[], size=3)
incorrect_component = [
    Paragraph(text='Select an incorrect connection and optionally select the reason why the connection is incorrect. You can select multiple by holding CTRL: '),
    incorrect_comment,
    incorrect_btn
]

# Stats
stats = PreText(text=update_stats())

# Selection table
label = Paragraph(text='Currently selected trajectories: ')
selection_table_cols = [TableColumn(field="traj_id", title="Trajectory id")]
selection_table = DataTable(source=table_source, columns=selection_table_cols, width=300)

# Segments table
segments_table_cols = [TableColumn(field=c, title=c) for c in segments.get_data().columns]
segments_table = DataTable(source=segments_table_source, columns=segments_table_cols)

# Incorrect segments component
incorrect_segments_table_source = ColumnDataSource(segments.get_incorrect_segments())
incorrect_segments_table_source.selected.on_change('indices', restore_connection)
incorrect_segments_table_cols = ['xs', 'ys', 'class', 'frame_in', 'frame_out', 'comments']
incorrect_segments_table_cols = [TableColumn(field=c, title=c) for c in incorrect_segments_table_cols]
incorrect_segments_table = DataTable(source=incorrect_segments_table_source, columns=incorrect_segments_table_cols, width=500)
incorrect_segments_component = [
    Paragraph(text="Wrong connections. Click on a row to restore it:"),
    incorrect_segments_table
]

# Candidates table
# TODO: Add euclidean distance
trajectories_table_cols = ['id', 'class', 'frame_in', 'frame_out']
trajectories_table_cols = [TableColumn(field=c, title=c) for c in trajectories_table_cols]
trajectories_table = DataTable(source=trajectories.get_source(), columns=trajectories_table_cols, width=500, index_position=None)
trajectories_component = [
    Paragraph(text="Trajectories/candidates on current frame. Click a trajectory to select it:"),
    trajectories_table
]

# New segments table
# TODO: Duplication: Extracting columns is done many times in the same way
new_segments_table_source = ColumnDataSource(segments.get_new_segments())
new_segments_table_cols = ['ID', 'class', 'frame_in', 'frame_out']
new_segments_table_cols = [TableColumn(field=c, title=c) for c in new_segments_table_cols]
new_segments_table = DataTable(source=new_segments_table_source, columns=new_segments_table_cols, width=500, index_position=None)
new_segments_table_source.selected.on_change('indices', table_click_handler(new_segments_table))
new_segments_component = [
    Paragraph(text="Manually created segments:"),
    new_segments_table
]

# TODO: Find a good place for this 
# Selection callbacks
# trajectories.get_source().selected.on_change('indices', trajectory_tap_handler)
trajectories.get_source().selected.on_change('indices', bind_cb_obj(trajectories))
segments.get_source().selected.on_change('indices', bind_cb_obj(segments))

# Create layout
curdoc().add_root(layout([
    [plot.plot, [*slider_component, jump_to, [second_backward, previous_frame, next_frame, second_forward], stats]],
    [connect_component, incorrect_component],
    [label],
    [selection_table,
    incorrect_segments_component,
    # segments_table,
    ],
    *trajectories_component,
    *new_segments_component
]))
