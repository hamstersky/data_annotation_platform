import cv2
from bokeh.layouts import column, row
from bokeh.plotting import curdoc

import settings
import ui.state as state
from app.helpers import handle_tap, refresh_frame
from app.segments import Segments
from app.trajectories import Trajectories
from ui.data_export import create_download_btn
from ui.labeling import create_labeling_controls
from ui.navigation import create_navigation
from ui.session import create_save_progress_btn
from ui.slider import create_slider
from ui.tables import create_tabs
from ui.trajectory_plot import TrajectoryPlot


def initialize_state():
    """Initializes the state of the application."""

    state.segments = Segments(settings.segments_path)
    state.segments.current_frame_view.selected.on_change(
        "indices", handle_tap(state.segments)
    )
    state.trajectories = Trajectories(settings.trajectories_path)
    state.trajectories.current_frame_view.selected.on_change(
        "indices", handle_tap(state.trajectories)
    )
    state.current_frame = 0
    state.current_minute = 0
    state.cap = cv2.VideoCapture(settings.video_path)
    state.total_frames = int(state.cap.get(cv2.CAP_PROP_FRAME_COUNT))
    state.plot = TrajectoryPlot(state.trajectories, state.segments)
    refresh_frame("", 1, 1)


initialize_state()

# == Create and add all UI components ==
save_btn = create_save_progress_btn()
download_btn = create_download_btn()
slider_row = row(create_slider())
jump_to, *btns = create_navigation()
navigation_btns = row(*btns)
navigation = column(slider_row, jump_to, navigation_btns)
table_tabs = column(*create_tabs())
labeling_controls = column(
    table_tabs, *create_labeling_controls(), save_btn, download_btn
)
curdoc().add_root(row(state.plot.plot, labeling_controls))
curdoc().add_root(navigation)
