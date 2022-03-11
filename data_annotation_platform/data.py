import pandas as pd

class Data():
    def __init__(self, source_path):
        self.data = pd.read_pickle(source_path)
        # TODO: Make the input data already in a format where this will not be necessary
        self.data.reset_index(inplace=True)
        # Extract only relevant features
        self.data = self.data[['xs', 'ys', 'class', 'frame_in', 'frame_out']]