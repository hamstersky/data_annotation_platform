from pickle import FRAME
import cv2
import numpy as np
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

cap = cv2.VideoCapture("../videos/video.m4v")
trajectories = TrajectoriesData("../data/broken_trajectories.pkl")
segments = SegmentsData("../data/segments.pkl")
plot = TrajectoryPlot(trajectories, segments)
capture_width = int(cap.get(3))
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
current_minute = 0
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
    slider.start = current_minute * FRAME_INTERVAL
    slider.end = (current_minute + 1) * FRAME_INTERVAL

    # if frame_nr > 0 and frame_nr < total_frames:
    #     global current_minute
    #     if frame_nr > slider.end - 1:
    #         current_minute += 1
    #         update_slider_limits()
    #         slider.value = slider.start + 1
    #     elif frame_nr < slider.start + 1:
    #         current_minute -= 1
    #         update_slider_limits()
    #         slider.value = slider.end - 1


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


def update_frame(attr, old, frame_nr):
    # update_slider(frame_nr)
    frame = get_frame_from_cap(cap, frame_nr)
    img = get_image_from_frame(frame)
    plot.update_img(img)
    update_sources([trajectories, segments], frame_nr)
    clear_trajectories()


def bind_cb_obj(trigger):
    def callback(_, old, new):
        # Temporarily remove callback to prevent infinite triggers as the
        # callback itself changes the value of the trigger
        trigger.get_source().selected._callbacks = {}
        tap_handler(trigger, old, new)
        trigger.get_source().selected.on_change("indices", bind_cb_obj(trigger))

    return callback


def tap_handler(trigger, old, new):
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
        update_sources([trajectories], slider.value)
    update_state()


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
        new_frame = segment["frame_out"]
    update_tables()
    clear_trajectories()
    # TODO: Figure out if there's a better way to update the plot
    # Jump to the frame_out value of the added segment
    slider.trigger("value", 0, int(new_frame))


def label_handler(label):
    def callback():
        global table_source
        segments.set_status(status=label, comments=incorrect_comment.value)
        # TODO: Figure out if there's a better way to update the plot
        slider.trigger("value", 0, slider.value)
        clear_trajectories()
        stats.text = update_stats()
        update_tables()

    return callback


def wrong_handler():
    global table_source
    segments.set_status(status=False, comments=incorrect_comment.value)
    # TODO: Figure out if there's a better way to update the plot
    slider.trigger("value", 0, slider.value)
    clear_trajectories()
    stats.text = update_stats()
    update_tables()


def jump_to_handler(attr, old, new):
    global current_minute
    current_minute = new // 30 // 60
    update_slider_limits()
    slider.value = new
    slider.trigger("value", 0, new)


def frame_button_handler(value):
    def callback():
        new = slider.value + value
        jump_to_handler("", 0, new)

    return callback


def reset_label():
    table = TABLES[tabs.tabs[tabs.active].name]
    indices = table.source.selected.indices
    ids = []
    for i in indices:
        ids.append(table.source.data["id"][i])
    segments.set_status(status=None, comments=[], ids=ids)
    table.source.selected._callbacks = {}
    table.source.selected.indices = []
    table.source.selected.on_change("indices", table_click_handler(table))
    update_tables()
    stats.text = update_stats()
    slider.trigger("value", 0, slider.value)


def table_click_handler(table):
    def callback(_, old, new):
        if new:
            frame = table.source.data["frame_in"][new[0]]
            jump_to_handler("", 0, frame)

    return callback


def tab_switch(attr, old, new):
    reset_tables = ["wrong_segments", "correct_segments", "new_segments"]
    reset_label_btn.visible = tabs.tabs[new].name in reset_tables
    tab_description.text = descriptions[tabs.tabs[new].name]


def next_interest_handler():
    frame_ins = segments.get_source().data["frame_in"]
    frame = max(frame_ins) if frame_ins else slider.value
    next_frame = segments.find_next_interest(int(frame))
    jump_to_handler("", 0, next_frame)


def update_slider(value):
    def callback():
        global current_minute
        if current_minute + value >= 0:
            current_minute += value
            update_slider_limits()
            slider.value = slider.end if value < 0 else slider.start

    return callback


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
next_min_btn.on_click(update_slider(1))
prev_min_btn = Button(label="-1min", width=50)
prev_min_btn.on_click(update_slider(-1))
slider_component = [
    Paragraph(text="Use the slider to change frames:"),
    [prev_min_btn, slider, next_min_btn],
]

# Jump to frame
jump_to = NumericInput(
    low=1,
    high=total_frames,
    placeholder="Jump to specific frame",
    width=plot.plot.width,
)
jump_to.on_change("value", jump_to_handler)

# Buttons
btn_size = 75
second_forward = Button(
    label="+1s", sizing_mode="fixed", height=btn_size, width=btn_size
)
second_forward.on_click(frame_button_handler(30))

second_backward = Button(
    label="-1s", sizing_mode="fixed", height=btn_size, width=btn_size
)
second_backward.on_click(frame_button_handler(-30))

next_frame = Button(
    label="+1 frame", sizing_mode="fixed", height=btn_size, width=btn_size
)
next_frame.on_click(frame_button_handler(1))

previous_frame = Button(
    label="-1 frame", sizing_mode="fixed", height=btn_size, width=btn_size
)
previous_frame.on_click(frame_button_handler(-1))

next_interest = Button(
    label="Jump to next interest", sizing_mode="fixed", height=btn_size, width=btn_size
)
next_interest.on_click(next_interest_handler)

btn_settings = {"disabled": True}
connect_btn = Button(label="Connect", **btn_settings)
connect_btn.on_click(connect_handler)

# Restore segment button
reset_label_btn = Button(label="Reset label", visible=False)
reset_label_btn.on_click(reset_label)

# Wrong connection component
incorrect_btn = Button(label="Incorrect segment", **btn_settings)
incorrect_btn.on_click(label_handler(False))
incorrect_options = ["reason1", "reason2"]
incorrect_comment = MultiChoice(
    options=incorrect_options,
    visible=False,
    title="Select the reason(s) why the connection is incorrect by clicking on the input box.",
)

correct_btn = Button(label="Correct segment", **btn_settings)
correct_btn.on_click(label_handler(True))

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
    "indices", table_click_handler(incorrect_segments_table)
)

# Candidates table
# TODO: Add euclidean distance
trajectories_table = DataTable(source=trajectories.get_source(), **table_params)

# New segments table
new_segments_table_source = ColumnDataSource(segments.get_new_segments())
new_segments_table = DataTable(source=new_segments_table_source, **table_params)
new_segments_table_source.selected.on_change(
    "indices", table_click_handler(new_segments_table)
)

# Correct segments table
correct_segments_table_source = ColumnDataSource(segments.get_segments_by_status(True))
correct_segments_table = DataTable(source=correct_segments_table_source, **table_params)
correct_segments_table_source.selected.on_change(
    "indices", table_click_handler(correct_segments_table)
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
tabs.on_change("active", tab_switch)

# TODO: Find a good place for this
# Selection callbacks
# trajectories.get_source().selected.on_change('indices', trajectory_tap_handler)
trajectories.get_source().selected.on_change("indices", bind_cb_obj(trajectories))
segments.get_source().selected.on_change("indices", bind_cb_obj(segments))


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
update_frame("value", 0, 1)

# Create layout
curdoc().add_root(
    layout(
        [
            [
                plot.plot,
                [tab_description, tabs, reset_label_btn, *labeling_controls],
            ],
            *slider_component,
            jump_to,
            [
                second_backward,
                previous_frame,
                next_frame,
                second_forward,
                next_interest,
            ],
        ]
    )
)
