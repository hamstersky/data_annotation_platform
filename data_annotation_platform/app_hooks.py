import settings
import state
import os
import uuid
from segments_data import SegmentsData


def on_session_created(session_context):
    if "uid" in session_context.request._cookies:
        uid = session_context.request._cookies["uid"]
        settings.uid = uid
        filename = f"{uid}.pkl"
        path = os.path.join(os.getcwd(), "data", filename)
        if os.path.exists(path):
            settings.segments_path = path
    else:
        settings.uid = str(uuid.uuid4())
    state.segments = SegmentsData(settings.segments_path)
