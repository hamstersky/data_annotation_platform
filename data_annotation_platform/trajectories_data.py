import pandas as pd
from data import Data

class TrajectoriesData(Data):
    def __init__(self, source_path):
        super().__init__(source_path)

    def get_frame_subset(self, frame_nr):
        return self.data[(frame_nr >= self.data['frame_in']) &
                         (frame_nr <= self.data['frame_out'] + 400)]