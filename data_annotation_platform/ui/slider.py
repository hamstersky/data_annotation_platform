import settings
import ui.state as state
from app.helpers import update_slider_limits
from app.helpers import update_frame
from bokeh.models import Button, Slider


def create_slider():
    def handle_minute_changed(value):
        def callback():
            max_minute = state.total_frames // 60 // 30
            next_minute = state.current_minute + value
            if next_minute >= 0 and next_minute <= max_minute:
                state.current_minute += value
                update_slider_limits()
                slider.value = slider.end if value < 0 else slider.start

        return callback

    slider = Slider(
        start=0,
        end=settings.FRAME_INTERVAL,
        value=1,
        step=1,
        width=state.plot.plot.width - 150,
        margin=(0, 15, 0, 15),
        name="slider",
    )
    slider.on_change("value", update_frame)
    next_min_btn = Button(label="+1min", width=50)
    next_min_btn.on_click(handle_minute_changed(1))
    prev_min_btn = Button(label="-1min", width=50)
    prev_min_btn.on_click(handle_minute_changed(-1))

    return [prev_min_btn, slider, next_min_btn]
