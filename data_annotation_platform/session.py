from bokeh.models import PreText, CustomJS, Button
from bokeh.plotting import curdoc

import settings
import state
import styles


def save_progress():
    # Bokeh doesn't provide an option to call arbitrary JS, it always requires a callback
    # As a workaround, create a text widget which is not visible
    # When the text changes, it trigger Custom JS code
    store_cookie_trigger = PreText(text="", visible=False)

    store_cookie = CustomJS(
        args=dict(uid=state.uid),
        code="""
            document.cookie = "uid=" + uid + ";max-age=31536000;SameSite=Strict"
        """,
    )
    store_cookie_trigger.js_on_change("text", store_cookie)

    def save():
        # Trigger the callback
        store_cookie_trigger.text = f"{store_cookie_trigger.text}1"
        state.segments.export_data(f"./data/{state.uid}")

    save_btn = Button(
        label="Save progress", height=styles.NAV_BTN_HEIGHT, width_policy="min"
    )
    save_btn.on_click(save)
    curdoc().add_periodic_callback(save, 60000)
    return save_btn
