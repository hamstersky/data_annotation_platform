import settings
import state
import os
import uuid
import cv2
from segments_data import SegmentsData
from trajectories_data import TrajectoriesData
from trajectory_plot import TrajectoryPlot


def on_session_created(session_context):
    if "uid" in session_context.request._cookies:
        uid = session_context.request._cookies["uid"]
        state.uid = uid
        filename = f"{uid}.pkl"
        path = os.path.join(os.getcwd(), "data", filename)
        if os.path.exists(path):
            settings.segments_path = path
    else:
        state.uid = str(uuid.uuid4())
        settings.segments_path = "./data/segments.pkl"
