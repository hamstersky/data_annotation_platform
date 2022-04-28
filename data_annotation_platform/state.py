from segments_data import SegmentsData
from trajectories_data import TrajectoriesData
from bokeh.models import Slider, DataTable
import cv2
import settings

segments: SegmentsData
trajectories: TrajectoriesData
current_frame = 0
current_minute = 0
total_frames = 0
uid = 0
slider: Slider
active_table: DataTable
cap: cv2.VideoCapture
plot = None
