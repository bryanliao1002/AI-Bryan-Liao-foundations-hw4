"""Storefront-ready product images.

About 70% of the catalogue photos have a pure-black background (flattened transparency) and
the rest are on white, which looks patchy on a light storefront. This module makes a
"display" copy of each photo with the background replaced by one warm neutral (TILE_BG),
so every product sits on the same tile color as the page.

- Originals in data/products are never modified; image_url still points at them.
- The background is found by flood-filling from the image edges, only through near-pure
  black (or near-pure white) pixels, so dark navy garments are not touched. The mask is
  softened by a pixel or two so there is no hard outline.
- Results are cached on disk in backend/.cache/products (git-ignored) and pre-built in a
  background thread at startup.
"""

import io
import logging
import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from db import PRODUCTS_DIR

TILE_BG = (246, 244, 240)  # matches --tile in frontend/src/index.css
MARKER = (255, 0, 255)  # temporary fill color, never present in the photos
DARK_THRESH = 10  # background black must be within 10/255 of pure black
LIGHT_THRESH = 14
HALO_THRESH = 38  # luminance at or below this counts as "near black" for halo cleanup
HALO_PASSES = 3
CACHE_DIR = Path(__file__).resolve().parent / ".cache" / "products"

logger = logging.getLogger("campus_customs.images")
router = APIRouter()


def clean_image(src: Path) -> bytes:
    im = Image.open(src).convert("RGB")
    w, h = im.size
    work = im.copy()
    step = max(1, min(w, h) // 80)
    edges = (
        [(x, 0) for x in range(0, w, step)] + [(x, h - 1) for x in range(0, w, step)]
        + [(0, y) for y in range(0, h, step)] + [(w - 1, y) for y in range(0, h, step)]
    )
    for seed in edges:
        p = work.getpixel(seed)
        if p == MARKER:
            continue
        if max(p) <= DARK_THRESH:
            ImageDraw.floodfill(work, seed, MARKER, thresh=DARK_THRESH)
        elif min(p) >= 255 - LIGHT_THRESH:
            ImageDraw.floodfill(work, seed, MARKER, thresh=LIGHT_THRESH)

    diff = ImageChops.difference(work, Image.new("RGB", work.size, MARKER)).convert("L")
    mask = diff.point(lambda v: 255 if v < 3 else 0)
    # JPEG edges leave a 1–3px ring of almost-black pixels around the garment. Grow the mask
    # a few pixels, but only into near-black pixels, so the halo goes and the fabric stays.
    near_black = im.convert("L").point(lambda v: 255 if v <= HALO_THRESH else 0)
    for _ in range(HALO_PASSES):
        mask = ImageChops.lighter(mask, ImageChops.multiply(mask.filter(ImageFilter.MaxFilter(3)), near_black))
    mask = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    out = Image.composite(Image.new("RGB", im.size, TILE_BG), im, mask)
    buf = io.BytesIO()
    out.save(buf, "JPEG", quality=88, optimize=True)
    return buf.getvalue()


def display_path(filename: str) -> Path | None:
    """Cached display image for data/products/<filename>, building it if needed."""
    src = PRODUCTS_DIR / filename
    # Only plain file names of real product images (no paths, so no directory traversal).
    if Path(filename).name != filename or not src.is_file():
        return None
    dest = CACHE_DIR / filename
    if not dest.exists() or dest.stat().st_mtime < src.stat().st_mtime:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".tmp")
        tmp.write_bytes(clean_image(src))
        tmp.replace(dest)
    return dest


@router.get("/media/display/products/{filename}")
def display_image(filename: str) -> FileResponse:
    path = display_path(filename)
    if path is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=86400"})


def prewarm() -> None:
    """Build every display image in the background so the first page view is fast."""

    def run() -> None:
        for src in sorted(PRODUCTS_DIR.glob("*.jpg")):
            try:
                display_path(src.name)
            except Exception:
                logger.exception("Could not build display image for %s", src.name)

    threading.Thread(target=run, daemon=True).start()
