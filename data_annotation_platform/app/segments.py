import numpy as np
import pandas as pd

from app.data_source import DataSource
from bokeh.models import ColumnDataSource


class Segments(DataSource):
    def __init__(self, source_path):
        super().__init__(source_path)

        # Check if the loaded data already has the annotation columns
        # This is the case when loading persisted data
        if "correct" not in self.data.columns:
            # For keeping the label
            self.data["correct"] = None
            # For keeping track of new segments added in the annotation tool
            self.data["new"] = False
            self.data["comments"] = ""

        self._register_source("incorrect_source", self.get_segments_by_status(False))
        self._register_source("correct_source", self.get_segments_by_status(True))
        self._register_source("new_source", self.get_new_segments())

    def get_frame_subset(self, frame_nr):
        return self.data[
            (frame_nr >= self.data["frame_in"])
            & (frame_nr <= self.data["frame_out"] + 400)
            & (self.data["correct"] != False)
        ]

    def set_status(self, status, comments="", ids=None):
        if ids is None:
            ids = self.selected_ids
        for id in ids:
            is_new_segment = self.data.at[id, "new"]
            if is_new_segment:
                self.data.drop(labels=[id], axis=0, inplace=True)
            else:
                self.data.loc[id, ["correct", "comments"]] = np.array(
                    [status, ",".join(comments)], dtype="object"
                )

    def create_segment(self, t1, t2):
        segment = pd.DataFrame(
            {
                # TODO: Figure out a way to keep the original class and use something else for colors
                "class": 8,
                "xs": [[t1["xs"][-1], t2["xs"][0]]],
                "ys": [[t1["ys"][-1], t2["ys"][0]]],
                "frame_in": t1["frame_out"],
                "frame_out": t2["frame_in"],
                "correct": True,
                "new": True,
            }
        )
        return segment

    def append_segment(self, segment):
        self.data = pd.concat([self.data, segment], ignore_index=True)
        self.data.index.name = "id"

    def get_segments_by_status(self, status):
        return self.data[self.data["correct"] == status]

    # Returns count of segments only created by the algorithm
    def get_total_segment_count(self):
        return self.data[self.data["new"] == False].shape[0]

    def get_correct_segment_count(self):
        return self.data[
            (self.data["new"] == False) & (self.data["correct"] != False)
        ].shape[0]

    def get_incorrect_segment_count(self):
        return self.data[
            (self.data["new"] == False) & (self.data["correct"] == False)
        ].shape[0]

    def get_correct_incorrect_ratio(self):
        return self.get_correct_segment_count() / self.get_total_segment_count()

    def get_new_segments(self):
        return self.data[self.data["new"] == True]

    def get_new_segments_count(self):
        return self.data[(self.data["new"] == True)].shape[0]

    def find_next_interest(self, frame_nr):
        return int(
            self.data[
                (self.data["frame_in"] > frame_nr) & (pd.isna(self.data["correct"]))
            ]["frame_in"].min()
        )

    def get_line_style(self, subset):
        colors = {True: "navy", None: "red"}
        line_style = {True: "solid", None: "dashed"}
        line_color = [colors[i] for i in subset["correct"]]
        line_dash = [line_style[i] for i in subset["correct"]]
        return dict(line_color=line_color, line_dash=line_dash)

    def update_sources(self):
        incorrect = self.get_segments_by_status(False)
        correct = self.get_segments_by_status(True)
        new = self.get_new_segments()
        self.incorrect_source.data = {
            **incorrect.to_dict(orient="list"),
            "id": incorrect.index.values,
        }
        self.correct_source.data = {
            **correct.to_dict(orient="list"),
            "id": correct.index.values,
        }
        self.new_source.data = {
            **new.to_dict(orient="list"),
            "id": new.index.values,
        }
