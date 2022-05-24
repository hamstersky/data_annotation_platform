import numpy as np
import pandas as pd
from bokeh.models import ColumnDataSource

from app.data_source import DataSource


class Segments(DataSource):
    """
    Class representing a data source specifically for segments which connect broken trajectories.
    Inherits from DataSource class.

    This class adds new columns to the data which are only relevant for segments. These are:

    correct: holds the label of the segment
    new: indicates whether the segment is newly created by the annotator (manually)
    comments: holds comments in case of incorrect segment

    Attributes:
        incorrect_view: holds only segments that have the incorrect label
        correct_view: holds only segments that have the correct label
        new_view: holds only segments that have been created manually by the annotator
    """

    def __init__(self, source_path):
        super().__init__(source_path)

        # Check if the loaded data already has the annotation columns
        # This is the case when loading persisted data
        if "correct" not in self.data.columns:
            self.data["correct"] = None
            self.data["new"] = False
            self.data["comments"] = ""

        self._register_view("incorrect_view", self.get_segments_by_label(False))
        self._register_view("correct_view", self.get_segments_by_label(True))
        self._register_view("new_view", self.get_new_segments())

    def get_frame_subset(self, frame_nr):
        """Returns a subset of data relevant for the given frame. It only includes segments that are correct."""
        return self.data[
            (frame_nr >= self.data["frame_in"])
            & (frame_nr <= self.data["frame_out"] + 258)
            & (self.data["correct"] != False)
        ]

    def update_label(self, label, comments="", ids=None):
        """
        Updates the label of a segment.

        Attributes:
            status: one of the possible labels. True for correct, False for incorrect, None for lack of label
            comments: comments in case of an incorrect label
            ids: ids of the segments to be updated. By default None, which means that the currently selected_ids will be used.
        """

        if ids is None:
            ids = self.selected_ids
        for id in ids:
            is_new_segment = self.data.at[id, "new"]
            # If the label of a newly created segment is updated it means that the segment is being deleted.
            # It's because a newly created segment cannot be incorrect
            if is_new_segment:
                self.data.drop(labels=[id], axis=0, inplace=True)
            else:
                self.data.loc[id, ["correct", "comments"]] = np.array(
                    [label, ",".join(comments)], dtype="object"
                )

    def add_segment(self, segment):
        """Adds a new segment to the data."""

        self.data = pd.concat([self.data, segment], ignore_index=True)
        # For some reason concatenation resets the name of the index so it needs to be set again.
        self.data.index.name = "id"

    def get_segments_by_label(self, label):
        """Returns a subset of data with the given label."""

        return self.data[self.data["correct"] == label]

    def get_new_segments(self):
        """Returns a subset of data with only segments manually created by the annotator."""

        return self.data[self.data["new"] == True]

    def get_total_segment_count(self):
        """Returns count of segments only created by the reconstruction algorithm. Doesn't include manually created segments by the annotator."""
        return self.data[self.data["new"] == False].shape[0]

    def get_correct_segment_count(self):
        """
        Returns count of segments with the correct label.
        Doesn't include manually created segments by the annotator as those are always correct by definition.
        """
        return self.data[
            (self.data["new"] == False) & (self.data["correct"] != False)
        ].shape[0]

    def get_incorrect_segment_count(self):
        """
        Returns count of segments with the incorrect label.
        Doesn't include manually created segments by the annotator as those are always correct by definition.
        """
        return self.data[
            (self.data["new"] == False) & (self.data["correct"] == False)
        ].shape[0]

    def get_new_segments_count(self):
        """Returns count of segments manually created by the annotator."""
        return self.data[(self.data["new"] == True)].shape[0]

    def get_correct_incorrect_ratio(self):
        """Returns the ratio of correct to incorrect segments."""

        return self.get_correct_segment_count() / self.get_total_segment_count()

    def get_next_interest_frame(self, frame_nr):
        """
        Returns the frame number of the next frame with a point of interest relative to the current frame .
        A point of interest is defined as a segment without a label.
        """
        return int(
            self.data[
                (self.data["frame_in"] > frame_nr) & (pd.isna(self.data["correct"]))
            ]["frame_in"].min()
        )

    def get_line_style(self, subset):
        """Returns styles for lines specific for segments."""

        colors = {True: "navy", None: "red"}
        line_style = {True: "solid", None: "dashed"}
        line_color = [colors[i] for i in subset["correct"]]
        line_dash = [line_style[i] for i in subset["correct"]]
        return dict(line_color=line_color, line_dash=line_dash)

    def update_views(self, frame_nr):
        """Updates the default view and views specific for segments."""

        super().update_views(frame_nr)
        incorrect = self.get_segments_by_label(False)
        correct = self.get_segments_by_label(True)
        new = self.get_new_segments()
        self.incorrect_view.data = {
            **incorrect.to_dict(orient="list"),
            "id": incorrect.index.values,
        }
        self.correct_view.data = {
            **correct.to_dict(orient="list"),
            "id": correct.index.values,
        }
        self.new_view.data = {
            **new.to_dict(orient="list"),
            "id": new.index.values,
        }
