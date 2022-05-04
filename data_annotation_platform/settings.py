import pathlib

project_path = pathlib.Path(__file__).parent.absolute()
print(project_path)
segments_path = f"{project_path}/data/segments.pkl"
trajectories_path = f"{project_path}/data/broken_trajectories.pkl"
FRAME_INTERVAL = 1800
