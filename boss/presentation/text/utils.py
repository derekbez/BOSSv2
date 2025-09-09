"""Shared text formatting utilities for mini-apps.

Provides deterministic wrapping so apps can disable backend wrapping
(`wrap=False`) and avoid double-wrap artifacts. Keep logic minimal and
UI-agnostic.
"""
from __future__ import annotations
from typing import List, Iterable, Callable, Optional
import textwrap

def estimate_char_columns(screen_width_px: int, font_size: int = 18) -> int:
    """Estimate character columns from pixel width.

    Heuristic: monospace glyph ~0.53 * font_size px wide; add small safety margin.
    Clamped to a practical range.
    """
    if screen_width_px <= 0:
        return 80
    approx_glyph = max(6.0, 0.53 * font_size)
    cols = int(screen_width_px / approx_glyph) - 2
    return max(40, min(cols, 180))

def wrap_with_prefix(text: str, prefix: str, width: int) -> List[str]:
    """Wrap a paragraph so first line has prefix and following lines align."""
    body_width = max(10, width - len(prefix))
    raw = textwrap.wrap(text, width=body_width) or [text]
    out: List[str] = []
    for i, seg in enumerate(raw):
        if i == 0:
            out.append(prefix + seg)
        else:
            out.append(' ' * len(prefix) + seg)
    return out

def wrap_events(events: Iterable[tuple[str, str]], width: int) -> List[str]:
    """Wrap (year, description) sequence into list of lines."""
    lines: List[str] = []
    for year, desc in events:
        prefix = f"{year}: "
        lines.extend(wrap_with_prefix(desc, prefix, width))
    return lines

def wrap_plain(text: str, width: int) -> List[str]:
    """Wrap a single block of text into lines."""
    return textwrap.wrap(text, width=width) or [text]

def wrap_paragraphs(paragraphs: Iterable[str], width: int, sep_blank: bool = True) -> List[str]:
    """Wrap multiple paragraphs preserving blank line separation."""
    out: List[str] = []
    first = True
    for p in paragraphs:
        p = (p or '').strip()
        if not p:
            continue
        if not first and sep_blank:
            out.append("")
        out.extend(wrap_plain(p, width))
        first = False
    return out


class TextPaginator:
    """Utility to manage a list of pre-wrapped lines with paging.

    Responsibilities:
      * Track current page
      * Provide current slice of lines
      * Expose navigation state (has_prev/has_next)
      * Optional LED updater callback (color -> bool) invoked on state changes
    """

    def __init__(self, lines: List[str], per_page: int, led_update: Optional[Callable[[str, bool], None]] = None,
                 prev_color: str = 'yellow', next_color: str = 'blue'):
        self._lines = lines
        self._per_page = max(1, per_page)
        self._page = 0
        self._led_update = led_update
        self._prev_color = prev_color
        self._next_color = next_color
        self._update_leds()

    # ---- Data mutation ----
    def set_lines(self, lines: List[str]) -> None:
        self._lines = lines
        if self._page >= self.total_pages:
            self._page = max(0, self.total_pages - 1)
        self._update_leds()

    # ---- Properties ----
    @property
    def page(self) -> int:
        return self._page

    @property
    def total_pages(self) -> int:
        if not self._lines:
            return 1
        return (len(self._lines) - 1) // self._per_page + 1

    def has_prev(self) -> bool:
        return self._page > 0

    def has_next(self) -> bool:
        return self._page < self.total_pages - 1

    # ---- Navigation ----
    def next(self) -> bool:
        if self.has_next():
            self._page += 1
            self._update_leds()
            return True
        return False

    def prev(self) -> bool:
        if self.has_prev():
            self._page -= 1
            self._update_leds()
            return True
        return False

    def reset(self) -> None:
        self._page = 0
        self._update_leds()

    # ---- Data access ----
    def page_lines(self) -> List[str]:
        if not self._lines:
            return []
        start = self._page * self._per_page
        end = start + self._per_page
        return self._lines[start:end]

    def _update_leds(self) -> None:
        if self._led_update:
            self._led_update(self._prev_color, self.has_prev())
            self._led_update(self._next_color, self.has_next())
