import os
import uuid

import settings
import ui.state as state

# app_hooks.py is a special file in Bokeh that allows triggering callbacks
# at specific points of the application lifecycle


def on_session_created(session_context):
    """
    Checks for a session cookie in the user's browser.
    If the cookie exists, load the relevant user data. Otherwise start a new session.
    """

    if "uid" in session_context.request._cookies:
        uid = session_context.request._cookies["uid"]
        state.uid = uid
        filename = f"{uid}.pkl"
        path = f"{settings.project_path}/data/{filename}"
        if os.path.exists(path):
            settings.segments_path = path
    else:
        state.uid = str(uuid.uuid4())
        settings.segments_path = f"{settings.project_path}/data/segments.pkl"
