"""
Optimized PillowScreen for B.O.S.S. (HDMI framebuffer, Pi 3+)
- Fast numpy framebuffer conversion
- TTF font support
- Mock mode for dev/testing
- Thread-safe
- Display text or images
"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import fcntl
import struct
import mmap
import threading

class PillowScreen:
    FONT_SIZE_LARGEST = 200
    FONT_SIZE_LARGER = 160
    FONT_SIZE_DEFAULT = 128
    FONT_SIZE_SMALLER = 96
    FONT_SIZE_SMALLEST = 48  # Default font size

    def __init__(self, width=1024, height=600, stride=2048, bpp=2, fbdev="/dev/fb0", mock=False):
        self.width = width
        self.height = height
        self.stride = stride
        self.bpp = bpp
        self.fbdev = fbdev
        self.mock = mock
        self.lock = threading.RLock()  # Use re-entrant lock to avoid deadlocks
        self.image = Image.new("RGB", (self.width, self.height), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        self.font = ImageFont.load_default()
        self.fb = None
        self.fb_mmap = None
        self.cursor_y = 0  # Track current y position for print_line
        if not self.mock:
            self._open_fb()
        else:
            print("[PillowScreen] MOCK MODE: No framebuffer access.")

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
            self.image.paste(color, [0, 0, self.width, self.height])
            self.cursor_y = 0  # Reset cursor on clear
            self._update_fb()

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
            self._update_fb()

    def display_image(self, img):
        with self.lock:
            if img.size != (self.width, self.height):
                img = img.resize((self.width, self.height), Image.LANCZOS)
            self.image.paste(img)
            self._update_fb()

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
        Falls back to default font if not found or on error.
        """
        if font_name:
            if not os.path.isfile(font_name):
                print(f"[PillowScreen] WARNING: Font file '{font_name}' not found. Using default font.")
                return ImageFont.load_default()
            try:
                return ImageFont.truetype(font_name, size)
            except Exception as e:
                print(f"[PillowScreen] WARNING: Could not load font '{font_name}': {e}. Using default font.")
                return ImageFont.load_default()
        return ImageFont.load_default()

    def _update_fb(self):
        print("[PillowScreen] _update_fb(): Entry.")
        if self.mock:
            print("[PillowScreen] _update_fb(): Mock mode, skipping.")
            return
        arr = np.asarray(self.image, dtype=np.uint8)
        print("[PillowScreen] _update_fb(): Converted image to numpy array.")
        if self.bpp == 2:
            print("[PillowScreen] _update_fb(): Converting to RGB565...")
            r = arr[:,:,0].astype(np.uint16)
            g = arr[:,:,1].astype(np.uint16)
            b = arr[:,:,2].astype(np.uint16)
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            buf = np.zeros((self.height, self.stride), dtype=np.uint8)
            packed = rgb565.flatten().view(np.uint8).reshape(self.height, self.width*2)
            buf[:,:self.width*2] = packed
            print("[PillowScreen] _update_fb(): Writing to framebuffer mmap...")
            self.fb_mmap.seek(0)
            self.fb_mmap.write(buf.tobytes())
            print("[PillowScreen] _update_fb(): Write complete.")
        else:
            print("[PillowScreen] Only 16bpp (RGB565) supported in optimized path.")
        print("[PillowScreen] _update_fb(): Exit.")

    def save_to_file(self, path):
        with self.lock:
            self.image.save(path)

    def close(self):
        if not self.mock:
            self.fb_mmap.close()
            self.fb.close()

    def print_line(self, text, color=(255,255,255), size=None, font_name=None, x=None, spacing=10):
        """
        Print text at the current cursor_y, optionally at x (default center), then advance cursor_y.
        """
        if size is None:
            size = self.FONT_SIZE_DEFAULT
        with self.lock:
            font = self._get_font(font_name, size)
            draw = ImageDraw.Draw(self.image)
            w, h = draw.textbbox((0,0), text, font=font)[2:4]
            if x is None:
                x = (self.width - w) // 2
            draw.text((x, self.cursor_y), text, font=font, fill=color)
            self.cursor_y += h + spacing

    def draw_text(self, x, y, text, color=(255,255,255), size=None, font_name=None):
        """
        Draw text at a specific (x, y) position.
        """
        if size is None:
            size = self.FONT_SIZE_DEFAULT
        with self.lock:
            font = self._get_font(font_name, size)
            draw = ImageDraw.Draw(self.image)
            draw.text((x, y), text, font=font, fill=color)

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
