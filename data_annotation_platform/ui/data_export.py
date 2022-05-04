from bokeh.models import Button, ColumnDataSource, CustomJS
import os
import ui.state as state


def create_download_btn():
    dl_button = Button(label="Download")
    source = ColumnDataSource(state.segments.get_data())
    dl_button.js_on_event(
        "button_click",
        CustomJS(
            args=dict(source=source),
            code=open(os.path.join(os.path.dirname(__file__), "download.js")).read(),
        ),
    )
    return dl_button
