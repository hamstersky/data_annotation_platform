from bokeh.models import Button, MultiChoice
import ui.state as state
from app.helpers import refresh_frame, clear_selected_data, update_buttons_state


def create_labeling_controls():
    def handle_connect():
        # Creates segments needed to connect the supplied trajectories (ids)
        # Connections will be done in the order of the supplied ids
        ids = state.trajectories.selected_ids
        pairs = [tuple(map(int, x)) for x in zip(ids, ids[1:])]
        new_frame = 0
        for t1_ID, t2_ID in pairs:
            segment = state.trajectories.connect(t1_ID, t2_ID)
            # TODO: Consider the append being an internal call. Possibly still return the segment
            state.segments.add_segment(segment)
            new_frame = int(segment["frame_out"])
            refresh_frame("", 0, new_frame)

    def handle_reset_label():
        ids = []
        # TODO: This could be replaced not to rely on the internals of segments if the currently selected ids are moved to state
        for source in state.segments.views:
            for i in source.selected.indices:
                ids.append(source.data["id"][i])
        state.segments.update_label(label=None, comments="", ids=ids)
        refresh_frame("", 0, state.current_frame)

    def handle_label_btn_click(label):
        def callback():
            state.segments.update_label(label=label, comments=incorrect_comment.value)
            refresh_frame("", 0, state.current_frame)

        return callback

    segments_labeling_tags = ["labeling", "segments-labeling"]
    trajectories_labeling_tags = ["labeling", "trajectories-labeling"]
    label_btn_settings = {"disabled": True}
    connect_btn = Button(
        label="Connect", tags=trajectories_labeling_tags, **label_btn_settings
    )
    connect_btn.on_click(handle_connect)

    # Restore segment button
    reset_label_btn = Button(label="Reset label", name="reset-btn", visible=False)
    reset_label_btn.on_click(handle_reset_label)

    # Wrong connection component
    incorrect_btn = Button(
        label="Incorrect segment", tags=segments_labeling_tags, **label_btn_settings
    )
    incorrect_btn.on_click(handle_label_btn_click(False))
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

    correct_btn = Button(
        label="Correct segment", tags=segments_labeling_tags, **label_btn_settings
    )
    correct_btn.on_click(handle_label_btn_click(True))

    reset_select_btn = Button(label="Reset selection")
    reset_select_btn.on_click(clear_selected_data)

    labeling_controls = [
        reset_select_btn,
        reset_label_btn,
        connect_btn,
        correct_btn,
        incorrect_btn,
        incorrect_comment,
    ]

    BUTTONS = [
        reset_select_btn,
        reset_label_btn,
        connect_btn,
        incorrect_btn,
        correct_btn,
    ]

    for btn in BUTTONS:
        btn.on_click(update_buttons_state)

    return labeling_controls
