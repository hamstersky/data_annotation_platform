from segments_data import SegmentsData
from trajectories_data import TrajectoriesData
from bokeh.models import DataTable
import cv2
import settings

segments: SegmentsData
trajectories: TrajectoriesData
current_frame: int
current_minute: int
total_frames: int
uid: str
active_table: DataTable
cap: cv2.VideoCapture
plot = None
