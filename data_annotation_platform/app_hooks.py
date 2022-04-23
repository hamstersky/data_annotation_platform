import session
import os
import uuid


def on_session_created(session_context):
    if "uid" in session_context.request._cookies:
        uid = session_context.request._cookies["uid"]
        session.uid = uid
        filename = f"{uid}.pkl"
        path = os.path.join(os.getcwd(), "data", filename)
        if os.path.exists(path):
            session.segments_path = path
    else:
        session.uid = str(uuid.uuid4())
