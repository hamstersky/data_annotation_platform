import cv2
import numpy as np
import settings
import ui.state as state
from bokeh.plotting import curdoc


def get_frame_from_cap(cap, frame_nr):
    """Returns the given frame from the video capture."""

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_nr)
    _, frame = cap.read()
    return frame


def get_image_from_frame(frame):
    """Returns the frame in a format friendly for plotting."""

    img = frame[::-1, :, ::-1]

    h, w, _ = img.shape

    img_orig = np.zeros((h, w), dtype=np.uint32)
    img_view = img_orig.view(dtype=np.uint8).reshape((h, w, 4))
    img_alpha = np.zeros((h, w, 4), dtype=np.uint8)
    img_alpha[:, :, 3] = 255
    img_alpha[:, :, :3] = img
    img_view[:, :, :] = img_alpha
    return img_orig


def clear_selected_data():
    """Clears the currently selected data."""
    state.trajectories.update_selected_data([], [])
    state.segments.update_selected_data([], [])


def refresh_frame(attr, old, frame_nr):
    """
    A callback used in many parts of the application.
    It refreshes the currently plotted frame with the new given frame number.
    """
    frame = get_frame_from_cap(state.cap, frame_nr)
    img = get_image_from_frame(frame)
    state.plot.update_img(img)
    state.current_frame = frame_nr
    state.trajectories.update_views(frame_nr)
    state.segments.update_views(frame_nr)
    clear_selected_data()


def update_buttons_state():
    """Updates the state of the buttons depending on the active selection."""
    segments_labeling = curdoc().select({"tags": "segments-labeling"})
    trajectories_labeling = curdoc().select({"tags": "trajectories-labeling"})
    incorrect_comment = curdoc().get_model_by_name("incorrect-comment")
    if len(state.trajectories.selected_ids) > 1:
        for control in segments_labeling:
            control.disabled = True
        for control in trajectories_labeling:
            control.disabled = False
        incorrect_comment.visible = False
    elif state.segments.selected_ids:
        for control in segments_labeling:
            control.disabled = False
        for control in trajectories_labeling:
            control.disabled = True
            incorrect_comment.visible = True
    else:
        for control in [*segments_labeling, *trajectories_labeling]:
            control.disabled = True
        incorrect_comment.visible = False


def update_slider_limits():
    """Updates the frame slider limits according to the current frame."""
    slider = curdoc().get_model_by_name("slider")
    max_minute = state.total_frames // 60 // 30
    slider.start = state.current_minute * settings.FRAME_INTERVAL
    if state.current_minute == max_minute:
        slider.end = state.total_frames - 1
    else:
        slider.end = (state.current_minute + 1) * settings.FRAME_INTERVAL


def handle_jump_to_frame(attr, old, new):
    """
    A callback used in many parts of the application.
    It updates the state of the application when an element of frame navigation has been used.
    """
    slider = curdoc().get_model_by_name("slider")
    state.current_minute = new // 30 // 60
    state.current_frame = new
    slider.value = new
    update_slider_limits()
