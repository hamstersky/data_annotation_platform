import pandas as pd

from app.data_source import DataSource


class Trajectories(DataSource):
    """
    Class representing a data source specifically for (broken) trajectories.
    Inherits from DataSource class.

    This class doesn't introduce any new attributes.
    """

    def __init__(self, source_path):
        super().__init__(source_path)

    def get_frame_subset(self, frame_nr):
        """Returns a subset of data relevant for the given frame."""

        return self.data[
            (frame_nr >= self.data["frame_in"])
            & (frame_nr <= self.data["frame_out"] + 400)
        ]

    def get_candidates(self, traj_id):
        """
        Returns a subset of trajectories that are a good candidate for the trajectory with the given ID.
        The only factor considered in the evaluation of candidates is time.
        Only trajectories that start within 900 frames are considered candidates.
        """

        t1 = self.data.iloc[traj_id]
        return self.data[
            (self.data.index == traj_id)
            | (self.data["frame_in"] >= t1["frame_out"])
            & (self.data["frame_out"] <= t1["frame_out"] + 900)
        ]

    def show_candidates(self, traj_id):
        """Updates the current frame view with candidate trajectories."""

        subset = self.get_candidates(traj_id)
        line_colors = ["brown" for _ in subset["class"]]
        # Keep the selected trajectory's color green
        line_colors[0] = "green"
        self.current_frame_view.data = {
            **subset.to_dict(orient="list"),
            "id": subset.index.values,
            "line_color": line_colors,
        }
