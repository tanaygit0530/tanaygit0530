"""One-off: turn a photo into ASCII art (assets/portrait.txt).
Usage: python3 scripts/make_portrait.py photo.png > assets/portrait.txt
The silhouette mask coordinates are tuned for a 460x460 head-and-shoulders photo."""
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageChops

src = Image.open(sys.argv[1]).convert("L").resize((460, 460))

def shape(draw_fn, blur=3):
    m = Image.new("L", src.size, 0)
    draw_fn(ImageDraw.Draw(m))
    return m.filter(ImageFilter.GaussianBlur(blur))

head = shape(lambda d: (d.ellipse((172, 100, 278, 252), fill=255),
                        d.polygon([(198, 225), (252, 225), (262, 262), (190, 262)], fill=255)))
body = shape(lambda d: d.polygon([(190, 248), (262, 248), (345, 285), (362, 380), (365, 460),
                                  (105, 460), (110, 360), (125, 285)], fill=255))
mask = ImageChops.lighter(head, body)

# sketch style: dark pixels -> dense glyphs. Face gets strong local contrast;
# the body is lifted toward light so the shirt stays sparse and the face carries the image
face = ImageOps.equalize(src, mask=head.point(lambda v: 255 if v > 128 else 0))
torso = ImageOps.autocontrast(src, cutoff=3).point(lambda v: min(255, int(v * 0.7 + 90)))
img = Image.composite(face, torso, head)

crop = (100, 92, 350, 372)
img, m = img.crop(crop), mask.crop(crop)
cols = 72
rows = int(cols * img.height / img.width * 0.55)
img, m = img.resize((cols, rows)), m.resize((cols, rows))
ramp = " .,:;-=+*coxO0#%@"
for y in range(rows):
    row = ""
    for x in range(cols):
        if m.getpixel((x, y)) < 110:
            row += " "
            continue
        v = (255 - img.getpixel((x, y))) / 256
        row += ramp[int(v * len(ramp))]
    print(row.rstrip())
