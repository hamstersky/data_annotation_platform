import cv2

from app.segments import Segments
from app.trajectories import Trajectories
from ui.trajectory_plot import TrajectoryPlot

# This file defines the state of the application that needs to be shared between
# the different components

segments: Segments
trajectories: Trajectories
current_frame: int
current_minute: int
total_frames: int
uid: str
cap: cv2.VideoCapture
plot: TrajectoryPlot
