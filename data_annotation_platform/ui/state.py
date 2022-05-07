from app.segments import Segments
from app.trajectories import Trajectories
from bokeh.models import DataTable
import cv2
import settings

segments: Segments
trajectories: Trajectories
current_frame: int
current_minute: int
total_frames: int
uid: str
cap: cv2.VideoCapture
plot = None
