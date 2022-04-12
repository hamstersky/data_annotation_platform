import pandas as pd
from data import Data


class TrajectoriesData(Data):
    def __init__(self, source_path):
        super().__init__(source_path)

    def get_frame_subset(self, frame_nr):
        return self.data[
            (frame_nr >= self.data["frame_in"])
            & (frame_nr <= self.data["frame_out"] + 400)
        ]

    # TODO: Is this method needed?
    def get_candidates(self, traj_id):
        t1 = self.data.iloc[traj_id]
        # TODO: What about other classes?
        return self.data[
            (self.data.index == traj_id)
            | (self.data["frame_in"] >= t1["frame_out"])
            & (self.data["frame_out"] <= t1["frame_out"] + 900)
        ]

    def update_source_candidates(self, traj_id):
        subset = self.get_candidates(traj_id)
        colors = [
            "red",
            "magenta",
            "green",
            "orange",
            "cyan",
            "yellow",
            "blue",
            "black",
            "navy",
        ]
        line_colors = ["brown" for i in subset["class"]]
        # Keep the selected trajectory's color corresponding to it's class
        line_colors[0] = colors[int(self.data.iloc[traj_id]["class"])]
        # TODO: Better way to include the id / index?
        self.source.data = {
            **subset.to_dict(orient="list"),
            "id": subset.index.values,
            "line_color": line_colors,
        }
