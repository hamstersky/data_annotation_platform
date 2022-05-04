from bokeh.models import Button, NumericInput
from handle_jump_to_frame import handle_jump_to_frame
import ui.state as state
import ui.styles as styles


def handle_frame_navigation(value):
    def callback():
        new_frame = state.current_frame + value
        handle_jump_to_frame("", 0, new_frame)

    return callback


def next_interest_handler():
    frame_ins = state.segments.get_source().data["frame_in"]
    frame = max(frame_ins) if frame_ins else state.current_frame
    next_frame = state.segments.find_next_interest(int(frame))
    handle_jump_to_frame("", 0, next_frame)


def create_navigation():
    jump_to = NumericInput(
        low=1,
        high=state.total_frames,
        placeholder="Jump to specific frame",
        width=styles.PLOT_WIDTH,
    )
    jump_to.on_change("value", handle_jump_to_frame)

    btn_size = 75
    labels = {-30: "-1s", -1: "-1 frame", 1: "+1 frame", 30: "+1s"}
    btns = []
    for frames, label in labels.items():
        btn = Button(label=label, sizing_mode="fixed", height=btn_size, width=btn_size)
        btn.on_click(handle_frame_navigation(frames))
        btns.append(btn)

    next_interest = Button(
        label="Jump to next interest", height=btn_size, width_policy="min"
    )
    next_interest.on_click(next_interest_handler)

    return [jump_to, *btns, next_interest]
