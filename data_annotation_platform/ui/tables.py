from bokeh.models import (
    DataTable,
    Panel,
    Paragraph,
    PreText,
    Tabs,
    TableColumn,
)
from bokeh.plotting import curdoc
from app.helpers import handle_jump_to_frame
from textwrap import dedent

import ui.state as state
import ui.styles as styles


def handle_table_row_clicked(table):
    """
    Callback generator for handling table row clicks.
    The callback jumps to the first frame of the segment in the clicked row.
    """

    def callback(attr, old, new):
        if new:
            frame = table.source.data["frame_in"][new[0]]
            handle_jump_to_frame("", 0, frame)

    return callback


def clear_selections(table):
    """Callback generator for clearing the selected row(s) in the given table."""

    def callback(attr, old, new):
        table.source.selected.indices = []

    return callback


def create_tabs():
    """Returns the panel widget with tabs for different tables."""

    def update_stats():
        """Updates the statistics text."""

        stats.text = dedent(
            f"""
                Number of correct segments: {state.segments.get_correct_segment_count()}
                Number of incorrect segments: {state.segments.get_incorrect_segment_count()}
                Number of new segments: {state.segments.get_new_segments_count()}
                Accuracy: {"{:.2f}".format(state.segments.get_correct_incorrect_ratio() * 100)}%
            """
        )

    def handle_tab_switched(attr, old, new):
        """Callback for updating the visibility of the reset label button depending on the active tab."""

        # Defines which tabs should show the reset label button
        reset_tables = [
            "wrong_segments",
            "correct_segments",
            "new_segments",
        ]
        reset_btn = curdoc().get_model_by_name("reset-btn")
        active_tab = tabs_widget.tabs[new].name
        reset_btn.visible = active_tab in reset_tables
        tab_description.text = TABLES.get(tabs_widget.tabs[new].name, {}).get(
            "description", ""
        )

    # All tables share these columns
    columns = [
        TableColumn(field=c, title=c) for c in ["id", "frame_in", "frame_out", "class"]
    ]

    # Default settings for all tables
    table_settings = {
        "columns": columns,
        "index_position": None,
        "height": styles.TABLE_HEIGHT,
        "width": styles.TABLE_WIDTH,
        "tags": ["table"],
    }

    # == Table for trajectories on current frame ==
    trajectories_table = DataTable(
        source=state.trajectories.current_frame_view, **table_settings
    )

    # == Table for incorrect segments ==
    incorrect_segments_table = DataTable(
        source=state.segments.incorrect_view,
        # exclude the default columns
        **{key: table_settings[key] for key in table_settings if key != "columns"},
        # expand the default columns with a another one for comments
        columns=[*columns, TableColumn(field="comments", title="comments")],
    )

    # == Table for correct segments ==
    correct_segments_table = DataTable(
        source=state.segments.correct_view, **table_settings
    )

    # == Table for new segments ==
    new_segments_table = DataTable(source=state.segments.new_view, **table_settings)

    # Define names and descriptions for the tables created above
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
    # Register callbacks and create panels for all tables
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

    # Add another tab for statistics
    stats = PreText()
    update_stats()  # Set up the initial statistics
    stats_tab = Panel(child=stats, title="Statistics", name="stats")

    tabs_widget = Tabs(
        tabs=[
            *panels,
            stats_tab,
        ],
        height=280,
    )
    tabs_widget.on_change("active", handle_tab_switched)

    # In the intial state use the description of the first tab
    tab_description = Paragraph(text=TABLES[list(TABLES.keys())[0]]["description"])

    return [tab_description, tabs_widget]
