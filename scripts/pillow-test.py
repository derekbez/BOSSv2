from PIL import Image, ImageDraw, ImageFont
import mmap
import os

# Framebuffer details
fb_path = "/dev/fb0"
width, height = 1024, 600
stride = 2048  # bytes per line
bpp = 2        # bytes per pixel (16-bit)

# Create a black image
img = Image.new("RGB", (width, height), (0, 0, 0))
draw = ImageDraw.Draw(img)

# Add some text
font = ImageFont.load_default()
draw.text((50, 50), "Hello from Pillow!", font=font, fill=(255, 255, 255))

# Convert to RGB565
def rgb_to_565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

buf = bytearray()
for y in range(height):
    for x in range(width):
        r, g, b = img.getpixel((x, y))
        color = rgb_to_565(r, g, b)
        buf += color.to_bytes(2, byteorder="little")

# Write to framebuffer
with open(fb_path, "rb+") as f:
    mm = mmap.mmap(f.fileno(), stride * height, mmap.MAP_SHARED, mmap.PROT_WRITE)
    mm.write(buf)
    mm.close()
