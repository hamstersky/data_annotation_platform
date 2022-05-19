from app.segments import Segments
from app.trajectories import Trajectories
from ui.trajectory_plot import TrajectoryPlot
import cv2

segments: Segments
trajectories: Trajectories
current_frame: int
current_minute: int
total_frames: int
uid: str
cap: cv2.VideoCapture
plot: TrajectoryPlot
