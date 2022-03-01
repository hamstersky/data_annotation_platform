from bokeh.plotting import figure
from bokeh.io import show, save, output_file
from bokeh.models import ColumnDataSource, HoverTool
import numpy as np
import cv2 as cv

class Plot:
    def __init__(self, data, width=640, height=360, img_path='../static/frame.jpg'):
        self.data_traj = data
        self.get_img(img_path)
        self.p = self.create_figure(width, height)
        self.p_traj = self.bokeh_line(self.p)
        self.add_hover_tool()
        self.colors = ['red', 'magenta', 'green', 'orange', 'cyan', 'yellow', 'blue', 'black', 'navy']

    def bokeh_rect(self, fig):
        source = ColumnDataSource(data={
            'x': [],
            'y': [],
            'width': [],
            'height': [],
            'class': [],
            'conf': [],
            'fill_color': [],
            'fill_alpha': [],
            'line_color': [],
            'line_alpha': [],
            'line_width': [],
            'line_dash': []
        })
        
        r = fig.rect(
            source=source,
            fill_color='fill_color',
            fill_alpha='fill_alpha',
            line_color='line_color',
            line_alpha='line_alpha',
            line_width='line_width',
            line_dash='line_dash',
            hover_line_width=2.0,
            hover_line_alpha=1.0,
            selection_fill_alpha=0.3,
            selection_line_width=2.0,
            selection_line_alpha=1.0,
            nonselection_fill_alpha=0.15,
            nonselection_line_width=0.8,
            nonselection_line_alpha=0.3
        )

        return r


    def bokeh_line(self, fig):
        source = ColumnDataSource(data={
            'xs': [],
            'ys': [],
            'line_color': [],
            'line_alpha': [],
            'line_width': [],
            'line_dash': []
        })

        l = fig.multi_line(
            source=source,
            line_color='line_color',
            line_alpha='line_alpha',
            line_width='line_width',
            line_dash='line_dash',
            hover_line_width=2.0,
            hover_line_alpha=1.0,
            selection_line_width=2.0,
            selection_line_alpha=1.0,
            nonselection_line_width=0.8,
            nonselection_line_alpha=0.3
        )

        return l

    def get_range_data(self, frame_no=(0, 0)):
        data = self.data_traj[(self.data_traj.frame_in >= int(frame_no[0])) & (self.data_traj.frame_in <= int(frame_no[1])) & (self.data_traj['class'] < 10)]
        data = data [['id', 'xs', 'ys', 'class', 'x0', 'y0', 'x1', 'y1']]
        self.data = data

    def update_traj_source(self):
        N = self.data.shape[0]

        # Store list of colors for CustomJS callback
        default_lc = [self.colors[int(i)] for i in self.data['class']]

        # Merge two dictionaries
        self.p_traj.data_source.data = {
            **self.data.to_dict(orient='list'),
            **{
                'line_color': default_lc,
                'line_alpha': [0.8] * N,
                'line_width': [2.0] * N,
                'line_dash': ['solid'] * N  # 'solid', 'dashed', 'dotted', 'dotdash', 'dashdot'
            }
        }
        # Add start/end markers
        x0, x1 = zip(*self.data['xs'].apply(lambda x: (x[0], x[-1])).to_list())
        y0, y1 = zip(*self.data['ys'].apply(lambda x: (x[0], x[-1])).to_list())
        self.p.circle(x0, y0, size=2)
        self.p.circle(x1, y1, color='red', size=2)

    def create_figure(self, cap_w, cap_h):
        # Bokeh figure
        p = figure(
            tools='pan,box_zoom,wheel_zoom,tap,save,reset',
            active_scroll='wheel_zoom',
            active_tap='auto',
            x_range=(0, cap_w),
            y_range=(0, cap_h)
        )
        
        p.plot_height = 600
        p.plot_width = int((600 / cap_h) * cap_w)
        p.match_aspect = True
        p.toolbar.logo = None
        p.grid.visible = False
        p.axis.visible = False
        p.outline_line_width = 0

        # Image source
        h, w, c = self.img.shape

        img_orig = np.zeros((h, w), dtype=np.uint32)
        img_view = img_orig.view(dtype=np.uint8).reshape((h, w, 4))
        img_alpha = np.zeros((h, w, 4), dtype=np.uint8)
        img_alpha[:, :, 3] = 255
        img_alpha[:, :, :3] = self.img
        img_view[:, :, :] = img_alpha

        source = ColumnDataSource(data=dict(
            image=[img_orig]
        ))

        p.image_rgba(
            source=source,
            image='image',
            x=0,
            y=0,
            dw=cap_w,
            dh=cap_h,
            level='image'
        )
        return p

    def add_hover_tool(self):
        self.p.add_tools(HoverTool(
            show_arrow=False,
            line_policy='nearest',
            renderers=[self.p_traj],
            tooltips=[("id", "@id")]
        ))

    def get_img(self, img_path):
        cap = cv.VideoCapture(img_path)
        _, frame = cap.read()
        cap.set(cv.CAP_PROP_POS_FRAMES, 0)
        self.img = frame[::-1, :, ::-1]

    def display(self):
        output_file(filename="custom_filename.html", title="Static HTML file")
        save(self.p)
        show(self.p)

if __name__ == '__main__':
    plot = Plot('broken_trajectories.pkl')
    plot.get_range_data((0, 240))
    plot.update_traj_source()
    plot.display()
