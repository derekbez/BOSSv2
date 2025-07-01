"""
Hello World mini-app template for B.O.S.S. (event-driven)
Displays 'Hello World!' when the red button is pressed.
"""
def run(stop_event, api):
    def on_red_button(event_type, payload):
        api.screen.display_text("Hello World!", align='center')
    api.event_bus.subscribe("button_press", on_red_button, filter={"button": "red"})
    stop_event.wait()
