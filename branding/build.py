#!/usr/bin/env python3
"""Regenerate the To Do logos, illustrations and icons from the Luna artwork.

Sources (kept verbatim): branding/luna-portrait.svg, branding/luna-full-body.svg.
They are traced vectors (0.7-0.9 MB each), so the app ships derived images:

- frontend/src/assets/logo.svg, logo-full.svg, logo-full-pride.svg: vector
  circle (blue or rainbow) + Luna as an embedded 320px WebP, already clipped
  to the circle. The "To Do" wordmark in logo-full*.svg stays vector so it
  follows light/dark mode (currentColor).
- frontend/src/assets/luna-portrait.webp (login page, 194px wide in CSS) and
  luna-full-body.webp (empty task list, 265x313 in CSS), both 2x.
- frontend/public/favicon.ico and frontend/public/images/icons/*.png.

Needs: pip install resvg-py pillow. Safe to re-run.
"""
import base64
import io
import pathlib
import re
import xml.etree.ElementTree as ET

import resvg_py
from PIL import Image, ImageChops, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT/'frontend/src/assets'
ICONS = ROOT/'frontend/public/images/icons'
PORTRAIT = (ROOT/'branding/luna-portrait.svg').read_text()
FULL_BODY = (ROOT/'branding/luna-full-body.svg').read_text()

BLUE = (25, 106, 255, 255)
TOP = 12            # head top in the 256-unit logo circle (the llama's ears were at 11.5)
ZOOM = 1.1          # past "fits top to bottom", so the face reads at favicon size
LOGO_PX = 320       # embedded logo raster: 3x the 100px loading-screen logo


def svg_size(svg):
    root = re.search(r'<svg\b[^>]*>', svg).group(0)
    m = re.search(r'viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', root)
    return float(m.group(1)), float(m.group(2))


def render(svg, scale):
    """Rasterize the whole SVG canvas at `scale` px per unit, transparent background."""
    w, h = svg_size(svg)
    root = re.search(r'<svg\b[^>]*>', svg).group(0)
    sized = re.sub(r'\s(width|height)="[^"]*"', '', root)[:-1] + f' width="{round(w*scale)}" height="{round(h*scale)}">'
    return Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=svg.replace(root, sized, 1))))).convert('RGBA')


def ink_box(svg):
    x0, y0, x1, y1 = render(svg, 1).getchannel('A').getbbox()
    return x0, y0, x1, y1


def trimmed(svg, px_high):
    """Render so the ink is px_high tall, cropped to the ink."""
    y0, y1 = ink_box(svg)[1::2]
    im = render(svg, px_high/(y1 - y0))
    return im.crop(im.getchannel('A').getbbox())


def disc(size, fill=(255, 255, 255, 255)):
    big = Image.new('RGBA', (size*4, size*4), (0, 0, 0, 0))
    ImageDraw.Draw(big).ellipse([0, 0, size*4 - 1, size*4 - 1], fill=fill)
    return big.resize((size, size), Image.LANCZOS)


PX0, PY0, PX1, PY1 = ink_box(PORTRAIT)
SCALE = ZOOM*(256 - TOP)/(PY1 - PY0)


def portrait_layer(size, unit=None, offset=(0, 0)):
    """Luna placed as in the 256-unit logo on a transparent size x size canvas.
    unit: pixels per logo unit (default size/256); offset: shift in pixels."""
    unit = unit or size/256
    layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    x = offset[0] + (128 - SCALE*(PX0 + PX1)/2)*unit
    y = offset[1] + (TOP - SCALE*PY0)*unit
    layer.paste(render(PORTRAIT, SCALE*unit), (round(x), round(y)))
    return layer


def clip_to_disc(layer):
    layer.putalpha(ImageChops.multiply(layer.getchannel('A'), disc(layer.width).getchannel('A')))
    return layer


def circle_logo(size):
    out = disc(size, BLUE)
    out.alpha_composite(clip_to_disc(portrait_layer(size)))
    return out


def small(make, size):
    """Small sizes: compose at 256 and downsample, for cleaner edges."""
    return make(size) if size >= 256 else make(256).resize((size, size), Image.LANCZOS)


def square_icon(size):
    """Full-bleed blue square, Luna not clipped (her chest runs off the bottom edge)."""
    out = Image.new('RGBA', (size, size), BLUE)
    out.alpha_composite(portrait_layer(size))
    return out.convert('RGB')


def webp_bytes(im):
    b = io.BytesIO()
    im.save(b, 'WEBP', quality=90, method=6)
    return b.getvalue()


def build_logos():
    uri = 'data:image/webp;base64,' + base64.b64encode(webp_bytes(clip_to_disc(portrait_layer(LOGO_PX)))).decode()
    luna = f'<image width="256" height="256" href="{uri}"/>'
    circle = '<circle cx="128" cy="128" r="128" fill="#196aff"/>'
    desc = '<desc>To Do logo: Luna the sheepadoodle in a {} circle on the left, with the text "To Do" on the right.</desc>'

    logos = {'logo.svg': ('<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="0 0 256 256" width="256" height="256">'
                          f'<title>To Do</title>{circle}{luna}</svg>\n')}

    # logo-full*: keep the root tag, title and the vector "To Do" wordmark group
    full = (ASSETS/'logo-full.svg').read_text()
    head, wordmark = full[:full.index('</desc>') + 7], full[full.index('<g fill="currentColor">'):]
    logos['logo-full.svg'] = re.sub(r'<desc>.*?</desc>', desc.format('blue'), head) + circle + luna + wordmark

    pride = (ASSETS/'logo-full-pride.svg').read_text()
    head, wordmark = pride[:pride.index('</desc>') + 7], pride[pride.index('<g fill="currentColor">'):]
    stripes = [m.group(0) for m in re.finditer(r'<path\b[^>]*/>', pride[len(head):pride.index('<g fill="currentColor">')])
               if re.search(r'e40303|ff8c00|ffed00|008026|004dff|750787', m.group(0))]
    assert len(stripes) == 6, f'expected 6 rainbow stripes, found {len(stripes)}'
    k = 124.5/128   # rainbow disc: centre (134.65, 124.9), r 124.5
    logos['logo-full-pride.svg'] = (re.sub(r'<desc>.*?</desc>', desc.format('rainbow'), head) + ''.join(stripes)
                                    + f'<g transform="translate({134.65 - 128*k:.2f} {124.9 - 128*k:.2f}) scale({k:.5f})">{luna}</g>'
                                    + wordmark)
    for name, svg in logos.items():
        ET.fromstring(svg)
        (ASSETS/name).write_text(svg)
        print(f'{name}: {len(svg)/1024:.0f} KB')


def build_illustrations():
    portrait = trimmed(PORTRAIT, 411)
    portrait.save(ASSETS/'luna-portrait.webp', quality=90, method=6)
    body = trimmed(FULL_BODY, 626).resize((530, 626), Image.LANCZOS)
    body.save(ASSETS/'luna-full-body.webp', quality=90, method=6)
    print(f'luna-portrait.webp {portrait.size}, luna-full-body.webp {body.size}')


def build_icons():
    def save(im, name):
        im.save(ICONS/name, optimize=True)
    for size, name in ((192, 'android-chrome-192x192.png'), (512, 'android-chrome-512x512.png'),
                       (144, 'msapplication-icon-144x144.png'), (32, 'favicon-32x32.png'), (16, 'favicon-16x16.png')):
        save(small(circle_logo, size), name)
    tile = Image.new('RGBA', (270, 270), (0, 0, 0, 0))
    tile.alpha_composite(circle_logo(150), (60, 60))
    save(tile, 'mstile-150x150.png')
    for size, name in ((60, 'apple-touch-icon-60x60.png'), (76, 'apple-touch-icon-76x76.png'),
                       (120, 'apple-touch-icon-120x120.png'), (152, 'apple-touch-icon-152x152.png'),
                       (180, 'apple-touch-icon-180x180.png'), (180, 'apple-touch-icon.png')):
        save(square_icon(size), name)
    f = 3.56    # maskable: composition at ~89%, centred, bottom-aligned (as the llama was)
    mask = Image.new('RGBA', (1024, 1024), BLUE)
    mask.alpha_composite(portrait_layer(1024, unit=f, offset=((1024 - 256*f)/2, 1024 - 256*f)))
    save(mask.convert('RGB'), 'icon-maskable.png')
    shape = trimmed(PORTRAIT, 123)
    silhouette = Image.new('RGBA', shape.size, (255, 255, 255, 0))
    silhouette.putalpha(shape.getchannel('A'))
    badge = Image.new('RGBA', (128, 128), (255, 255, 255, 0))
    badge.alpha_composite(silhouette, ((128 - shape.width)//2, 5))
    save(badge, 'badge-monochrome.png')
    tracking = circle_logo(256)   # red "timer running" dot, lower left
    ImageDraw.Draw(tracking).ellipse([1*8, 24*8, 8*8, 31*8], fill=(255, 65, 54, 255))
    save(tracking.resize((32, 32), Image.LANCZOS), 'favicon-tracking-32x32.png')
    circle_logo(256).save(ROOT/'frontend/public/favicon.ico', sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    print('icons: favicon.ico + 15 PNGs')


if __name__ == '__main__':
    build_logos()
    build_illustrations()
    build_icons()
