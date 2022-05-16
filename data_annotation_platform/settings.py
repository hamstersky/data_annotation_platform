import pathlib

project_path = pathlib.Path(__file__).parent.absolute()
segments_path = f"{project_path}/data/segments.pkl"
trajectories_path = f"{project_path}/data/broken_trajectories.pkl"
FRAME_INTERVAL = 1800
video_path = f"{project_path}/video/video.mp4"
