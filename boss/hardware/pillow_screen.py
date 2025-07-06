"""
Optimized PillowScreen for B.O.S.S. (HDMI framebuffer, Pi 3+)
- Fast numpy framebuffer conversion
- TTF font support
- Mock mode for dev/testing
- Thread-safe
- Display text or images
"""

# --- Hardware import fallback logic ---
import sys
try:
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
except ImportError:
    Image = ImageDraw = ImageFont = np = None

import os
import threading
import struct
import mmap
try:
    import fcntl
except ImportError:
    fcntl = None

class PillowScreen:
    FONT_SIZE_LARGEST = 64
    FONT_SIZE_LARGER = 48
    FONT_SIZE_DEFAULT = 32
    FONT_SIZE_SMALLER = 24
    FONT_SIZE_SMALLEST = 16  # Default font size

    def __init__(self, width=1024, height=600, stride=2048, bpp=2, fbdev="/dev/fb0", mock=False):
        self.width = width
        self.height = height
        self.stride = stride
        self.bpp = bpp
        self.fbdev = fbdev
        self.mock = mock
        self.lock = threading.RLock()  # Use re-entrant lock to avoid deadlocks
        if Image is not None and ImageDraw is not None and ImageFont is not None:
            self.image = Image.new("RGB", (self.width, self.height), (0, 0, 0))
            self.draw = ImageDraw.Draw(self.image)
            self.font = ImageFont.load_default()
        else:
            self.image = None
            self.draw = None
            self.font = None
        self.fb = None
        self.fb_mmap = None
        self.cursor_y = 0  # Track current y position for print_line
        if not self.mock and self.image is not None and fcntl is not None:
            self._open_fb()
        elif not self.mock:
            print("[PillowScreen] MOCK MODE: No framebuffer access (missing fcntl or image libs).")

    def _open_fb(self):
        self.fb = open(self.fbdev, "rb+")
        try:
            FBIOGET_VSCREENINFO = 0x4600
            FBIOGET_FSCREENINFO = 0x4602
            vinfo = fcntl.ioctl(self.fb, FBIOGET_VSCREENINFO, b'\x00' * 160)
            finfo = fcntl.ioctl(self.fb, FBIOGET_FSCREENINFO, b'\x00' * 64)
            xres = struct.unpack_from('I', vinfo, 0)[0]
            yres = struct.unpack_from('I', vinfo, 4)[0]
            bits_per_pixel = struct.unpack_from('I', vinfo, 24)[0]
            line_length = struct.unpack_from('I', finfo, 8)[0]
        except Exception:
            xres = yres = bits_per_pixel = line_length = 0
        if xres > 0 and yres > 0 and line_length > 0 and bits_per_pixel > 0:
            self.width = xres
            self.height = yres
            self.stride = line_length
            self.bpp = bits_per_pixel // 8
            print("[PillowScreen] Using detected framebuffer parameters.")
        else:
            print("[PillowScreen] WARNING: Auto-detect failed, using manual framebuffer parameters.")
        print(f"[PillowScreen] Framebuffer info: width={self.width} height={self.height} stride={self.stride} bpp={self.bpp}")
        self.fb_size = self.stride * self.height
        self.fb_mmap = mmap.mmap(self.fb.fileno(), self.fb_size)

    def clear(self, color=(0,0,0)):
        with self.lock:
            if self.image is not None:
                self.image.paste(color, [0, 0, self.width, self.height])
            self.cursor_y = 0  # Reset cursor on clear
            self.refresh()

    def display_text(self, text, color=(255,255,255), size=48, align='center', font_name=None):
        with self.lock:
            self.clear()
            font = self._get_font(font_name, size)
            draw = ImageDraw.Draw(self.image)
            # Multi-line support
            lines = text.split('\n')
            total_height = sum([draw.textbbox((0,0), line, font=font)[3] for line in lines])
            y = (self.height - total_height) // 2
            for line in lines:
                bbox = draw.textbbox((0,0), line, font=font)
                w, h = bbox[2]-bbox[0], bbox[3]-bbox[1]
                if align == 'center':
                    x = (self.width - w) // 2
                elif align == 'right':
                    x = self.width - w - 10
                else:
                    x = 10
                draw.text((x, y), line, font=font, fill=color)
                y += h
            self.refresh()

    def display_image(self, img):
        with self.lock:
            if self.image is not None:
                if img.size != (self.width, self.height):
                    img = img.resize((self.width, self.height), Image.LANCZOS)
                self.image.paste(img)
            self.refresh()

    def render_text_to_image(self, text, color=(255,255,255), size=48, align='center', font_name=None, bg=(0,0,0)):
        font = self._get_font(font_name, size)
        img = Image.new("RGB", (self.width, self.height), bg)
        draw = ImageDraw.Draw(img)
        lines = text.split('\n')
        total_height = sum([draw.textbbox((0,0), line, font=font)[3] for line in lines])
        y = (self.height - total_height) // 2
        for line in lines:
            bbox = draw.textbbox((0,0), line, font=font)
            w, h = bbox[2]-bbox[0], bbox[3]-bbox[1]
            if align == 'center':
                x = (self.width - w) // 2
            elif align == 'right':
                x = self.width - w - 10
            else:
                x = 10
            draw.text((x, y), line, font=font, fill=color)
            y += h
        return img

    def _get_font(self, font_name, size):
        """
        Returns a PIL ImageFont object. If font_name is provided, checks for file existence first.
        Falls back to a system TTF font at the requested size, or default font if not found or on error.
        """
        if font_name:
            if not os.path.isfile(font_name):
                print(f"[PillowScreen] WARNING: Font file '{font_name}' not found. Using fallback font.")
            else:
                try:
                    return ImageFont.truetype(font_name, size)
                except Exception as e:
                    print(f"[PillowScreen] WARNING: Could not load font '{font_name}': {e}. Using fallback font.")
        # Try common system fonts for size support
        for sys_font in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]:
            if os.path.isfile(sys_font):
                try:
                    return ImageFont.truetype(sys_font, size)
                except Exception as e:
                    print(f"[PillowScreen] WARNING: Could not load system font '{sys_font}': {e}.")
        print(f"[PillowScreen] WARNING: No TTF font found. Using default font (fixed size, ignores requested size={size}).")
        # Only return default font if ImageFont and load_default are available
        if ImageFont is not None and hasattr(ImageFont, 'load_default'):
            return ImageFont.load_default()
        else:
            print("[PillowScreen] ERROR: ImageFont or load_default not available. Returning None.")
            return None

    def _update_fb(self):
        """
        Write the current image buffer to the framebuffer (if not in mock mode and all dependencies present).
        Only supports 16bpp (RGB565) output. Safe on non-Pi/dev platforms (no-op if mock or missing deps).
        """
        if self.mock or self.fb_mmap is None or np is None or self.image is None:
            # No-op in mock mode or if not all dependencies present
            return
        # Convert PIL image to numpy array
        arr = np.asarray(self.image, dtype=np.uint8)
        if self.bpp == 2:
            # Convert to RGB565
            r = arr[:, :, 0].astype(np.uint16)
            g = arr[:, :, 1].astype(np.uint16)
            b = arr[:, :, 2].astype(np.uint16)
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            # Prepare buffer for framebuffer (stride may be larger than width*2)
            buf = np.zeros((self.height, self.stride), dtype=np.uint8)
            packed = rgb565.flatten().view(np.uint8).reshape(self.height, self.width * 2)
            buf[:, :self.width * 2] = packed
            self.fb_mmap.seek(0)
            self.fb_mmap.write(buf.tobytes())
        # else: silently ignore unsupported bpp

    def save_to_file(self, path):
        with self.lock:
            if self.image is not None:
                self.image.save(path)
            else:
                print("[PillowScreen] WARNING: Cannot save image, self.image is None.")

    def close(self):
        if not self.mock:
            if self.fb_mmap is not None:
                self.fb_mmap.close()
            if self.fb is not None:
                self.fb.close()

    def print_line(self, text, color=(255,255,255), size=None, font_name=None, x=None, spacing=10, align='left'):
        """
        Print text at the current cursor_y, optionally at x (default center), then advance cursor_y.
        align: 'left', 'center', or 'right'.
        """
        if size is None:
            size = self.FONT_SIZE_DEFAULT
        with self.lock:
            font = self._get_font(font_name, size)
            if self.image is not None and font is not None and ImageDraw is not None and hasattr(ImageDraw, 'Draw'):
                draw = ImageDraw.Draw(self.image)
                w, h = draw.textbbox((0,0), text, font=font)[2:4]
                if x is not None:
                    xpos = x
                elif align == 'center':
                    xpos = (self.width - w) // 2
                elif align == 'right':
                    xpos = self.width - w - 10
                else:
                    xpos = 10
                draw.text((xpos, self.cursor_y), text, font=font, fill=color)
                self.cursor_y += h + spacing
                self.refresh()
            else:
                print("[PillowScreen] WARNING: Cannot print_line, image/font/ImageDraw/Draw is None or missing.")

    def draw_text(self, x, y, text, color=(255,255,255), size=None, font_name=None):
        """
        Draw text at a specific (x, y) position.
        """
        if size is None:
            size = self.FONT_SIZE_DEFAULT
        with self.lock:
            font = self._get_font(font_name, size)
            if self.image is not None and font is not None and ImageDraw is not None and hasattr(ImageDraw, 'Draw'):
                draw = ImageDraw.Draw(self.image)
                draw.text((x, y), text, font=font, fill=color)
            else:
                print("[PillowScreen] WARNING: Cannot draw_text, image/font/ImageDraw/Draw is None or missing.")

    def set_cursor(self, y=0):
        """
        Set the y position for the next print_line.
        """
        with self.lock:
            self.cursor_y = y

    def reset_cursor(self):
        """
        Reset the cursor to the top of the screen.
        """
        with self.lock:
            self.cursor_y = 0

    def refresh(self):
        """
        Public method to update the framebuffer after drawing operations.
        """
        self._update_fb()
