from bokeh.models import CustomJS, Button
from bokeh.plotting import curdoc

import settings
import ui.state as state


def create_save_progress_btn():
    """Returns button for saving progress and add automatic periodic save."""

    # JavaScript callback to save a cookie in the user's browser
    store_cookie = CustomJS(
        args=dict(uid=state.uid),
        code="""
            document.cookie = "uid=" + uid + ";max-age=31536000;SameSite=Strict"
        """,
    )

    def save():
        save_btn.name = f"{save_btn.name}1"
        # Save the data on the server
        state.segments.export_data(f"{settings.project_path}/data/{state.uid}")

    save_btn = Button(label="Save progress", margin=(100, 0, 0, 0))
    save_btn.on_click(save)

    # Bokeh doesn't allow for arbitrary JS exectution, it can only be done via a callback
    # As a workaround, the button's name property will be updated to trigger the callback
    save_btn.js_on_change("name", store_cookie)

    # Automatic saves every minute
    curdoc().add_periodic_callback(save, 60000)
    return save_btn
