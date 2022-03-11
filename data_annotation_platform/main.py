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

def clear_trajectories():
    table_source.data['traj_id'] = []
    update_selection([], [])

def update_selection(old, new):
    if new == []:
        trajectories.source.selected.indices = []
    else:
        trajectories.source.selected.indices = old + new

def update_stats():
    total = segments.data.shape[0]
    correct_count = segments.data[segments.data['correct']==True].shape[0]
    incorrect_count = segments.data[segments.data['correct']==False].shape[0]
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

lock = False
def tap_handler(attr, old, new):
    global table_source
    global lock
    if not lock:
        lock = True
        if len(new) > 0:
            traj_id = trajectories.source.data['id'][new[0]]
            table_source.stream(dict(traj_id=[traj_id]))
            update_selection(old, new)
        else:
            clear_trajectories()
        lock = False

def segments_tap_handler(attr, old, new):
    global table_source
    if len(new) > 0:
        traj_id = segments.source.data['id'][new[0]]
        table_source.stream(dict(traj_id=[traj_id]))

def connect_handler():
    global table_source
    global segments
    # TODO: Make a connect method that connects a list of ids
    # Can't be part of segments as it doesn't have access to the whole data
    # segments.connect(table_source.data['traj_id'])
    ids = table_source.data['traj_id']
    pairs = zip(ids, ids[1:])
    pairs = [tuple(map(int, x)) for x in pairs]
    for t1_ID, t2_ID in pairs:
        t1 = trajectories.data.iloc[t1_ID]
        t2 = trajectories.data.iloc[t2_ID]
        segment = segments.create_segment(t1, t2)
        segments.append_segment(segment)
    segments_table_source.data = segments.data
    clear_trajectories()
    # TODO: Figure out if there's a better way to update the plot
    slider.trigger('value_throttled', 0, slider.value)

def forward_frames():
    old = slider.value
    slider.value += 30
    slider.trigger('value_throttled', old, slider.value)

def wrong_handler():
    global table_source
    # TODO: Make it possible to handle multiple wrong connections
    traj_id = table_source.data['traj_id'][0]
    segments.toggle_correct(traj_id)
    # TODO: Figure out if there's a better way to update the plot
    slider.trigger('value_throttled', 0, slider.value)
    clear_trajectories()
    stats.text = update_stats()
    segments_table_source.data['correct'] = segments.data['correct']     

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

    # TODO: This initial definition might not be needed? At least not the keys
    # trajectories_source = ColumnDataSource(data={
    #     'xs': [],
    #     'ys': [],
    #     'line_color': [],
    #     'line_alpha': [],
    #     'line_width': [],
    #     'line_dash': []
    # })
    trajectories_source = ColumnDataSource()

    segments_source = ColumnDataSource()
    segments_source.selected.on_change('indices', segments_tap_handler)

    table_source = ColumnDataSource(data=dict(traj_id=[]))
    segments_table_source = ColumnDataSource(segments.data)
    return (img_source, trajectories_source, segments_source, table_source, segments_table_source)

img_source, trajectories_source, segments_source, table_source, segments_table_source = setup_sources()

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
        source=trajectories.source,
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
        source=segments.source,
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

# Selection callbacks
# trajectories_source.selected.on_change('indices', tap_handler)
# segments_source.selected.on_change('indices', segments_tap_handler)

# Segments table
segments_table_cols = [TableColumn(field=c, title=c) for c in segments.data.columns]
segments_table = DataTable(source=segments_table_source, columns=segments_table_cols)

# TODO: Find a good place for this 
trajectories.source.selected.on_change('indices', tap_handler)
segments.source.selected.on_change('indices', segments_tap_handler)

# Create layout
curdoc().add_root(layout([
    [plot, [slider, forward, connect, wrong]],
    [stats],
    [selection_table, segments_table]
]))
