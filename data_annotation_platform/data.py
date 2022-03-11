import pandas as pd
from bokeh.models import ColumnDataSource

class Data():
    def __init__(self, source_path):
        self.data = pd.read_pickle(source_path)
        # TODO: Make the input data already in a format where this will not be necessary
        self.data.reset_index(inplace=True)
        # Extract only relevant features
        self.data = self.data[['xs', 'ys', 'class', 'frame_in', 'frame_out']]
        self.source = ColumnDataSource()

    def get_frame_subset(self, frame_nr):
        raise NotImplementedError

    def update_data_source(self, frame_nr):
        # TODO: Extract this as a global?
        subset = self.get_frame_subset(frame_nr)
        colors = ['red', 'magenta', 'green', 'orange', 'cyan', 'yellow', 'blue', 'black', 'navy']
        line_colors = [colors[int(i)] for i in subset['class']]
        # TODO: Better way to include the id / index?
        self.source.data = {
            **subset.to_dict(orient='list'),
            'id': subset.index.values,
            'line_color': line_colors,
        }