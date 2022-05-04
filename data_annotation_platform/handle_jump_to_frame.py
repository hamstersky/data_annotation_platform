from bokeh.plotting import curdoc
import ui.state as state
import settings


def update_slider_limits():
    slider = curdoc().get_model_by_name("slider")
    max_minute = state.total_frames // 60 // 30
    slider.start = state.current_minute * settings.FRAME_INTERVAL
    if state.current_minute == max_minute:
        slider.end = state.total_frames - 1
    else:
        slider.end = (state.current_minute + 1) * settings.FRAME_INTERVAL


def handle_jump_to_frame(attr, old, new):
    slider = curdoc().get_model_by_name("slider")
    state.current_minute = new // 30 // 60
    state.current_frame = new
    slider.value = new
    update_slider_limits()
