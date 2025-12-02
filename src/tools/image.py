import base64
import io
from typing import Literal
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat, ImageChops
from langchain_core.tools import tool
import os
import re
import uuid

def _decode_image(b64: str) -> Image.Image:
    return Image.open(io.BytesIO(base64.b64decode(b64)))

def _encode_image(img: Image.Image, fmt: str = "PNG", quality: int = 80) -> str:
    buf = io.BytesIO()
    if fmt.upper() == "WEBP":
        img = img.convert("RGB")
        img.save(buf, format=fmt, quality=quality, method=6)
    elif fmt.upper() == "JPEG":
        img = img.convert("RGB")
        img.save(buf, format=fmt, quality=quality, optimize=True)
    else:
        img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode('utf-8')
def _choose_font(font_path: str, font_size: int):
    if font_path and os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, font_size)
        except Exception:
            pass
    cands = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyh.ttf",
        "C:/Windows/Fonts/msyhbd.ttf",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/msjh.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/arphic/ukai.ttc",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
        "arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans.ttf",
    ]
    for fp in cands:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, font_size)
            except Exception:
                pass
    return ImageFont.load_default()

ARTIFACT_CACHE = {}

def _put_artifact(data: str) -> str:
    k = uuid.uuid4().hex
    ARTIFACT_CACHE[k] = data
    return k

def get_artifact(key: str) -> str:
    return ARTIFACT_CACHE.get(key, "")

@tool
def image_resize_base64(image_base64: str, width: int, height: int) -> str:
    """Resize a base64-encoded image and return base64 (PNG)."""
    try:
        img = _decode_image(image_base64)
        resized = img.resize((width, height))
        b64 = _encode_image(resized, "PNG")
        aid = _put_artifact(b64)
        return f"Image resized. [IMAGE_ID:{aid}:png]"
    except Exception as e:
        return f"Error resizing image: {str(e)}"

@tool
def image_convert_base64(image_base64: str, format: Literal["PNG", "JPEG", "WEBP"] = "PNG") -> str:
    """Convert a base64-encoded image to a different format and return base64."""
    try:
        img = _decode_image(image_base64)
        b64 = _encode_image(img, format)
        lower = format.lower()
        mime = "png" if lower == "png" else ("jpeg" if lower == "jpeg" else "webp")
        aid = _put_artifact(b64)
        return f"Image converted. [IMAGE_ID:{aid}:{mime}]"
    except Exception as e:
        return f"Error converting image: {str(e)}"

@tool
def image_crop_base64(image_base64: str, x: int, y: int, width: int, height: int) -> str:
    """Crop a base64-encoded image to a rectangle and return base64 (PNG)."""
    try:
        img = _decode_image(image_base64)
        box = (x, y, x + width, y + height)
        cropped = img.crop(box)
        b64 = _encode_image(cropped, "PNG")
        aid = _put_artifact(b64)
        return f"Image cropped. [IMAGE_ID:{aid}:png]"
    except Exception as e:
        return f"Error cropping image: {str(e)}"

@tool
def image_compress_base64(image_base64: str, quality: int = 75, format: Literal["JPEG", "WEBP"] = "JPEG") -> str:
    """Compress image by re-encoding with given quality; return base64."""
    try:
        img = _decode_image(image_base64).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format=format, quality=quality, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        mime = "jpeg" if format == "JPEG" else "webp"
        aid = _put_artifact(b64)
        return f"Image compressed. [IMAGE_ID:{aid}:{mime}]"
    except Exception as e:
        return f"Error compressing image: {str(e)}"

@tool
def image_rotate_base64(image_base64: str, angle: float, expand: bool = True) -> str:
    """Rotate image by angle degrees; return base64 (PNG)."""
    try:
        img = _decode_image(image_base64)
        rotated = img.rotate(angle, expand=expand)
        b64 = _encode_image(rotated, "PNG")
        aid = _put_artifact(b64)
        return f"Image rotated. [IMAGE_ID:{aid}:png]"
    except Exception as e:
        return f"Error rotating image: {str(e)}"

@tool
def image_add_text_watermark_base64(image_base64: str, text: str, x: int = 10, y: int = 10, opacity: float = 0.3, font_size: int = 24) -> str:
    """Add semi-transparent text watermark; return base64 (PNG)."""
    try:
        img = _decode_image(image_base64).convert("RGBA")
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        font = _choose_font("", font_size)
        # If default font is too small, try scaling via stroke
        draw.text((x, y), text, font=font, fill=(255, 255, 255, int(255 * opacity)))
        out = Image.alpha_composite(img, txt_layer)
        b64 = _encode_image(out.convert("RGB"), "PNG")
        aid = _put_artifact(b64)
        return f"Text watermark added. [IMAGE_ID:{aid}:png]"
    except Exception as e:
        return f"Error adding text watermark: {str(e)}"

@tool
def image_add_image_watermark_base64(image_base64: str, watermark_base64: str, x: int = 10, y: int = 10, opacity: float = 0.3, scale: float = 1.0) -> str:
    """Overlay an image watermark with opacity and scale; return base64 (PNG)."""
    try:
        base = _decode_image(image_base64).convert("RGBA")
        wm = _decode_image(watermark_base64).convert("RGBA")
        if scale != 1.0:
            w = int(wm.width * scale)
            h = int(wm.height * scale)
            wm = wm.resize((w, h))
        alpha = wm.split()[3]
        alpha = alpha.point(lambda p: int(p * opacity))
        wm.putalpha(alpha)
        base.paste(wm, (x, y), wm)
        b64 = _encode_image(base.convert("RGB"), "PNG")
        aid = _put_artifact(b64)
        return f"Image watermark added. [IMAGE_ID:{aid}:png]"
    except Exception as e:
        return f"Error adding image watermark: {str(e)}"

@tool
def image_remove_watermark_base64(
    image_base64: str,
    x: int,
    y: int,
    width: int,
    height: int,
    method: Literal["blur", "pixelate", "median", "clone_left", "clone_top"] = "blur",
    strength: int = 6,
    feather: int = 0,
) -> str:
    """Remove watermark in a selected rectangle using different methods; return base64 (PNG).
    - method: blur | pixelate | median | clone_left | clone_top
    - strength: blur radius / pixelation level / median size
    - feather: blend the edited region edges with GaussianBlur(feather)
    """
    try:
        img = _decode_image(image_base64).convert("RGBA")
        box = (x, y, x + width, y + height)
        region = img.crop(box)
        strength = max(1, strength)
        if method == "blur":
            region = region.filter(ImageFilter.GaussianBlur(radius=strength))
        elif method == "pixelate":
            small = region.resize((max(1, width // max(1, strength)), max(1, height // max(1, strength))), resample=Image.NEAREST)
            region = small.resize((width, height), resample=Image.NEAREST)
        elif method == "median":
            size = strength if strength % 2 == 1 else strength + 1
            region = region.filter(ImageFilter.MedianFilter(size=size))
        elif method in ("clone_left", "clone_top"):
            src_img = img.copy()
            if method == "clone_left":
                sx = max(0, x - width)
                sy = y
                src_box = (sx, sy, sx + width, sy + height)
            else:
                sx = x
                sy = max(0, y - height)
                src_box = (sx, sy, sx + width, sy + height)
            # Clamp source box within bounds
            sx1, sy1, sx2, sy2 = src_box
            sx1 = max(0, min(sx1, src_img.width))
            sy1 = max(0, min(sy1, src_img.height))
            sx2 = max(0, min(sx2, src_img.width))
            sy2 = max(0, min(sy2, src_img.height))
            src_box = (sx1, sy1, sx2, sy2)
            sample = src_img.crop(src_box)
            # If sample size mismatch, resize
            if sample.size != (width, height):
                sample = sample.resize((width, height))
            region = sample
        # Compose with optional feather for smoother edges
        out_img = img.copy()
        out_img.paste(region, (x, y))
        if feather > 0:
            mask = Image.new("L", img.size, 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.rectangle([x, y, x + width, y + height], fill=255)
            mask = mask.filter(ImageFilter.GaussianBlur(radius=feather))
            out_img = Image.composite(out_img, img, mask)
        b64 = _encode_image(out_img.convert("RGB"), "PNG")
        aid = _put_artifact(b64)
        return f"Watermark removed. [IMAGE_ID:{aid}:png]"
    except Exception as e:
        return f"Error removing watermark: {str(e)}"

@tool
def image_upload_to_base64(filename: str) -> str:
    """Read uploaded image from 'uploads/' and return as base64 (PNG)."""
    try:
        if not _allowed(filename):
            return "Error: File not allowed (not in current session uploads)"
        path = os.path.join("uploads", filename)
        with open(path, "rb") as f:
            data = f.read()
        # Detect format roughly via Pillow
        img = Image.open(io.BytesIO(data))
        fmt = img.format or "PNG"
        # Normalize to given format when encoding
        b64 = base64.b64encode(data).decode("utf-8")
        mime = fmt.lower()
        aid = _put_artifact(b64)
        return f"Image loaded. [IMAGE_ID:{aid}:{mime}]"
    except Exception as e:
        return f"Error reading uploaded image: {str(e)}"
    finally:
        try:
            os.remove(path)
        except Exception:
            pass

@tool
def image_crop_upload(filename: str, x: int, y: int, width: int, height: int) -> str:
    """Crop an uploaded image to a rectangle and return base64 (WEBP)."""
    try:
        if not _allowed(filename):
            return "Error: File not allowed (not in current session uploads)"
        path = os.path.join("uploads", filename)
        img = Image.open(path)
        box = (x, y, x + width, y + height)
        cropped = img.crop(box)
        b64 = _encode_image(cropped, "WEBP", quality=80)
        aid = _put_artifact(b64)
        return f"Image cropped. [IMAGE_ID:{aid}:webp]"
    except Exception as e:
        return f"Error cropping image: {str(e)}"
    finally:
        try:
            os.remove(path)
        except Exception:
            pass

@tool
def image_compress_upload(filename: str, quality: int = 75, format: Literal["JPEG", "WEBP"] = "JPEG") -> str:
    """Compress an uploaded image by re-encoding with given quality; return base64."""
    try:
        if not _allowed(filename):
            return "Error: File not allowed (not in current session uploads)"
        path = os.path.join("uploads", filename)
        img = Image.open(path).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format=format, quality=quality, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        mime = "jpeg" if format == "JPEG" else "webp"
        aid = _put_artifact(b64)
        return f"Image compressed. [IMAGE_ID:{aid}:{mime}]"
    except Exception as e:
        return f"Error compressing image: {str(e)}"
    finally:
        try:
            os.remove(path)
        except Exception:
            pass

@tool
def image_rotate_upload(filename: str, angle: float, expand: bool = True) -> str:
    """Rotate an uploaded image by angle degrees; return base64 (WEBP)."""
    try:
        if not _allowed(filename):
            return "Error: File not allowed (not in current session uploads)"
        path = os.path.join("uploads", filename)
        img = Image.open(path)
        rotated = img.rotate(angle, expand=expand)
        b64 = _encode_image(rotated, "WEBP", quality=80)
        aid = _put_artifact(b64)
        return f"Image rotated. [IMAGE_ID:{aid}:webp]"
    except Exception as e:
        return f"Error rotating image: {str(e)}"
    finally:
        try:
            os.remove(path)
        except Exception:
            pass

@tool
def image_add_text_watermark_upload(
    filename: str,
    text: str,
    x: int = 10,
    y: int = 10,
    opacity: float = 0.3,
    font_size: int = 24,
    color: str = "#FFFFFF",
    stroke_color: str = "#000000",
    mode: Literal["single", "tile", "diagonal", "center"] = "single",
    spacing: int = 160,
    angle: float = 0.0,
    align: Literal["lt", "rt", "lb", "rb", "center"] = "lt",
    font_path: str = "",
) -> str:
    """Add configurable text watermark to an uploaded image; return base64 (WEBP)."""
    try:
        if not _allowed(filename):
            return "Error: File not allowed (not in current session uploads)"
        path = os.path.join("uploads", filename)
        img = Image.open(path).convert("RGBA")
        txt_layer = Image.new("RGBA", img.size)
        txt_layer.putalpha(0)
        draw = ImageDraw.Draw(txt_layer)
        def parse_color(s: str, a: int):
            t = s.strip().lower()
            if t.startswith("#"):
                t = t[1:]
                if len(t) == 6:
                    r = int(t[0:2], 16); g = int(t[2:4], 16); b = int(t[4:6], 16)
                    return (r, g, b, a)
                if len(t) == 3:
                    r = int(t[0]*2, 16); g = int(t[1]*2, 16); b = int(t[2]*2, 16)
                    return (r, g, b, a)
            if "," in t:
                parts = [p.strip() for p in t.split(",")]
                if len(parts) >= 3:
                    try:
                        r = int(parts[0]); g = int(parts[1]); b = int(parts[2])
                        return (r, g, b, a)
                    except Exception:
                        pass
            return (255, 255, 255, a)
        alpha = int(255 * max(0.0, min(1.0, opacity)))
        fill = parse_color(color, alpha)
        stroke_fill = parse_color(stroke_color, alpha)
        f = _choose_font(font_path, font_size)
        try:
            tw, th = draw.textsize(text, font=f)
        except Exception:
            tw, th = (font_size * max(1, len(text) // 2), font_size)
        px, py = x, y
        if mode == "center" or align == "center":
            px = (img.width - tw) // 2
            py = (img.height - th) // 2
        else:
            if align == "rt":
                px = img.width - tw - x
                py = y
            elif align == "rb":
                px = img.width - tw - x
                py = img.height - th - y
            elif align == "lb":
                px = x
                py = img.height - th - y
        px = max(0, min(px, img.width - tw))
        py = max(0, min(py, img.height - th))
        if mode == "single" or mode == "center":
            draw.text((px, py), text, font=f, fill=fill, stroke_width=2, stroke_fill=stroke_fill)
        else:
            step = max(20, spacing)
            for yy in range(0, img.height + step, step):
                for xx in range(0, img.width + step, step):
                    draw.text((xx, yy), text, font=f, fill=fill, stroke_width=2, stroke_fill=stroke_fill)
        if angle != 0.0 or mode == "diagonal":
            ang = angle if angle != 0.0 else 30.0
            txt_layer = txt_layer.rotate(ang, expand=False)
        out = Image.alpha_composite(img, txt_layer)
        b64 = _encode_image(out.convert("RGB"), "WEBP", quality=80)
        aid = _put_artifact(b64)
        return f"Text watermark added. [IMAGE_ID:{aid}:webp]"
    except Exception as e:
        return f"Error adding text watermark: {str(e)}"
    finally:
        try:
            os.remove(path)
        except Exception:
            pass

@tool
def image_add_image_watermark_upload(
    filename: str,
    watermark_filename: str,
    x: int = 10,
    y: int = 10,
    opacity: float = 0.3,
    scale: float = 1.0,
    mode: Literal["single", "tile", "diagonal", "center"] = "single",
    spacing: int = 160,
    angle: float = 0.0,
    align: Literal["lt", "rt", "lb", "rb", "center"] = "lt",
) -> str:
    """Overlay an uploaded image watermark with arrangement options; return base64 (WEBP)."""
    try:
        if not (_allowed(filename) and _allowed(watermark_filename)):
            return "Error: File not allowed (not in current session uploads)"
        base_path = os.path.join("uploads", filename)
        wm_path = os.path.join("uploads", watermark_filename)
        base = Image.open(base_path).convert("RGBA")
        wm = Image.open(wm_path).convert("RGBA")
        if scale != 1.0:
            w = int(max(1, wm.width * scale))
            h = int(max(1, wm.height * scale))
            wm = wm.resize((w, h))
        alpha = wm.split()[3]
        alpha = alpha.point(lambda p: int(p * max(0.0, min(1.0, opacity))))
        wm.putalpha(alpha)
        if angle != 0.0:
            wm = wm.rotate(angle, expand=True)
        overlay = Image.new("RGBA", base.size)
        overlay.putalpha(0)
        if mode == "single" or mode == "center":
            px, py = x, y
            if mode == "center" or align == "center":
                px = (base.width - wm.width) // 2
                py = (base.height - wm.height) // 2
            else:
                if align == "rt":
                    px = base.width - wm.width - x
                    py = y
                elif align == "rb":
                    px = base.width - wm.width - x
                    py = base.height - wm.height - y
                elif align == "lb":
                    px = x
                    py = base.height - wm.height - y
            px = max(0, min(px, base.width - wm.width))
            py = max(0, min(py, base.height - wm.height))
            overlay.paste(wm, (px, py), wm)
        else:
            step = max(10, spacing)
            for yy in range(0, base.height + step, step):
                for xx in range(0, base.width + step, step):
                    overlay.paste(wm, (xx, yy), wm)
            if mode == "diagonal" and angle == 0.0:
                overlay = overlay.rotate(30.0, expand=False)
        out = Image.alpha_composite(base, overlay)
        b64 = _encode_image(out.convert("RGB"), "WEBP", quality=80)
        aid = _put_artifact(b64)
        return f"Image watermark added. [IMAGE_ID:{aid}:webp]"
    except Exception as e:
        return f"Error adding image watermark: {str(e)}"
    finally:
        for p in (base_path, wm_path):
            try:
                os.remove(p)
            except Exception:
                pass

@tool
def image_remove_watermark_upload(
    filename: str,
    x: int,
    y: int,
    width: int,
    height: int,
    method: Literal["blur", "pixelate", "median", "clone_left", "clone_top"] = "blur",
    strength: int = 6,
    feather: int = 0,
) -> str:
    """Remove watermark from uploaded image using different methods; return base64 (WEBP)."""
    try:
        if not _allowed(filename):
            return "Error: File not allowed (not in current session uploads)"
        path = os.path.join("uploads", filename)
        img = Image.open(path).convert("RGBA")
        box = (x, y, x + width, y + height)
        region = img.crop(box)
        strength = max(1, strength)
        if method == "blur":
            region = region.filter(ImageFilter.GaussianBlur(radius=strength))
        elif method == "pixelate":
            small = region.resize((max(1, width // max(1, strength)), max(1, height // max(1, strength))), resample=Image.NEAREST)
            region = small.resize((width, height), resample=Image.NEAREST)
        elif method == "median":
            size = strength if strength % 2 == 1 else strength + 1
            region = region.filter(ImageFilter.MedianFilter(size=size))
        elif method in ("clone_left", "clone_top"):
            src_img = img.copy()
            if method == "clone_left":
                sx = max(0, x - width)
                sy = y
                src_box = (sx, sy, sx + width, sy + height)
            else:
                sx = x
                sy = max(0, y - height)
                src_box = (sx, sy, sx + width, sy + height)
            sx1, sy1, sx2, sy2 = src_box
            sx1 = max(0, min(sx1, src_img.width))
            sy1 = max(0, min(sy1, src_img.height))
            sx2 = max(0, min(sx2, src_img.width))
            sy2 = max(0, min(sy2, src_img.height))
            src_box = (sx1, sy1, sx2, sy2)
            sample = src_img.crop(src_box)
            if sample.size != (width, height):
                sample = sample.resize((width, height))
            region = sample
        out_img = img.copy()
        out_img.paste(region, (x, y))
        if feather > 0:
            mask = Image.new("L", img.size, 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.rectangle([x, y, x + width, y + height], fill=255)
            mask = mask.filter(ImageFilter.GaussianBlur(radius=feather))
            out_img = Image.composite(out_img, img, mask)
        b64 = _encode_image(out_img.convert("RGB"), "WEBP", quality=80)
        aid = _put_artifact(b64)
        return f"Watermark removed. [IMAGE_ID:{aid}:webp]"
    except Exception as e:
        return f"Error removing watermark: {str(e)}"
    finally:
        try:
            os.remove(path)
        except Exception:
            pass
def _allowed(filename: str) -> bool:
    allowed = os.environ.get("CURRENT_SESSION_UPLOADS", "")
    names = [x.strip() for x in re.split(r"[;,]", allowed) if x.strip()]
    return filename in names

@tool
def image_auto_remove_watermark_upload(
    filename: str,
    prefer: Literal["auto", "median", "clone", "blur"] = "auto"
) -> str:
    """Automatically detect and remove watermark from an uploaded image; return base64 (WEBP).
    - Heuristics: detect high-frequency residual against median background; threshold to get candidate mask.
    - If mask found and near edges, prefer cloning from adjacent area; otherwise median filter with feather.
    - Only operates on current session uploads and deletes source after processing.
    """
    try:
        if not _allowed(filename):
            return "Error: File not allowed (not in current session uploads)"
        path = os.path.join("uploads", filename)
        img = Image.open(path).convert("RGBA")
        rgb = img.convert("RGB")
        gray = rgb.convert("L")
        # median background
        size = max(5, (min(img.width, img.height) // 100) * 2 + 1)
        med = gray.filter(ImageFilter.MedianFilter(size=size))
        pos = ImageChops.subtract(gray, med)
        neg = ImageChops.subtract(med, gray)
        vals = list(pos.getdata()) + list(neg.getdata())
        vals.sort()
        thr = vals[int(len(vals) * 0.92)] if vals else 32
        m1 = pos.point(lambda p: 255 if p >= thr else 0)
        m2 = neg.point(lambda p: 255 if p >= thr else 0)
        edges = gray.filter(ImageFilter.FIND_EDGES)
        ve = list(edges.getdata())
        ve.sort()
        thr_e = ve[int(len(ve) * 0.85)] if ve else 32
        m3 = edges.point(lambda p: 255 if p >= thr_e else 0)
        merged = ImageChops.lighter(ImageChops.lighter(m1, m2), m3)
        merged = merged.filter(ImageFilter.MaxFilter(size=3)).filter(ImageFilter.MaxFilter(size=3))
        # mask fraction to decide strategy
        cnt = sum(1 for v in merged.getdata() if v)
        frac = cnt / float(img.width * img.height)
        bbox = merged.getbbox()
        if not bbox:
            # Fallback: common logo position at bottom-right
            bx1 = int(img.width * 0.65)
            by1 = int(img.height * 0.65)
            bx2 = int(img.width * 0.95)
            by2 = int(img.height * 0.95)
            bbox = (bx1, by1, bx2, by2)
        x1, y1, x2, y2 = bbox
        w = max(1, x2 - x1)
        h = max(1, y2 - y1)
        if frac > 0.3:
            # likely tiled watermark: apply median to entire image and blend by mask
            med_img = rgb.filter(ImageFilter.MedianFilter(size=5)).convert("RGBA")
            soft_mask = merged.filter(ImageFilter.GaussianBlur(radius=6))
            out_img = Image.composite(med_img, img, soft_mask)
        else:
            method = "median"
            feather = 6
            strength = max(5, min(25, (w + h) // 40))
            if prefer == "clone" or (prefer == "auto" and (x1 < img.width * 0.1 or y1 < img.height * 0.1 or x2 > img.width * 0.9 or y2 > img.height * 0.9)):
                method = "clone_left" if x1 > img.width // 2 else "clone_top"
            elif prefer == "blur":
                method = "blur"
            else:
                method = "median"
            box = (x1, y1, x1 + w, y1 + h)
            region = img.crop(box)
            if method == "blur":
                region = region.filter(ImageFilter.GaussianBlur(radius=strength))
            elif method == "median":
                size2 = strength if strength % 2 == 1 else strength + 1
                region = region.filter(ImageFilter.MedianFilter(size=size2))
            elif method in ("clone_left", "clone_top"):
                src_img = img.copy()
                if method == "clone_left":
                    sx = max(0, x1 - w)
                    sy = y1
                    src_box = (sx, sy, sx + w, sy + h)
                else:
                    sx = x1
                    sy = max(0, y1 - h)
                    src_box = (sx, sy, sx + w, sy + h)
                sx1, sy1, sx2, sy2 = src_box
                sx1 = max(0, min(sx1, src_img.width))
                sy1 = max(0, min(sy1, src_img.height))
                sx2 = max(0, min(sx2, src_img.width))
                sy2 = max(0, min(sy2, src_img.height))
                sample = src_img.crop((sx1, sy1, sx2, sy2))
                if sample.size != (w, h):
                    sample = sample.resize((w, h))
                region = sample
            out_img = img.copy()
            out_img.paste(region, (x1, y1))
            if feather > 0:
                mask = Image.new("L", img.size, 0)
                mdraw = ImageDraw.Draw(mask)
                mdraw.rectangle([x1, y1, x1 + w, y1 + h], fill=255)
                mask = mask.filter(ImageFilter.GaussianBlur(radius=feather))
                out_img = Image.composite(out_img, img, mask)
        b64 = _encode_image(out_img.convert("RGB"), "WEBP", quality=80)
        aid = _put_artifact(b64)
        return f"Watermark auto-removed. [IMAGE_ID:{aid}:webp]"
    except Exception as e:
        return f"Error auto-removing watermark: {str(e)}"
    finally:
        try:
            os.remove(path)
        except Exception:
            pass
