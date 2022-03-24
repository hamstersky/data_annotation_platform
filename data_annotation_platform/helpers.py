import cv2
import numpy as np
from segments_data import SegmentsData
from trajectories_data import TrajectoriesData

# ===============
# Helpers
# ===============

def get_frame_from_cap(cap, frame_nr):
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_nr)
    _, frame = cap.read()
    return frame

def get_image_from_frame(frame):
    img = frame[::-1, :, ::-1]

    h, w, _ = img.shape

    img_orig = np.zeros((h, w), dtype=np.uint32)
    img_view = img_orig.view(dtype=np.uint8).reshape((h, w, 4))
    img_alpha = np.zeros((h, w, 4), dtype=np.uint8)
    img_alpha[:, :, 3] = 255
    img_alpha[:, :, :3] = img
    img_view[:, :, :] = img_alpha
    return img_orig

def update_sources(sources, frame_nr):
    for source in sources:
        source.update_data_source(frame_nr)