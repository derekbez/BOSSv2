"""
PillowScreen implementation for B.O.S.S.
Renders text/images using Pillow and writes directly to the framebuffer (/dev/fb0) for HDMI display on headless Raspberry Pi OS.
"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import fcntl
import struct
import mmap

class PillowScreen:
    def __init__(self, width=1024, height=600, stride=2048, bpp=2, fbdev="/dev/fb0"):
        self.width = width
        self.height = height
        self.stride = stride
        self.bpp = bpp
        self.fbdev = fbdev
        self.image = Image.new("RGB", (self.width, self.height), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        self.font = ImageFont.load_default()
        self._open_fb()

    def _open_fb(self):
        self.fb = open(self.fbdev, "rb+")
        # Try ioctl auto-detect, fallback to manual if fails or zero
        try:
            FBIOGET_VSCREENINFO = 0x4600
            FBIOGET_FSCREENINFO = 0x4602
            vinfo = fcntl.ioctl(self.fb, FBIOGET_VSCREENINFO, b'\x00' * 160)
            finfo = fcntl.ioctl(self.fb, FBIOGET_FSCREENINFO, b'\x00' * 64)
            xres = struct.unpack_from('I', vinfo, 0)[0]
            yres = struct.unpack_from('I', vinfo, 4)[0]
            bits_per_pixel = struct.unpack_from('I', vinfo, 24)[0]
            line_length = struct.unpack_from('I', finfo, 8)[0]
            visual = struct.unpack_from('I', finfo, 20)[0]
        except Exception:
            xres = yres = bits_per_pixel = line_length = visual = 0
        # Use detected values if valid, else fallback to manual
        if xres > 0 and yres > 0 and line_length > 0 and bits_per_pixel > 0:
            self.width = xres
            self.height = yres
            self.stride = line_length
            self.bpp = bits_per_pixel // 8
            print("[PillowScreen] Using detected framebuffer parameters.")
        else:
            print("[PillowScreen] WARNING: Auto-detect failed, using manual framebuffer parameters.")
        print("[PillowScreen] Framebuffer info:")
        print("  width:", self.width)
        print("  height:", self.height)
        print("  stride:", self.stride)
        print("  bpp:", self.bpp)
        # Use stride*height for mmap size
        self.fb_size = self.stride * self.height
        self.fb_mmap = mmap.mmap(self.fb.fileno(), self.fb_size)

    def clear(self):
        self.image.paste((0, 0, 0), [0, 0, self.width, self.height])
        self._update_fb()

    def display_text(self, text, **kwargs):
        self.clear()
        color = kwargs.get('color', (255, 255, 255))
        size = kwargs.get('size', 48)
        align = kwargs.get('align', 'center')
        font_name = kwargs.get('font_name', None)
        if font_name:
            try:
                font = ImageFont.truetype(font_name, size)
            except Exception:
                font = ImageFont.load_default()
        else:
            font = ImageFont.load_default()
        try:
            bbox = self.draw.textbbox((0, 0), text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            w, h = font.getsize(text)
        if align == 'center':
            x = (self.width - w) // 2
        elif align == 'right':
            x = self.width - w - 10
        else:
            x = 10
        y = (self.height - h) // 2
        self.draw.text((x, y), text, font=font, fill=color)
        self._update_fb()

    def show_status(self, message):
        self.display_text(f"STATUS: {message}", color=(0,255,0))

    def show_app_output(self, content):
        self.display_text(content, color=(255,255,255))

    def _update_fb(self):
        arr = np.array(self.image, dtype=np.uint8)
        if self.bpp == 2:
            # Convert RGB888 to RGB565, build full buffer with stride
            def rgb_to_565(r, g, b):
                return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            buf = bytearray()
            for y in range(self.height):
                line = bytearray()
                for x in range(self.width):
                    r, g, b = arr[y, x]
                    color = int(rgb_to_565(r, g, b))
                    line += color.to_bytes(2, byteorder="little")
                # Pad line to stride
                if len(line) < self.stride:
                    line += b'\x00' * (self.stride - len(line))
                buf += line
            if len(buf) != self.stride * self.height:
                print(f"[PillowScreen] WARNING: Framebuffer buffer size mismatch: {len(buf)} vs {self.stride * self.height}")
            self.fb_mmap.seek(0)
            self.fb_mmap.write(buf)
        elif self.bpp == 3 or self.bpp == 4:
            # RGB to BGR, build full buffer with stride
            bgr = arr[..., ::-1]
            buf = bytearray()
            for y in range(self.height):
                line = bgr[y, :self.width].tobytes()
                if len(line) < self.stride:
                    line += b'\x00' * (self.stride - len(line))
                buf += line
            self.fb_mmap.seek(0)
            self.fb_mmap.write(buf)
        else:
            print("[PillowScreen] Unknown bpp, not writing to framebuffer.")

    def close(self):
        self.fb_mmap.close()
        self.fb.close()
