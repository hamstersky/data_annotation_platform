import pandas as pd
import numpy as np
from data import Data

class SegmentsData(Data):
    def __init__(self, source_path):
        super().__init__(source_path)
        # For keeping stats about connections
        self.data['correct'] = True
        # For keeping track of new segments added in the annotation tool
        self.data['new'] = False
        self.data['comments'] = ''

    def get_frame_subset(self, frame_nr):
        return self.data[(frame_nr >= self.data['frame_in']) &
                         (frame_nr <= self.data['frame_out'] + 400) &
                         (self.data['correct'] == True)]

    def toggle_correct(self, comments=[], ids=None):
        if ids is None:
            ids = self.selected_ids
        for id in ids:
            is_new_segment = self.data.at[id, 'new']
            if is_new_segment:
                self.data.drop(labels=[id], axis=0, inplace=True)
            else:  
                new_label = not self.data.at[id, 'correct']
                self.data.loc[id, ['correct', 'comments']] = np.array([new_label, comments], dtype='object')

    def create_segment(self, t1, t2):
        segment = pd.DataFrame({
            # TODO: Figure out a way to keep the original class and use something else for colors
            'class': 8,
            'xs': [[t1['xs'][-1], t2['xs'][0]]],
            'ys': [[t1['ys'][-1], t2['ys'][0]]],
            'frame_in': t1['frame_out'],
            'frame_out': t2['frame_in'],
            'correct': True,
            'new': True
        })
        return segment

    def append_segment(self, segment):
        self.data = pd.concat([self.data, segment], ignore_index=True)
        self.data.index.name = 'id'

    def get_incorrect_segments(self):
        return self.data[self.data['correct'] == False]

    # Returns count of segments only created by the algorithm
    def get_total_segment_count(self):
        return self.data[self.data['new'] == False].shape[0]

    def get_correct_segment_count(self):
        return self.data[(self.data['new'] == False) & (self.data['correct'] == True)].shape[0]

    def get_incorrect_segment_count(self):
        return self.data[(self.data['new'] == False) & (self.data['correct'] == False)].shape[0]

    def get_correct_incorrect_ratio(self):
        return self.get_correct_segment_count() / self.get_total_segment_count()

    def get_new_segments(self):
        return self.data[self.data['new'] == True]