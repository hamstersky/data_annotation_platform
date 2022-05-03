from bokeh.models import CustomJS, Button
from bokeh.plotting import curdoc

import state


def save_progress():
    store_cookie = CustomJS(
        args=dict(uid=state.uid),
        code="""
            console.log('hi')
            document.cookie = "uid=" + uid + ";max-age=31536000;SameSite=Strict"
        """,
    )

    def save():
        # Trigger JS script
        save_btn.name = f"{save_btn.name}1"
        state.segments.export_data(f"./data/{state.uid}")

    save_btn = Button(label="Save progress", margin=(100, 0, 0, 0))
    save_btn.on_click(save)
    save_btn.js_on_change("name", store_cookie)
    curdoc().add_periodic_callback(save, 60000)
    return save_btn
