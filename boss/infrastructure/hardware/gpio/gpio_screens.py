"""
GPIO screen implementations for BOSS (Pillow and Rich backends)
"""
from boss.domain.interfaces.hardware import ScreenInterface
from boss.domain.models.config import HardwareConfig
import logging
import sys
import io
from typing import Optional, Any

logger = logging.getLogger(__name__)

# --- Rich Screen Implementation ---
class RichFramebufferWrapper:
    """Wrapper to redirect Rich console output to framebuffer on Raspberry Pi."""
    
    def __init__(self, framebuffer_path="/dev/fb0"):
        self.framebuffer_path = framebuffer_path
        self._buffer = io.StringIO()
        self._framebuffer = None
        
    def write(self, text):
        """Write text to buffer and optionally to framebuffer."""
        self._buffer.write(text)
        # TODO: Convert text to framebuffer format and write to /dev/fb0
        # This requires character-to-bitmap conversion for the target display
        return len(text)
    
    def flush(self):
        """Flush any buffered output."""
        if self._framebuffer:
            try:
                self._framebuffer.flush()
            except:
                pass

try:
    from rich.console import Console
    from rich.text import Text
    from rich.table import Table
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.panel import Panel
    from rich.tree import Tree
    from rich.syntax import Syntax
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    # Create loose-typed dummies for graceful fallback (avoid static errors)
    from typing import Any
    Console: Any = None
    Text: Any = None
    Table: Any = None
    Progress: Any = None
    Panel: Any = None
    Tree: Any = None
    Syntax: Any = None

class PerformanceMonitor:
    """Monitor Rich backend performance metrics."""
    
    def __init__(self):
        self.metrics = {
            'display_text_calls': 0,
            'display_table_calls': 0,
            'display_progress_calls': 0,
            'display_panel_calls': 0,
            'display_tree_calls': 0,
            'display_code_calls': 0,
            'display_markup_calls': 0,
            'total_render_time': 0.0,
            'average_render_time': 0.0,
            'peak_render_time': 0.0
        }
        self.total_calls = 0
    
    def record_call(self, operation: str, render_time: float):
        """Record a display operation and its render time."""
        self.metrics[f'{operation}_calls'] += 1
        self.total_calls += 1
        self.metrics['total_render_time'] += render_time
        self.metrics['average_render_time'] = self.metrics['total_render_time'] / self.total_calls
        self.metrics['peak_render_time'] = max(self.metrics['peak_render_time'], render_time)
        
        # Log performance warnings
        if render_time > 0.1:  # 100ms threshold
            logger.warning(f"Slow Rich render: {operation} took {render_time:.3f}s")
    
    def get_metrics(self) -> dict:
        """Get current performance metrics."""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset all performance metrics."""
        for key in self.metrics:
            self.metrics[key] = 0.0 if 'time' in key else 0
        self.total_calls = 0

def performance_timer(operation: str):
    """Decorator to time Rich operations for performance monitoring."""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, '_perf_monitor'):
                return func(self, *args, **kwargs)
            
            import time
            start_time = time.time()
            try:
                result = func(self, *args, **kwargs)
                return result
            finally:
                render_time = time.time() - start_time
                self._perf_monitor.record_call(operation, render_time)
        return wrapper
    return decorator

class GPIORichScreen(ScreenInterface):
    """Rich-based screen implementation for HDMI output."""
    def __init__(self, hardware_config: HardwareConfig):
        self.hardware_config = hardware_config
        self._available = False
        self._screen_width = hardware_config.screen_width
        self._screen_height = hardware_config.screen_height
        
        if HAS_RICH:
            # Setup console with framebuffer redirection on Raspberry Pi
            try:
                # Try to detect if we're on Raspberry Pi with framebuffer
                import os
                if os.path.exists("/dev/fb0"):
                    # Use framebuffer wrapper for physical display
                    self._fb_wrapper = RichFramebufferWrapper()
                    self._console = Console(
                        file=self._fb_wrapper,
                        width=hardware_config.screen_width // 8,  # Convert pixels to character width
                        height=hardware_config.screen_height // 16,  # Convert pixels to character height
                        force_terminal=True,
                        legacy_windows=False
                    )
                    logger.info("Rich console configured for framebuffer output")
                else:
                    # Standard console for development/testing
                    self._console = Console(
                        record=True,
                        width=hardware_config.screen_width // 8,
                        height=hardware_config.screen_height // 16,
                        force_terminal=True
                    )
                    logger.info("Rich console configured for standard output")
            except Exception as e:
                logger.warning(f"Failed to setup Rich framebuffer redirection: {e}")
                # Fallback to standard console
                self._console = Console(
                    record=True,
                    width=hardware_config.screen_width // 8,
                    height=hardware_config.screen_height // 16
                )
        else:
            self._console = None
            logger.warning("Rich library not available, screen functionality limited")

    def initialize(self) -> bool:
        if not HAS_RICH:
            logger.error("Rich library not available for GPIORichScreen")
            return False
        
        self._available = True
        logger.info(f"GPIORichScreen initialized ({self._screen_width}x{self._screen_height})")
        return True

    def cleanup(self) -> None:
        self._available = False
        if self._console and HAS_RICH:
            self._console.clear()
        logger.debug("GPIORichScreen cleaned up")

    @property
    def is_available(self) -> bool:
        return self._available and HAS_RICH

    def clear_screen(self, color: str = "black") -> None:
        if not self._available:
            return
        if self._console is None:
            return
        self._console.clear()  # type: ignore[union-attr]
        self._console.print("", style=f"on {color}")  # type: ignore[union-attr]
        logger.info(f"GPIORichScreen cleared with color: {color}")

    def display_text(self, text: str, font_size: int = 48, color: str = "white", background: str = "black", align: str = "center") -> None:
        if not self._available:
            logger.warning("GPIORichScreen not available for display_text")
            return
        style = f"{color} on {background}"
        rich_text = Text(text, style=style) if HAS_RICH else text
        if self._console is None:
            return
        self._console.clear()  # type: ignore[union-attr]
        if align == "center":
            self._console.print(rich_text, justify="center")  # type: ignore[union-attr]
        elif align == "right":
            self._console.print(rich_text, justify="right")  # type: ignore[union-attr]
        else:
            self._console.print(rich_text, justify="left")  # type: ignore[union-attr]
        logger.info(f"GPIORichScreen text displayed: '{text}' (color: {color}, align: {align})")

    def display_image(self, image_path: str, scale: float = 1.0, position: tuple = (0, 0)) -> None:
        if not self._available:
            return
        if self._console is None:
            return
        self._console.print(f"[Image: {image_path}]", style="bold yellow")  # type: ignore[union-attr]
        logger.info(f"GPIORichScreen image placeholder: {image_path}")

    def get_screen_size(self) -> tuple:
        return (self._screen_width, self._screen_height)

    # Rich-specific enhanced features
    def display_table(self, table_data: dict, title: Optional[str] = None) -> None:
        """Display a Rich table with optional title."""
        if not self._available:
            logger.warning("GPIORichScreen not available for display_table")
            return
        
        table = Table(title=title)
        
        # Add columns
        if table_data and len(table_data) > 0:
            first_row = next(iter(table_data.values()))
            if isinstance(first_row, dict):
                for col_name in first_row.keys():
                    table.add_column(str(col_name), style="cyan")
                
                # Add rows
                for row_name, row_data in table_data.items():
                    table.add_row(str(row_name), *[str(val) for val in row_data.values()])
            else:
                table.add_column("Key", style="cyan")
                table.add_column("Value", style="magenta")
                for key, value in table_data.items():
                    table.add_row(str(key), str(value))
        
        if self._console is None:
            return
        self._console.clear()  # type: ignore[union-attr]
        self._console.print(table)  # type: ignore[union-attr]
        logger.info(f"GPIORichScreen table displayed with title: {title}")

    def display_progress(self, progress_value: float, description: str = "Progress") -> None:
        """Display a progress bar."""
        if not self._available:
            logger.warning("GPIORichScreen not available for display_progress")
            return
        
        # Clamp progress value between 0 and 100
        progress_value = max(0, min(100, progress_value))
        if self._console is None or not HAS_RICH:
            return
        with Progress(  # type: ignore[misc]
            TextColumn("[progress.description]{task.description}"),  # type: ignore[name-defined]
            BarColumn(),  # type: ignore[name-defined]
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),  # type: ignore[name-defined]
            console=self._console  # type: ignore[arg-type]
        ) as progress:
            task = progress.add_task(description, total=100)
            progress.update(task, completed=progress_value)
        
        logger.info(f"GPIORichScreen progress displayed: {progress_value}% - {description}")

    def display_panel(self, content: str, title: Optional[str] = None, border_style: str = "blue") -> None:
        """Display content within a bordered panel."""
        if not self._available:
            logger.warning("GPIORichScreen not available for display_panel")
            return
        
        panel = Panel(content, title=title, border_style=border_style)
        if self._console is None:
            return
        self._console.clear()  # type: ignore[union-attr]
        self._console.print(panel)  # type: ignore[union-attr]
        logger.info(f"GPIORichScreen panel displayed with title: {title}")

    def display_tree(self, tree_data: dict, root_label: str = "Root") -> None:
        """Display hierarchical data as a tree structure."""
        if not self._available:
            logger.warning("GPIORichScreen not available for display_tree")
            return
        
        tree = Tree(root_label)
        
        def add_tree_items(node, data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        branch = node.add(str(key))
                        add_tree_items(branch, value)
                    else:
                        node.add(f"{key}: {value}")
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        branch = node.add(f"Item {i}")
                        add_tree_items(branch, item)
                    else:
                        node.add(str(item))
        
        add_tree_items(tree, tree_data)
        if self._console is None:
            return
        self._console.clear()  # type: ignore[union-attr]
        self._console.print(tree)  # type: ignore[union-attr]
        logger.info(f"GPIORichScreen tree displayed with root: {root_label}")

    def display_code(self, code: str, language: str = "python", theme: str = "monokai") -> None:
        """Display syntax-highlighted code."""
        if not self._available:
            logger.warning("GPIORichScreen not available for display_code")
            return
        
        syntax = Syntax(code, language, theme=theme, line_numbers=True)
        if self._console is None:
            return
        self._console.clear()  # type: ignore[union-attr]
        self._console.print(syntax)  # type: ignore[union-attr]
        logger.info(f"GPIORichScreen code displayed in {language} with {theme} theme")

    def display_markup(self, markup_text: str) -> None:
        """Display Rich markup text with formatting."""
        if not self._available:
            logger.warning("GPIORichScreen not available for display_markup")
            return
        
        if self._console is None:
            return
        self._console.clear()  # type: ignore[union-attr]
        self._console.print(markup_text)  # type: ignore[union-attr]
        logger.info("GPIORichScreen markup displayed")

# --- Pillow Screen Implementation ---
class GPIOPillowScreen(ScreenInterface):
    """GPIO HDMI screen implementation using Pillow framebuffer."""
    def __init__(self, hardware_config: HardwareConfig):
        self.hardware_config = hardware_config
        self._available = False
        self._fb_path = "/dev/fb0"
        self._framebuffer = None
        self._image = None
        self._draw = None
        self._font = None
        self._screen_width, self._screen_height = self._detect_fb_size(hardware_config)
        self._fb_bpp = 16

    def _detect_fb_size(self, hardware_config):
        try:
            with open("/sys/class/graphics/fb0/virtual_size", "r") as f:
                size_str = f.read().strip()
                width, height = map(int, size_str.split(","))
                logger.info(f"Detected framebuffer size: {width}x{height}")
                return width, height
        except Exception as e:
            logger.warning(f"Could not auto-detect framebuffer size, using config: {e}")
            return hardware_config.screen_width, hardware_config.screen_height

    def initialize(self) -> bool:
        try:
            fb_width, fb_height = self._screen_width, self._screen_height
            fb_bpp = 16
            try:
                with open("/sys/class/graphics/fb0/virtual_size", "r") as f:
                    size_str = f.read().strip()
                    fb_width, fb_height = map(int, size_str.split(","))
                with open("/sys/class/graphics/fb0/bits_per_pixel", "r") as f:
                    fb_bpp = int(f.read().strip())
                # persist detected values for write path
                self._screen_width, self._screen_height = fb_width, fb_height
                self._fb_bpp = fb_bpp
            except Exception as e:
                logger.warning(f"Could not auto-detect framebuffer geometry/bpp: {e}")
            if (self._screen_width, self._screen_height) != (fb_width, fb_height):
                logger.warning(f"Screen config {self._screen_width}x{self._screen_height} does not match framebuffer {fb_width}x{fb_height}. Update config or HDMI settings to match.")
            if fb_bpp not in (16, 24, 32):
                logger.warning(f"Unsupported framebuffer bpp {fb_bpp}. Attempting best-effort write.")
            from PIL import Image, ImageDraw, ImageFont
            self._image = Image.new("RGB", (self._screen_width, self._screen_height), "black")
            self._draw = ImageDraw.Draw(self._image)
            try:
                self._font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
            except Exception:
                self._font = ImageFont.load_default()
            self._available = True
            logger.info("GPIOPillowScreen initialized (Pillow framebuffer)")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize GPIOPillowScreen (Pillow): {e}")
            return False

    def cleanup(self) -> None:
        self._available = False
        self._image = None
        self._draw = None
        self._font = None

    @property
    def is_available(self) -> bool:
        return self._available

    def _write_to_framebuffer(self):
        try:
            if self._image is None:
                return
            img = self._image.convert("RGB")
            width, height = img.size
            fb_bytes = None
            # Choose conversion based on framebuffer bpp
            try:
                if self._fb_bpp == 32:
                    # Most RPi KMS uses XRGB8888 or ARGB8888; BGRX works well for many fb drivers
                    fb_bytes = img.tobytes("raw", "BGRX")
                elif self._fb_bpp == 24:
                    fb_bytes = img.tobytes("raw", "BGR")
                else:
                    # default to 16bpp RGB565
                    fb_bytes = img.tobytes("raw", "BGR;16")
            except Exception as e:
                logger.debug(f"Fast conversion failed ({e}); falling back to manual pack for {self._fb_bpp}bpp")
                arr: Any = img.load()
                if self._fb_bpp == 32:
                    fb_bytes = bytearray()
                    for y in range(height):
                        for x in range(width):
                            r, g, b = arr[x, y]  # type: ignore[index]
                            # B,G,R, padding
                            fb_bytes.extend((b, g, r, 0))
                elif self._fb_bpp == 24:
                    fb_bytes = bytearray()
                    for y in range(height):
                        for x in range(width):
                            r, g, b = arr[x, y]  # type: ignore[index]
                            fb_bytes.extend((b, g, r))
                else:
                    fb_bytes = bytearray()
                    for y in range(height):
                        for x in range(width):
                            r, g, b = arr[x, y]  # type: ignore[index]
                            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                            fb_bytes.append((rgb565 >> 8) & 0xFF)
                            fb_bytes.append(rgb565 & 0xFF)
            # Write to framebuffer from start
            with open(self._fb_path, "rb+") as fb:
                fb.seek(0)
                fb.write(fb_bytes)
        except Exception as e:
            logger.error(f"Failed to write to framebuffer: {e}")

    def clear_screen(self, color: str = "black") -> None:
        if not self.is_available or self._draw is None:
            return
        # Fast path: solid fill without text metrics
        self._draw.rectangle([(0, 0), (self._screen_width, self._screen_height)], fill=color)
        self._write_to_framebuffer()

    def display_text(self, text: str, font_size: int = 48, color: str = "white", background: str = "black", align: str = "center") -> None:
        if not self.is_available:
            logger.warning("GPIOPillowScreen not available for display_text")
            return
        from PIL import ImageFont
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except Exception:
            font = self._font or ImageFont.load_default()
        self.clear_screen(background)
        try:
            if self._draw is None:
                text_w, text_h = 0, 0
            else:
                bbox = self._draw.textbbox((0, 0), text, font=font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]
        except Exception as e:
            logger.error(f"Failed to calculate text bounding box: {e}")
            text_w, text_h = 0, 0
        # Match Rich behavior: top-aligned; only horizontal justification changes
        margin = 0
        if align == "center":
            x = (self._screen_width - text_w) // 2
        elif align == "right":
            x = max(margin, self._screen_width - text_w - margin)
        else:
            x = margin
        y = margin  # top-aligned for parity with Rich's default rendering
        if self._draw is None:
            return
        self._draw.text((x, y), text, font=font, fill=color)
        self._write_to_framebuffer()

    def display_image(self, image_path: str, scale: float = 1.0, position: tuple = (0, 0)) -> None:
        logger.info(f"TODO: display_image not yet implemented. Would display: {image_path}")

    def get_screen_size(self) -> tuple:
        return (self._screen_width, self._screen_height)
