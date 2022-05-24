from random import random

from bokeh.layouts import column
from bokeh.models import Button, Slider, ColumnDataSource, HoverTool, DataTable, TableColumn, Paragraph
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure, curdoc
from bokeh.events import Tap
import cv2
import pandas as pd
import numpy as np

# create a plot and style its properties
cap_w = 640
cap_h = 360
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

cap = cv2.VideoCapture('../videos/video.m4v')
ret = True
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
data = pd.read_pickle('../data/broken_trajectories.pkl')
data.reset_index(inplace=True)
segments = pd.read_pickle('../data/segments.pkl')
segments.reset_index(inplace=True)
segments = segments[['id', 'xs', 'ys', 'class', 'frame_in', 'frame_out']]
# Add column for keeping track of correct / incorrect connections
segments['correct'] = True

def update_frame(attr, old, new):
    frame_nr = new
    frame = get_frame(frame_nr)
    img = get_image_from_frame(frame)
    plot_image(img)
    get_data_range(frame_nr)

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

def get_data_range(frame_nr):
    global l
    global segments_lines
    global segments
    global data
    subset = data[(frame_nr >= data['frame_in']) & (frame_nr <= data['frame_out'] + 400)]
    subset_segments = segments[(frame_nr >= segments['frame_in']) & (frame_nr <= segments['frame_out'] + 400) & segments['correct'] == True]

    N = subset.shape[0]

    colors = ['red', 'magenta', 'green', 'orange', 'cyan', 'yellow', 'blue', 'black', 'navy']
    # Store list of colors for CustomJS callback
    default_lc = [colors[int(i)] for i in subset['class']]

    # Merge two dictionaries
    l.data_source.data = {
        **subset.to_dict(orient='list'),
        **{
            'line_color': default_lc,
            'line_alpha': [0.8] * N,
            'line_width': [2.0] * N,
            'line_dash': ['solid'] * N  # 'solid', 'dashed', 'dotted', 'dotdash', 'dashdot'
        }
    }

    N = subset_segments.shape[0]
    segment_colors = ['blue' for _ in subset_segments['class']]
    segments_lines.data_source.data = {
        **subset_segments.to_dict(orient='list'),
        **{
            'line_color': segment_colors,
            'line_alpha': [0.8] * N,
            'line_width': [2.0] * N,
            'line_dash': ['solid'] * N  # 'solid', 'dashed', 'dotted', 'dotdash', 'dashdot'
        }
    }

def plot_image(img):
    img_plot.data_source.data['image'] = [img]

img_source = ColumnDataSource(data=dict(
    image=[]
))

img_plot = p.image_rgba(
    source=img_source,
    image='image',
    x=0,
    y=0,
    dw=cap_w,
    dh=cap_h,
    level='image'
)    

slider = Slider(start=1, end=total_frames, value=1, step=1)
slider.on_change('value_throttled', update_frame)

# Set up initial plot
source = ColumnDataSource(data={
    'xs': [],
    'ys': [],
    'line_color': [],
    'line_alpha': [],
    'line_width': [],
    'line_dash': []
})

segments_source = ColumnDataSource(data={
    'xs': [],
    'ys': [],
    'line_color': [],
    'line_alpha': [],
    'line_width': [],
    'line_dash': []
})

l = p.multi_line(
    source=source,
    line_color='line_color',
    line_alpha='line_alpha',
    line_width='line_width',
    line_dash='line_dash',
    hover_line_width=2.0,
    hover_line_alpha=1.0,
    selection_line_width=3.0,
    selection_line_alpha=1.0,
    selection_line_color='red',
    nonselection_line_width=2,
    nonselection_line_alpha=0.8
)

segments_lines = p.multi_line(
    source=segments_source,
    line_color='line_color',
    line_alpha='line_alpha',
    line_width='line_width',
    line_dash='line_dash',
    hover_line_width=2.0,
    hover_line_alpha=1.0,
    selection_line_width=2.0,
    selection_line_alpha=1.0,
    # nonselection_line_width=0.8,
    # nonselection_line_alpha=0.3
)

p.add_tools(HoverTool(
    show_arrow=False,
    line_policy='nearest',
    renderers=[l, segments_lines],
    tooltips=[("id", "@id"), ("frame_in", "@frame_in"), ("frame_out", "@frame_out")]
))

p.plot_height = 360
p.plot_width = 640
update_frame('value', 1, 1)



lock = False
def tap_handler(attr, old, new):
    global table_source
    global lock
    if not lock:
        lock = True
        if len(new) > 0:
            traj_id = source.data['id'][new[0]]
            table_source.stream(dict(traj_id=[traj_id]))
            update_selection(old, new)
        else:
            clear_trajectories()
        lock = False

def segments_tap_handler(attr, old, new):
    global table_source
    if len(new) > 0:
        traj_id = segments_source.data['id'][new[0]]
        table_source.stream(dict(traj_id=[traj_id]))

# p.on_event(Tap, tap_handler)
# l.data_source.on_change('tap', tap_handler)
source.selected.on_change('indices', tap_handler)
segments_source.selected.on_change('indices', segments_tap_handler)
columns = [
    TableColumn(field="traj_id", title="Trajectory id"),
]
table_source = ColumnDataSource(data=dict(traj_id=[]))
table = DataTable(source=table_source, columns=columns)
connect = Button(label='Connect')
forward = Button(label='+30 frames')
wrong = Button(label='Wrong')

def connect_handler():
    global table_source
    global segments
    # TODO: Add support for connecting multiple trajectories
    traj1_id = table_source.data['traj_id'][0]
    traj2_id = table_source.data['traj_id'][1]
    # TODO: Copying might not be needed
    traj1 = data[data['id'] == traj1_id].copy()
    traj2 = data[data['id'] == traj2_id].copy()
    traj_data = {
        'id': traj1['id'] + .1,
        'class': 8,
        'xs': [[*traj1['x1'].values, *traj2['x0'].values]],
        'ys': [[*traj1['y1'].values, *traj2['y0'].values]],
        'frame_in': traj1['frame_out'].values,
        'frame_out': traj2['frame_in'].values,
        'correct': True
    }
    traj_data = pd.DataFrame(traj_data)
    segments = pd.concat([segments, traj_data])
    segments_table_source.data = segments
    clear_trajectories()
    # TODO: Figure out if there's a better way to update the plot
    slider.trigger('value_throttled', 0, slider.value)

def forward_frames():
    old = slider.value
    slider.value += 30
    slider.trigger('value_throttled', old, slider.value)

def wrong_handler():
    global table_source
    traj_id = table_source.data['traj_id'][0]
    segments.loc[segments['id'] == traj_id, 'correct'] = False
    # TODO: Figure out if there's a better way to update the plot
    slider.trigger('value_throttled', 0, slider.value)
    clear_trajectories()
    par.text = update_stats()
    segments_table_source.data['correct'] = segments['correct']
    
def clear_trajectories():
    table_source.data['traj_id'] = []
    update_selection([], [])

def update_selection(old, new):
    if new == []:
        source.selected.indices = []
    else:
        source.selected.indices = old + new

connect.on_click(connect_handler)
forward.on_click(forward_frames)
wrong.on_click(wrong_handler)

def update_stats():
    total = segments.shape[0]
    correct_count = segments[segments['correct']==True].shape[0]
    incorrect_count = segments[segments['correct']==False].shape[0]
    ratio = correct_count / total
    return f'''Correct: {correct_count}
    Incorrect: {incorrect_count}
    Ratio: {ratio}
    '''

par = Paragraph(text=update_stats())

columns2 = [TableColumn(field=c, title=c) for c in segments.columns]
segments_table_source = ColumnDataSource(segments)
segments_table = DataTable(source=segments_table_source, columns=columns2)

curdoc().add_root(column(slider, forward, p, table, connect, wrong, par, segments_table))