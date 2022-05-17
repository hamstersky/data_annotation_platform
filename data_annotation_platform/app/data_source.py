import pandas as pd
from bokeh.models import ColumnDataSource


class DataSource:
    """
    Superclass representing a data source such as trajectories or segments.

    Args:
        source_path: Location of the Pickle file to be loaded as the data source.

    Attributes:
        data: Data loaded from file as a Pandas DataFrame.
        views: List of views extracted from the data. Each of this views is an attribute on its own.
        selected_ids: IDs of data points currently selected from the UI.
    """

    def __init__(self, source_path):
        self.data = pd.read_pickle(source_path)
        self.views = []
        self._register_view("current_frame_view", {})
        self.selected_ids = []

    def _register_view(self, name, data):
        """
        Helper method for registering views.
        """
        setattr(self, name, ColumnDataSource(data))
        self.views.append(getattr(self, name))

    def get_frame_subset(self, frame_nr):
        """
        Abstract method. Returns a subset of data for a given frame. Implementation depends on the data source.
        """
        raise NotImplementedError

    def update_views(self, frame_nr):
        """
        Updates the current frame view with data for the given frame.
        """
        subset = self.get_frame_subset(frame_nr)
        line_style = self.get_line_style(subset)
        self.current_frame_view.data = {
            **subset.to_dict(orient="list"),
            "id": subset.index.values,
            **line_style,
        }

    def get_line_style(self, subset):
        """
        Returns default styles for lines according to their class.
        """
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
        line_color = [colors[int(i)] for i in subset["class"]]
        line_dash = ["solid" for i in subset["class"]]
        return dict(line_color=line_color, line_dash=line_dash)

    def connect(self, t1_id, t2_id):
        """Returns a new segment by connecting two trajectories with given IDs."""
        t1 = self.data.iloc[t1_id]
        t2 = self.data.iloc[t2_id]
        connection = pd.DataFrame(
            {
                "class": t1["class"],
                "xs": [[t1["xs"][-1], t2["xs"][0]]],
                "ys": [[t1["ys"][-1], t2["ys"][0]]],
                "frame_in": t1["frame_out"],
                "frame_out": t2["frame_in"],
                "correct": True,
                "new": True,
            }
        )
        return connection

    def get_id_of_selected_trajectory(self, selected_index):
        """Returns the true ID of a trajectory given its selection index in the view."""
        return self.current_frame_view.data["id"][selected_index]

    def update_selected_data(self, old, new):
        """
        Updates the currently selected data points.
        It is necessary for overwritting the default Bokeh behavior when selecting data points.

        Arguments:
            old: the indices of already selected data in the view
            new: the index of the newly selected data point in the view
        """
        if new == []:
            # If the new selection is empty, reset all views
            self.selected_ids = []
            for view in self.views:
                view.selected.indices = []
        else:
            # Else, add the new selection to the already selected ids and update the view
            traj_id = self.get_id_of_selected_trajectory([new[0]])
            self.selected_ids.append(traj_id)
            self.current_frame_view.selected.indices = old + new

    def export_data(self, path):
        """Saves the data into a Pickle file."""
        self.data.to_pickle(f"{path}.pkl")
