import os

from bokeh.models import Button, ColumnDataSource, CustomJS

import ui.state as state


def create_download_btn():
    """Returns a button widget for downloading the annotated dataset in a csv format."""

    dl_button = Button(label="Download")
    source = ColumnDataSource(state.segments.data)
    dl_button.js_on_event(
        "button_click",
        CustomJS(
            args=dict(source=source),
            code=open(os.path.join(os.path.dirname(__file__), "download.js")).read(),
        ),
    )
    return dl_button
