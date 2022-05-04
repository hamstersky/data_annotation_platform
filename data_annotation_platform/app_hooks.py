import os
import uuid
import settings
import ui.state as state


def on_session_created(session_context):
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
