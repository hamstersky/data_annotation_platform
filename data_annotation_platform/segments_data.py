import pandas as pd
from data import Data

class SegmentsData(Data):
    def __init__(self, source_path):
        super().__init__(source_path)
        self.data['correct'] = True

    def get_frame_subset(self, frame_nr):
        return self.data[(frame_nr >= self.data['frame_in']) &
                         (frame_nr <= self.data['frame_out'] + 400) &
                         (self.data['correct'] == True)]

    # Returns new label (true/false)
    def toggle_correct(self, id):
        new_label = not self.data.at[id, 'correct']
        self.data.at[id, 'correct'] = new_label
        return new_label

    # TODO: Doesn't belong here as doesn't have access to all data
    # Creates segments needed to connect the supplied trajectories (ids)
    # Connections will be done in the order of the supplied ids
    def connect(self, ids):
        # Generate pairs of trajectories to be connected with a segment
        pairs = zip(ids, ids[1:])
        for t1_ID, t2_ID in pairs:
            segment = self.create_segment(t1_ID, t2_ID)
            self.append_segment(segment)

    def create_segment(self, t1, t2):
        segment = pd.DataFrame({
            'class': 8,
            'xs': [[t1['xs'][-1], t2['xs'][0]]],
            'ys': [[t1['ys'][-1], t2['ys'][0]]],
            'frame_in': t1['frame_out'],
            'frame_out': t2['frame_in'],
            'correct': True
        })
        return segment

    def append_segment(self, segment):
        self.data = pd.concat([self.data, segment])

