"""
Example mini-app for B.O.S.S. Implements required API interface.
"""
def run(stop_event, api):
    api.display.show_message("Hello from Example App!")
    while not stop_event.is_set():
        # App logic here
        pass
