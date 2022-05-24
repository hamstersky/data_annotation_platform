import settings
from bokeh.models import Button, Slider

from app.helpers import refresh_frame, update_slider_limits
import ui.state as state
import ui.styles as styles


def handle_minute_changed(value, slider):
    """Callback generator for updating the slider when the current minute is changed.

    Attributes:
        value: represents the value by which the minutes have changed.
               For instance, 1 means that the change is 1 minute forward.
        slider: the slider element needs to be injected as a dependency
    """

    def callback():
        max_minute = state.total_frames // 60 // 30
        next_minute = state.current_minute + value
        # Make sure that the minute doesn't go over the limit
        if next_minute >= 0 and next_minute <= max_minute:
            state.current_minute += value
            update_slider_limits()
            slider.value = slider.end if value < 0 else slider.start

    return callback


def create_slider():
    """Returns the slider for changing frames and buttons to update its range."""

    # == Slider ==
    slider = Slider(
        start=1,
        end=settings.FRAME_INTERVAL,
        value=1,
        step=1,
        width=styles.SLIDER_WIDTH,
        margin=(0, 15, 0, 15),
        name="slider",
    )
    slider.on_change("value", refresh_frame)

    # == Next minute button ===
    next_min_btn = Button(label="+1min", width=50)
    next_min_btn.on_click(handle_minute_changed(1, slider))

    # Previous minute button ==
    prev_min_btn = Button(label="-1min", width=50)
    prev_min_btn.on_click(handle_minute_changed(-1, slider))

    return [prev_min_btn, slider, next_min_btn]
