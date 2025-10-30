from boss.ui.api.web_ui import create_app

# Create a lightweight ASGI app using an empty hardware dict and no event bus.
# This is useful for running the Web UI in isolation for testing.
app = create_app({}, None)
