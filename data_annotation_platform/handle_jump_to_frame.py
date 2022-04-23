from event import emit
import state


def handle_jump_to_frame(attr, old, new):
    state.current_minute = new // 30 // 60
    state.current_frame = new
    emit("frame_updated")
