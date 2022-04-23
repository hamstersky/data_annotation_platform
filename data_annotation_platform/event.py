from collections import defaultdict


# _callbacks = {}


# class Event:
#     @staticmethod
#     def on(event_name, f):
#         _callbacks[event_name] = _callbacks.get(event_name, []) + [f]
#         return f

#     @staticmethod
#     def emit(event_name, *data):
#         [f(*data) for f in _callbacks.get(event_name, [])]

#     @staticmethod
#     def off(event_name, f):
#         _callbacks.get(event_name, []).remove(f)

#     @staticmethod
#     def list():
#         print(_callbacks)


subscribers = defaultdict(list)


def subscribe(event_name, f):
    subscribers[event_name].append(f)


def emit(event_name, **kwargs):
    for f in subscribers.get(event_name, []):
        f(**kwargs)
