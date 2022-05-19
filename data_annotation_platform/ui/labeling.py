from bokeh.models import Button, MultiChoice
import ui.state as state
from app.helpers import refresh_frame, clear_selected_data, update_buttons_state


def handle_connect():
    """Callback for connecting the currently selected trajectories."""
    t1Id, t2Id = state.trajectories.selected_ids
    segment = state.trajectories.connect(t1Id, t2Id)
    state.segments.add_segment(segment)
    new_frame = int(segment["frame_out"])
    # Jump to the the last frame of the new segment so the user can see the whole trajectory
    refresh_frame("", 0, new_frame)


def handle_reset_label():
    """Callback for resetting the labels for all currently selected segments."""
    ids = []
    for view in state.segments.views:
        for i in view.selected.indices:
            ids.append(view.data["id"][i])
    state.segments.update_label(label=None, comments="", ids=ids)
    refresh_frame("", 0, state.current_frame)


def handle_label_btn_click(label, incorrect_comment):
    """Callback generator for updating the label of the selected segment.

    Arguments:
        label: the label to assign to the selected segment
        incorrect_comment: the comment in case of incorrect label
    """

    def callback():
        state.segments.update_label(label=label, comments=incorrect_comment.value)
        refresh_frame("", 0, state.current_frame)

    return callback


def create_labeling_controls():
    """Returns a list of widgets used for labeling trajectories."""

    # Tags are used for for distinguishing between controls relevant for broken trajectories and segments
    segments_labeling_tags = ["labeling", "segments-labeling"]
    trajectories_labeling_tags = ["labeling", "trajectories-labeling"]
    label_btn_settings = {"disabled": True}

    # == Connect button ==
    connect_btn = Button(
        label="Connect", tags=trajectories_labeling_tags, **label_btn_settings
    )
    connect_btn.on_click(handle_connect)

    # == Reasons for incorrect segment dropdown ==
    incorrect_options = [
        "lack of good connection",
        "large distance",
        "illegal maneuver",
        "wrong direction",
        "parked vehicle",
        "object misclassification",
        "other",
    ]
    incorrect_comment = MultiChoice(
        options=incorrect_options,
        visible=False,
        title="Select the reason(s) why the connection is incorrect by clicking on the input box.",
        name="incorrect-comment",
    )

    # == Incorrect segment button ==
    incorrect_btn = Button(
        label="Incorrect segment", tags=segments_labeling_tags, **label_btn_settings
    )
    incorrect_btn.on_click(handle_label_btn_click(False, incorrect_comment))

    # == Correct segment button ==
    correct_btn = Button(
        label="Correct segment", tags=segments_labeling_tags, **label_btn_settings
    )
    correct_btn.on_click(handle_label_btn_click(True, incorrect_comment))

    # == Reset label button ==
    reset_label_btn = Button(label="Reset label", name="reset-btn", visible=False)
    reset_label_btn.on_click(handle_reset_label)

    # == Reset current selection button ==
    reset_select_btn = Button(label="Reset selection")
    reset_select_btn.on_click(clear_selected_data)

    # Collect all buttons in a list so it can be used to easily add a callback to all of them
    BUTTONS = [
        reset_select_btn,
        reset_label_btn,
        connect_btn,
        correct_btn,
        incorrect_btn,
    ]
    for btn in BUTTONS:
        btn.on_click(update_buttons_state)

    # The final controls are the buttons and the incorrect comment dropdown
    controls = [*BUTTONS, incorrect_comment]

    return controls
