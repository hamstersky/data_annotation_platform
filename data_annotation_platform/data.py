from dataclasses import dataclass

import pandas as pd
from bokeh.models import ColumnDataSource


class Data:
    def __init__(self, source_path):
        self.data = pd.read_pickle(source_path)
        # TODO: Make the input data already in a format where this will not be necessary
        self.data.reset_index(inplace=True)
        # Extract only relevant features
        self.data = self.data[["xs", "ys", "class", "frame_in", "frame_out"]]
        self.data.index.name = "id"
        self.source = ColumnDataSource()
        self.selected_ids = []

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
            self.source.selected.indices = []
        else:
            # 'new' holds the index of the new selected data not the actual id
            # need to extract the id from the source data
            traj_id = self.source.data["id"][new[0]]
            self.selected_ids.append(traj_id)
            self.source.selected.indices = old + new
