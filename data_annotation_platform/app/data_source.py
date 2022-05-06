import pandas as pd
from bokeh.models import ColumnDataSource


class DataSource:
    def __init__(self, source_path):
        self.data = pd.read_pickle(source_path)
        self.sources = []
        self._register_source("source", {})
        self.selected_ids = []

    def _register_source(self, name, data):
        setattr(self, name, ColumnDataSource(data))
        self.sources.append(getattr(self, name))

    def get_frame_subset(self, frame_nr):
        raise NotImplementedError

    def update_data_source(self, frame_nr):
        # TODO: Extract this as a global?
        subset = self.get_frame_subset(frame_nr)
        # TODO: Better way to include the id / index?
        line_style = self.get_line_style(subset)
        self.source.data = {
            **subset.to_dict(orient="list"),
            "id": subset.index.values,
            **line_style,
        }

    def get_line_style(self, subset):
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

    def get_data(self):
        return self.data

    def get_source(self):
        return self.source

    def get_trajectory_by_id(self, id):
        return self.data.iloc[id]

    def get_selected_trajectories(self):
        return self.selected_ids

    def get_id_of_selected_trajectory(self, selected_index):
        return self.source.data["id"][selected_index]

    def update_selected_data(self, old, new):
        if new == []:
            self.selected_ids = []
            for source in self.sources:
                source.selected.indices = []
        else:
            # 'new' holds the index of the new selected data not the actual id
            # need to extract the id from the source data
            traj_id = self.source.data["id"][new[0]]
            self.selected_ids.append(traj_id)
            self.source.selected.indices = old + new

    def export_data(self, path):
        self.data.to_pickle(f"{path}.pkl")
