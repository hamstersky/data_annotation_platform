from bokeh.models import (
    ColumnDataSource,
    DataTable,
    Panel,
    Paragraph,
    PreText,
    Tabs,
    TableColumn,
)
from handle_jump_to_frame import handle_jump_to_frame
from event import emit, subscribe

import state

segments = state.segments
trajectories = state.trajectories
active_tab = None


def create_tabs():
    def update_stats(**kwargs):
        stats.text = f"""
    Number of correct segments: {segments.get_correct_segment_count()}
    Number of incorrect segments: {segments.get_incorrect_segment_count()}
    Accuracy: {"{:.2f}".format(segments.get_correct_incorrect_ratio() * 100)}%
        """

    subscribe("label_changed", update_stats)

    def handle_table_row_clicked(table):
        def callback(_, old, new):
            if new:
                frame = table.source.data["frame_in"][new[0]]
                handle_jump_to_frame("", 0, frame)

        return callback

    def handle_tab_switched(attr, old, new):
        reset_tables = ["wrong_segments", "correct_segments", "new_segments"]
        # TODO: Will need to emit an event here
        btn_state = tabs.tabs[new].name in reset_tables
        emit("tab_switched", state=btn_state)
        tab_description.text = descriptions[tabs.tabs[new].name]
        active_tab = TABLES[tabs.tabs[new].name]

    def update_tables(**kwargs):
        # TODO: Find better way for keeping track of the original index
        # At least remove the direct access to the index
        incorrect_segments_table_source.data = segments.get_segments_by_status(False)
        incorrect_segments_table_source.data[
            "original_index"
        ] = segments.get_segments_by_status(False).index
        correct_segments_table_source.data = segments.get_segments_by_status(True)
        new_segments_table_source.data = segments.get_new_segments()
        for table in TABLES.values():
            # TODO: Figure out if removing the callbacks is necessary
            table.source.selected._callbacks = {}
            table.source.selected.indices = []
            table.source.selected.on_change("indices", handle_table_row_clicked(table))

    subscribe("label_changed", update_tables)

    # Stats
    stats = PreText(text="")
    update_stats()

    # Settings for all tables
    columns = [
        TableColumn(field=c, title=c) for c in ["id", "frame_in", "frame_out", "class"]
    ]
    table_params = {
        "columns": columns,
        "index_position": None,
        "height": 250,
        "width": 550,
    }

    # Incorrect segments component
    incorrect_segments_table_source = ColumnDataSource(
        segments.get_segments_by_status(False)
    )
    incorrect_segments_table = DataTable(
        source=incorrect_segments_table_source,
        **{key: table_params[key] for key in table_params if key != "columns"},
        columns=[*columns, TableColumn(field="comments", title="comments")],
    )
    incorrect_segments_table_source.selected.on_change(
        "indices", handle_table_row_clicked(incorrect_segments_table)
    )

    # Candidates table
    # TODO: Add euclidean distance
    trajectories_table = DataTable(source=trajectories.get_source(), **table_params)

    # New segments table
    new_segments_table_source = ColumnDataSource(segments.get_new_segments())
    new_segments_table = DataTable(source=new_segments_table_source, **table_params)
    new_segments_table_source.selected.on_change(
        "indices", handle_table_row_clicked(new_segments_table)
    )

    # Correct segments table
    correct_segments_table_source = ColumnDataSource(
        segments.get_segments_by_status(True)
    )
    correct_segments_table = DataTable(
        source=correct_segments_table_source, **table_params
    )
    correct_segments_table_source.selected.on_change(
        "indices", handle_table_row_clicked(correct_segments_table)
    )

    descriptions = {
        "trajectories": "Trajectories/candidates on current frame. Click a trajectory to select it:",
        "wrong_segments": "Wrong segments:",
        "correct_segments": "Correct segments:",
        "new_segments": "Manually created segments:",
        "current_selection": "Currently selected trajectories:",
        "stats": "",
    }
    trajectories_tab = Panel(
        child=trajectories_table, title="Current frame", name="trajectories"
    )
    wrong_segments_tab = Panel(
        child=incorrect_segments_table, title="Wrong segments", name="wrong_segments"
    )
    correct_segments_tab = Panel(
        child=correct_segments_table, title="Correct segments", name="correct_segments"
    )
    new_segments_tab = Panel(
        child=new_segments_table, title="New segments", name="new_segments"
    )

    stats_tab = Panel(child=stats, title="Statistics", name="stats")
    tab_description = Paragraph(text=descriptions["trajectories"])
    tabs = Tabs(
        tabs=[
            trajectories_tab,
            correct_segments_tab,
            wrong_segments_tab,
            new_segments_tab,
            stats_tab,
        ],
        height=280,
    )
    tabs.on_change("active", handle_tab_switched)

    TABLES = {
        "trajectories": trajectories_table,
        "wrong_segments": incorrect_segments_table,
        "correct_segments": correct_segments_table,
        "new_segments": new_segments_table,
    }

    return [tab_description, tabs]


# def get_panel():
#     return [tab_description, tabs]


# TODO: Get rid of this eventually
def get_active_tab():
    return active_tab
