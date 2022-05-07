from bokeh.models import (
    DataTable,
    Panel,
    Paragraph,
    PreText,
    Tabs,
    TableColumn,
)
from app.helpers import handle_jump_to_frame
from bokeh.plotting import curdoc

import ui.state as state


def create_tabs():
    segments = state.segments
    trajectories = state.trajectories

    def update_stats():
        stats.text = f"""
    Number of correct segments: {segments.get_correct_segment_count()}
    Number of incorrect segments: {segments.get_incorrect_segment_count()}
    Number of new segments: {segments.get_new_segments_count()}
    Accuracy: {"{:.2f}".format(segments.get_correct_incorrect_ratio() * 100)}%
        """

    def handle_table_row_clicked(table):
        def callback(_, old, new):
            if new:
                frame = table.source.data["frame_in"][new[0]]
                handle_jump_to_frame("", 0, frame)

        return callback

    def handle_tab_switched(attr, old, new):
        reset_tables = ["wrong_segments", "correct_segments", "new_segments"]
        reset_btn = curdoc().get_model_by_name("reset-btn")
        active_tab = tabs.tabs[new].name
        reset_btn.visible = active_tab in reset_tables
        tab_description.text = TABLES.get(tabs.tabs[new].name, {}).get(
            "description", ""
        )

    def clear_selections(table):
        def callback(attr, old, new):
            table.source.selected.indices = []

        return callback

    # Stats
    stats = PreText()
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
        "tags": ["table"],
    }

    # Incorrect segments component
    incorrect_segments_table = DataTable(
        source=segments.incorrect_source,
        **{key: table_params[key] for key in table_params if key != "columns"},
        columns=[*columns, TableColumn(field="comments", title="comments")],
    )

    # Candidates table
    # TODO: Add euclidean distance
    trajectories_table = DataTable(source=trajectories.get_source(), **table_params)

    # New segments table
    new_segments_table = DataTable(source=segments.new_source, **table_params)

    # Correct segments table
    correct_segments_table = DataTable(source=segments.correct_source, **table_params)

    TABLES = {
        "current_frame": {
            "object": trajectories_table,
            "description": "Trajectories/candidates on current frame. Click a trajectory to select it:",
        },
        "wrong_segments": {
            "object": incorrect_segments_table,
            "description": "Wrong segments:",
        },
        "correct_segments": {
            "object": correct_segments_table,
            "description": "Correct segments:",
        },
        "new_segments": {
            "object": new_segments_table,
            "description": "Manually created segments:",
        },
    }

    panels = []
    # Register callbacks and create panels for tables
    for name, params in TABLES.items():
        table = params["object"]
        panels.append(
            Panel(child=table, title=" ".join(name.split("_")).capitalize(), name=name)
        )
        # The current_frame table doesn't need the same callbacks
        if name == "current_frame":
            continue
        table.source.selected.on_change("indices", handle_table_row_clicked(table))
        # Update the stats when the data changes
        table.source.on_change("data", lambda attr, old, new: update_stats())
        table.source.on_change("data", clear_selections(table))

    stats_tab = Panel(child=stats, title="Statistics", name="stats")
    # In the intial state use the description of the first tab
    tab_description = Paragraph(text=TABLES[list(TABLES.keys())[0]]["description"])
    tabs = Tabs(
        tabs=[
            *panels,
            stats_tab,
        ],
        height=280,
    )
    tabs.on_change("active", handle_tab_switched)

    return [tab_description, tabs]
