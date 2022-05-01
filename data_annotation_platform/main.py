import cv2
from bokeh.layouts import column, row
from bokeh.plotting import curdoc
from helpers import clear_trajectories, update_state, update_frame, update_sources
from segments_data import SegmentsData
from trajectories_data import TrajectoriesData
from trajectory_plot import TrajectoryPlot
import settings
import session
import state
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
