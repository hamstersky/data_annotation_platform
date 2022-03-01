from random import random

from bokeh.layouts import column
from bokeh.models import Button, Slider, ColumnDataSource, HoverTool, CustomJS
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

data = pd.read_pickle('../data/broken_trajectories.pkl')
cap = cv2.VideoCapture('../videos/video.m4v')
ret = True
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
data = pd.read_pickle('../data/broken_trajectories.pkl')

def update_frame(attr, old, new):
    frame_nr = old
    frame = get_frame(frame_nr)
    img = get_image_from_frame(frame)
    plot_image(img)
    get_data_range(frame_nr)

def get_frame(frame_nr):
    _, frame = cap.read()
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_nr)
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
    global data
    subset = data[(frame_nr >= data['frame_in']) & (frame_nr <= data['frame_out'] + 900)]

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

def plot_image(img):
    global p
    source = ColumnDataSource(data=dict(
        image=[img]
    ))

    p.image_rgba(
        source=source,
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

l = p.multi_line(
    source=source,
    line_color='line_color',
    line_alpha='line_alpha',
    line_width='line_width',
    line_dash='line_dash',
    hover_line_width=2.0,
    hover_line_alpha=1.0,
    selection_line_width=2.0,
    selection_line_alpha=1.0,
    nonselection_line_width=0.8,
    nonselection_line_alpha=0.3
)

p.add_tools(HoverTool(
    show_arrow=False,
    line_policy='nearest',
    renderers=[l],
    tooltips=[("id", "@id")]
))

p.plot_height = 360
p.plot_width = 640
update_frame('value', 1, 1)


# p.js_on_event('tap', callback)
# def tap_handler(event):
#     selected = l.data_source.selected.indices
#     print(selected)

def tap_handler(attr, old, new):
    # selected = source.selected.indices
    # source.selected.indices = old + new
    # selected = source.selected.indices
    print(source.data['id'][new[0]])
    # print(new[0])
    # print(source.data)
    # print(attr)
    # print(old)

# p.on_event(Tap, tap_handler)
# l.data_source.on_change('tap', tap_handler)
source.selected.on_change('indices', tap_handler)

# put the button and plot in a layout and add to the document
curdoc().add_root(column(slider, p))