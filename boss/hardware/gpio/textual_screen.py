"""Textual (Rich-based) debounced text screen backend.

Currently implements baseline of user stories:
 - US-TXT-01: textual backend option
 - US-TXT-02: non-blocking debounced rendering
 - US-TXT-03: API parity (display_text / clear_screen, duplicate suppression, alignment)
 - US-TXT-08: basic rendering metrics (avg/max/p95)
 - US-TXT-09: loop crash marks backend unavailable (for fallback)
 - US-TXT-13: env override handled in factory (not here)
 - US-TXT-14: image stub warning

Remaining stories (auto selection docs, splash sequencing, richer footer/app name, fallback orchestrator,
systemd hardening, extended tests & docs) will be layered incrementally.
"""

from __future__ import annotations
import logging
import threading
import time
import queue
from typing import Optional, List, Dict, Any

from boss.core.interfaces.hardware import ScreenInterface
from boss.core.models import HardwareConfig

logger = logging.getLogger(__name__)

try:  # pragma: no cover
    from rich.console import Console  # type: ignore
    from rich.text import Text as RichText  # type: ignore
    HAS_RICH = True
except Exception:  # pragma: no cover
    Console = object  # type: ignore
    RichText = object  # type: ignore
    HAS_RICH = False


class _Cmd:
    def __init__(self, kind: str, payload: Dict[str, Any]):
        self.kind = kind
        self.payload = payload


class TextualScreen(ScreenInterface):
    """Threaded debounced text rendering backend (Rich console)."""

    def __init__(self, hardware_config: HardwareConfig, debounce_ms: int = 50):
        self.hardware_config = hardware_config
        self._available = False
        self._screen_width = hardware_config.screen_width
        self._screen_height = hardware_config.screen_height
        self._console: Optional[Console] = Console() if HAS_RICH else None  # type: ignore
        self._queue: "queue.Queue[_Cmd]" = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._debounce_ms = debounce_ms
        self._last_render_text: Optional[str] = None
        self._render_durations: List[float] = []
        self._metrics_lock = threading.Lock()
    # Footer concept removed (decision: no footer/status line)

    # ---- ScreenInterface ----
    def initialize(self) -> bool:
        if not HAS_RICH:
            logger.warning("TextualScreen: rich not available; backend disabled")
            return False
        self._available = True
        self._thread = threading.Thread(target=self._loop, name="TextualScreenLoop", daemon=True)
        self._thread.start()
        logger.info("TextualScreen initialized (debounce=%dms)" % self._debounce_ms)
        return True

    def cleanup(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._available = False
        logger.debug("TextualScreen cleaned up")

    @property
    def is_available(self) -> bool:  # pragma: no cover
        return self._available and HAS_RICH

    def display_text(self, text: str, font_size: int = 24, color: str = "white", background: str = "black", align: str = "center", wrap: bool = True, wrap_width: Optional[int] = None) -> None:
        if not self.is_available:
            return
        if text == self._last_render_text:  # duplicate suppression
            return
        self._queue.put(_Cmd("text", {"text": text, "color": color, "background": background, "align": align, "wrap": wrap, "wrap_width": wrap_width}))

    def display_image(self, image_path: str, scale: float = 1.0, position: tuple = (0, 0)) -> None:  # pragma: no cover simple
        if not hasattr(self, "_warned_image"):
            logger.info("TextualScreen: display_image not supported (text-only backend); use pillow backend for images")
            self._warned_image = True

    def clear_screen(self, color: str = "black") -> None:
        if not self.is_available:
            return
        self._queue.put(_Cmd("clear", {"color": color}))

    def get_screen_size(self) -> tuple:  # pragma: no cover
        return self._screen_width, self._screen_height

    # ---- Metrics ----
    def get_metrics(self) -> Dict[str, Any]:
        with self._metrics_lock:
            if not self._render_durations:
                return {"render_count": 0}
            durations = list(self._render_durations)
        rc = len(durations)
        avg = sum(durations) / rc
        mx = max(durations)
        p95 = sorted(durations)[int(0.95 * (rc - 1))] if rc > 1 else mx
        return {"render_count": rc, "avg_ms": round(avg, 2), "max_ms": round(mx, 2), "p95_ms": round(p95, 2)}

    # Event bus attachment stub (footer removed)
    def attach_event_bus(self, event_bus) -> None:  # pragma: no cover simple
        return None

    # ---- Internal loop ----
    def _loop(self) -> None:
        pending: Optional[_Cmd] = None
        # footer removed; keep placeholder variable for backward compat logic simplicity
        last_flush = 0.0
        debounce = self._debounce_ms / 1000.0
        try:
            while not self._stop_event.is_set():
                try:
                    cmd = self._queue.get(timeout=0.05)
                    if cmd.kind != "footer":  # ignore deprecated footer cmds
                        pending = cmd
                except queue.Empty:
                    pass
                now = time.time()
                if pending and (now - last_flush >= debounce):
                    start = time.time()
                    self._execute(pending)
                    pending = None
                    dur = (time.time() - start) * 1000.0
                    with self._metrics_lock:
                        self._render_durations.append(dur)
                        if len(self._render_durations) > 150:
                            self._render_durations.pop(0)
                    last_flush = now
        except Exception as e:  # pragma: no cover
            logger.error(f"TextualScreen loop crashed: {e}")
            self._available = False

    def _execute(self, cmd: _Cmd) -> None:
        if self._console is None:
            return
        try:
            if cmd.kind == "clear":
                self._console.clear()
                return
            if cmd.kind == "text":
                p = cmd.payload
                justify = p.get("align", "left")
                raw_text = p.get("text", "")
                if p.get("wrap", True):
                    try:
                        import textwrap
                        # Determine effective width: if explicit wrap_width use it; else derive from configured width
                        eff_width = p.get("wrap_width")
                        if eff_width is None:
                            # Use configured default wrap width (screen_wrap_width_chars) if present
                            cfg_width = getattr(self.hardware_config, 'screen_wrap_width_chars', 80)
                            eff_width = int(cfg_width) if cfg_width else 80
                        wrapped_lines = []
                        for line in str(raw_text).splitlines():
                            wrapped_lines.extend(textwrap.wrap(line, width=int(eff_width)) or [""])
                        raw_text = "\n".join(wrapped_lines)
                    except Exception as e:  # pragma: no cover
                        logger.debug(f"Wrapping failed: {e}")
                rt = RichText(raw_text, style=f"{p.get('color','white')} on {p.get('background','black')}")  # type: ignore
                self._console.clear()
                self._console.print(rt, justify=justify if justify in ("left", "center", "right") else "left")
                self._last_render_text = p.get("text", "")
                return
            # footer commands ignored (deprecated)
        except Exception as e:  # pragma: no cover
            logger.debug(f"TextualScreen render error: {e}")
