"""
Event Handlers for B.O.S.S. system
All event-driven logic for hardware and app events is centralized here for maintainability.
"""

import sys
import os
from typing import Any, Callable
import time
import logging

logger = logging.getLogger("boss.core.event_handlers")

def on_display_update(display):
    def handler(event_type: str, payload: dict):
        val = payload.get("value")
        if val is not None and display:
            try:
                n = int(val)
                if hasattr(display, 'show_number'):
                    display.show_number(n)
                else:
                    logger.warning("Display object missing show_number method.")
            except Exception:
                if hasattr(display, 'show_message'):
                    display.show_message(str(val))
                else:
                    logger.warning("Display object missing show_message method.")
    return handler

def handle_button_pressed():
    """
    Generic handler for all button presses. Logs the button and event.
    Extend this for global button actions if needed.
    """
    def handler(event_type: str, payload: dict):
        button_id = payload.get("button_id")
        logger.info(f"Button pressed: {button_id} | Payload: {payload}")
    return handler

def on_go_button_pressed(switch, app_mappings, app_runner, api):
    def handler(event_type: str, payload: dict):
        if payload.get("button_id") == "main":
            value = switch.read_value() if switch else 0
            app_name = app_mappings.get(str(value))
            logger.info(f"Go button pressed (event). Switch value: {value}, launching app: {app_name}")
            if app_name:
                app_runner.run_app(app_name, api=api)
            else:
                logger.info(f"No app mapped for value {value}.")
    return handler

def handle_display_update(seg_display):
    """
    Handles 'switch_change' events to update the 7-segment display.
    Args:
        seg_display: The display object to update.
    """
    def handler(event_type: str, payload: dict):
        if seg_display and hasattr(seg_display, 'show_number'):
            seg_display.show_number(payload["value"])
    return handler

def handle_led_set(led_red, led_yellow, led_green, led_blue):
    def handler(event_type: str, payload: dict):
        color = payload.get("color")
        state = payload.get("state")
        if color == "red" and led_red:
            led_red.on() if state else led_red.off()
        elif color == "yellow" and led_yellow:
            led_yellow.on() if state else led_yellow.off()
        elif color == "green" and led_green:
            led_green.on() if state else led_green.off()
        elif color == "blue" and led_blue:
            led_blue.on() if state else led_blue.off()
    return handler

def handle_switch_set(switch, display):
    def handler(event_type: str, payload: dict):
        value = payload.get("value")
        logger.info(f"[WebUI] Switch set to {value} via web UI.")
        print(f"[WebUI] Switch set to {value} via web UI.")
        # Update the switch_reader mock (if present)
        if hasattr(switch, 'set_value'):
            # Prevent feedback loop: only set if value is different
            try:
                current = switch.read_value()
            except Exception:
                current = None
            if value != current:
                switch.set_value(value)
        # Do NOT update the display here; display_update_handler (on switch_change) will handle it.
        # Do NOT publish another switch_change event here; APISwitchReader.set_value does it.
    return handler


def handle_system_shutdown(app_runner, cleanup, logger):
    def handler(event_type, payload):
        reason = payload.get('reason', 'unknown')
        logger.critical(f"[SHUTDOWN HANDLER] System shutdown event received. Reason: {reason}")
        try:
            cleanup()
        except Exception as e:
            logger.error(f"[SHUTDOWN HANDLER] Cleanup error: {e}")
        if app_runner and hasattr(app_runner, 'stop_app'):
            try:
                app_runner.stop_app()
            except Exception as e:
                logger.warning(f"Error stopping app_runner during shutdown: {e}")
        logger.critical(f"[SHUTDOWN HANDLER] After app_runner.stop_app(). About to exit for reason: {reason}")
        if reason == 'reboot':
            logger.critical("[SHUTDOWN HANDLER] Rebooting system now...")
            os.system('sudo reboot')
        elif reason == 'poweroff':
            logger.critical("[SHUTDOWN HANDLER] Powering off system now...")
            os.system('sudo poweroff')
        elif reason == 'exit_to_os':
            logger.critical("[SHUTDOWN HANDLER] Exiting BOSS to OS shell...")
            sys.exit(0)
        else:
            logger.critical(f"[SHUTDOWN HANDLER] Unknown shutdown reason: {reason}. Exiting BOSS main loop.")
            sys.exit(0)
    return handler