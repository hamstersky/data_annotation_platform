from random import random

from bokeh.layouts import column, layout
from bokeh.models import Button, Slider, ColumnDataSource, HoverTool, DataTable, TableColumn, Paragraph
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure, curdoc
from bokeh.events import Tap
import cv2
import numpy as np
from segments_data import SegmentsData
from trajectories_data import TrajectoriesData

cap_w = 640
cap_h = 360

cap = cv2.VideoCapture('../videos/video.m4v')
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
trajectories = TrajectoriesData('../data/broken_trajectories.pkl')
segments = SegmentsData('../data/segments.pkl')

# ===============
# Helpers
# ===============

def get_frame(frame_nr):
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_nr)
    _, frame = cap.read()
    return frame

def get_image_from_frame(frame):
    img = frame[::-1, :, ::-1]

    h, w, c = img.shape

    img_orig = np.zeros((h, w), dtype=np.uint32)
    img_view = img_orig.view(dtype=np.uint8).reshape((h, w, 4))
    img_alpha = np.zeros((h, w, 4), dtype=np.uint8)
    img_alpha[:, :, 3] = 255
    img_alpha[:, :, :3] = img
    img_view[:, :, :] = img_alpha
    return img_orig

def update_sources(frame_nr):
    segments.update_data_source(frame_nr)
    trajectories.update_data_source(frame_nr)

def plot_image(img):
    img_plot.data_source.data['image'] = [img]

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
    frame = get_frame(frame_nr)
    img = get_image_from_frame(frame)
    plot_image(img)
    update_sources(frame_nr)

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

# ===============
# Plot setup
# ===============

def setup_plot():
    p = figure(
        tools='pan,box_zoom,wheel_zoom,tap,save,reset',
        active_scroll='wheel_zoom',
        active_tap='auto',
        x_range=(0, cap_w),
        y_range=(0, cap_h)
    )
    p.toolbar.logo = None
    p.grid.visible = False
    p.axis.visible = False
    p.outline_line_width = 0
    p.plot_height = 360
    p.plot_width = 640
    return p

plot = setup_plot()

def setup_sources():
    img_source = ColumnDataSource(data=dict(
        image=[]
    ))

    table_source = ColumnDataSource(data=dict(traj_id=[]))
    segments_table_source = ColumnDataSource(segments.get_data())
    return (img_source, table_source, segments_table_source)

img_source, table_source, segments_table_source = setup_sources()

def setup_renderers():
    img_plot = plot.image_rgba(
        source=img_source,
        image='image',
        x=0,
        y=0,
        dw=cap_w,
        dh=cap_h,
        level='image'
    )

    trajectories_lines = plot.multi_line(
        source=trajectories.get_source(),
        line_color='line_color',
        line_alpha=0.8,
        line_width=2.0,
        line_dash='solid',
        hover_line_width=2.0,
        hover_line_alpha=1.0,
        selection_line_width=4.0,
        selection_line_alpha=1.0,
        # selection_line_color='red',
        nonselection_line_width=2.0,
        nonselection_line_alpha=0.7
    )

    segments_lines = plot.multi_line(
        source=segments.get_source(),
        line_color='line_color',
        line_alpha=0.8,
        line_width=2.0,
        line_dash='solid',
        hover_line_width=2.0,
        hover_line_alpha=1.0,
        selection_line_width=4.0,
        # selection_line_color='black',
        selection_line_alpha=1.0,
        nonselection_line_width=2.0,
        nonselection_line_alpha=0.7
    )

    return (img_plot, trajectories_lines, segments_lines)

img_plot, trajectories_lines, segments_lines = setup_renderers()

plot.add_tools(HoverTool(
    show_arrow=False,
    line_policy='nearest',
    renderers=[trajectories_lines, segments_lines],
    tooltips=[("id", "@id"), ("frame_in", "@frame_in"), ("frame_out", "@frame_out")]
))   

# Setup initial frame
update_frame('value', 1, 1)

# ===============
# Widgets / Layout
# ===============

# Slider
slider = Slider(start=1, end=total_frames, value=1, step=1)
slider.on_change('value_throttled', update_frame)

# Buttons 
forward = Button(label='+30 frames')
forward.on_click(forward_frames)

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
    [plot, [slider, forward, connect, wrong]],
    [stats],
    [selection_table, segments_table]
]))
