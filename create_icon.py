"""
Create a simple application icon for the Cover Letter Generator
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Create a simple image
img_size = 256
img = Image.new('RGBA', (img_size, img_size), color=(0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw a simple document icon
# Background
draw.rectangle([(40, 20), (img_size-40, img_size-20)],
               fill=(41, 150, 243))  # Blue background
# Folded corner
draw.polygon([(img_size-40, 20), (img_size-40, 70), (img_size-90, 20)],
             fill=(25, 118, 210))  # Dark blue folded corner
# Lines representing text
for i in range(7):
    y_pos = 60 + i * 25
    line_length = img_size - 100 - \
        (30 if i % 2 == 0 else 0)  # Alternate line lengths
    draw.rectangle([(60, y_pos), (60 + line_length, y_pos + 10)],
                   fill=(255, 255, 255, 220))  # White lines

# Save as PNG first
icon_png_path = os.path.join("files", "storage", "icon.png")
img.save(icon_png_path)

# Convert to ICO
icon_path = os.path.join("files", "storage", "icon.ico")
img.save(icon_path, format='ICO', sizes=[
         (256, 256), (128, 128), (64, 64), (32, 32)])

print(f"Icon created at {icon_path}")
