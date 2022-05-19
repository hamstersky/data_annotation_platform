from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure
import ui.styles as styles


class TrajectoryPlot:
    """
    A class to represent the plot with trajectories. It set ups the plot with all the necessary settings.

    Attributes:
        trajectories: a DataFrame with broken trajectories data
        segments: a DataFrame with segments data
    """

    def __init__(self, trajectories, segments):
        self.cap_w = 640
        self.cap_h = 360
        self.img_source = ColumnDataSource(data=dict(image=[]))
        self.setup_plot()
        self.setup_renderers(trajectories, segments)
        self.setup_legend()
        self.setup_tools()

    def setup_plot(self):
        """Creates a plot object and saves it as an instance variable."""

        p = figure(
            tools="pan,wheel_zoom,tap,reset",
            toolbar_location="below",
            active_scroll="wheel_zoom",
            active_tap="auto",
            x_range=(0, self.cap_w),
            y_range=(0, self.cap_h),
            name="plot",
        )
        p.toolbar.logo = None
        p.grid.visible = False
        p.axis.visible = False
        p.outline_line_width = 0
        p.plot_height = styles.PLOT_HEIGHT
        p.plot_width = styles.PLOT_WIDTH
        self.plot = p

    def setup_renderers(self, trajectories, segments):
        """Adds renderers to the plot."""

        self.img_plot = self.plot.image_rgba(
            source=self.img_source,
            image="image",
            x=0,
            y=0,
            dw=self.cap_w,
            dh=self.cap_h,
            level="image",
        )

        self.trajectories_lines = self.plot.multi_line(
            source=trajectories.current_frame_view,
            line_color="line_color",
            line_alpha=0.8,
            line_width=2.0,
            line_dash="solid",
            hover_line_width=2.0,
            hover_line_alpha=1.0,
            selection_line_width=4.0,
            selection_line_alpha=1.0,
            nonselection_line_width=2.0,
            nonselection_line_alpha=0.7,
            legend_label="broken trajectories",
        )

        self.segments_lines = self.plot.multi_line(
            source=segments.current_frame_view,
            line_color="line_color",
            line_alpha=0.8,
            line_width=2.0,
            line_dash="line_dash",
            hover_line_width=2.0,
            hover_line_alpha=1.0,
            selection_line_width=4.0,
            selection_line_alpha=1.0,
            nonselection_line_width=2.0,
            nonselection_line_alpha=0.7,
        )

        # Below renderers are only used for legend as the segments' line color and
        # dash are dynamic
        self.not_labeled = self.plot.multi_line(
            line_color="red",
            line_alpha=0.8,
            line_width=2.0,
            line_dash="dashed",
            legend_label="not labeled segments",
        )

        self.labeled = self.plot.multi_line(
            line_color="navy",
            line_alpha=0.8,
            line_width=2.0,
            line_dash="solid",
            legend_label="correct segments",
        )

        self.candidates = self.plot.multi_line(
            line_color="brown",
            line_alpha=0.8,
            line_width=2.0,
            line_dash="solid",
            legend_label="candidate trajectories",
        )

    def setup_tools(self):
        """Adds a hover tool to the plot."""

        self.plot.add_tools(
            HoverTool(
                show_arrow=False,
                line_policy="nearest",
                renderers=[self.trajectories_lines, self.segments_lines],
                tooltips=[
                    ("id", "@id"),
                    ("frame_in", "@frame_in"),
                    ("frame_out", "@frame_out"),
                ],
            )
        )

    def setup_legend(self):
        """Configures the legend for the plot."""
        self.plot.legend.orientation = "horizontal"
        self.plot.legend.spacing = 15
        self.plot.legend.background_fill_alpha = 0.6
        self.plot.legend.border_line_dash = "solid"
        self.plot.legend.border_line_color = "black"

    def update_img(self, img):
        """Helper method for updating the frame image in the plot."""
        self.img_plot.data_source.data["image"] = [img]
