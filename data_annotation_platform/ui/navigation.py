from bokeh.models import Button, NumericInput

from app.helpers import handle_jump_to_frame
import ui.state as state
import ui.styles as styles


def handle_frame_navigation(value):
    """Callback generator for updating the current frame."""

    def callback():
        new_frame = state.current_frame + value
        handle_jump_to_frame("", 0, new_frame)

    return callback


def handle_next_interest():
    """Callback for jumping to frame with the next point of interest."""

    frame_ins = state.segments.current_frame_view.data["frame_in"]
    # Find the segment with the latest frame_in in the current frame view
    max_frame = int(max(frame_ins)) if frame_ins else state.current_frame
    # Find the next not annotated segment with frame_in after max_frame
    next_frame = state.segments.get_next_interest_frame(max_frame)
    handle_jump_to_frame("", 0, next_frame)


def create_navigation():
    """Returns a list of widgets used for navigating frames."""
    # == Jump to input field ==
    jump_to = NumericInput(
        low=1,
        high=state.total_frames,
        placeholder="Jump to specific frame",
        width=styles.PLOT_WIDTH,
    )
    jump_to.on_change("value", handle_jump_to_frame)

    # == Frame navigation buttons ==
    # Define the type of frame navigation buttons in format {frames: label}
    labels = {-30: "-1s", -1: "-1 frame", 1: "+1 frame", 30: "+1s"}
    btns = []
    for frames, label in labels.items():
        btn = Button(
            label=label,
            sizing_mode="fixed",
            height=styles.NAV_BTN_SIZE,
            width=styles.NAV_BTN_SIZE,
        )
        btn.on_click(handle_frame_navigation(frames))
        btns.append(btn)

    # == Next interest button ==
    next_interest = Button(
        label="Jump to next interest", height=styles.NAV_BTN_SIZE, width_policy="min"
    )
    next_interest.on_click(handle_next_interest)

    return [jump_to, *btns, next_interest]
