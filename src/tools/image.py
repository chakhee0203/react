import base64
import io
from typing import Literal
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat
from langchain_core.tools import tool
import os

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

@tool
def image_resize_base64(image_base64: str, width: int, height: int) -> str:
    """Resize a base64-encoded image and return base64 (PNG)."""
    try:
        img = _decode_image(image_base64)
        resized = img.resize((width, height))
        b64 = _encode_image(resized, "PNG")
        return f"Image resized. [IMAGE:png:{b64}]"
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
        return f"Image converted. [IMAGE:{mime}:{b64}]"
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
        return f"Image cropped. [IMAGE:png:{b64}]"
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
        return f"Image compressed. [IMAGE:{mime}:{b64}]"
    except Exception as e:
        return f"Error compressing image: {str(e)}"

@tool
def image_rotate_base64(image_base64: str, angle: float, expand: bool = True) -> str:
    """Rotate image by angle degrees; return base64 (PNG)."""
    try:
        img = _decode_image(image_base64)
        rotated = img.rotate(angle, expand=expand)
        b64 = _encode_image(rotated, "PNG")
        return f"Image rotated. [IMAGE:png:{b64}]"
    except Exception as e:
        return f"Error rotating image: {str(e)}"

@tool
def image_add_text_watermark_base64(image_base64: str, text: str, x: int = 10, y: int = 10, opacity: float = 0.3, font_size: int = 24) -> str:
    """Add semi-transparent text watermark; return base64 (PNG)."""
    try:
        img = _decode_image(image_base64).convert("RGBA")
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        font = ImageFont.load_default()
        # If default font is too small, try scaling via stroke
        draw.text((x, y), text, font=font, fill=(255, 255, 255, int(255 * opacity)))
        out = Image.alpha_composite(img, txt_layer)
        b64 = _encode_image(out.convert("RGB"), "PNG")
        return f"Text watermark added. [IMAGE:png:{b64}]"
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
        return f"Image watermark added. [IMAGE:png:{b64}]"
    except Exception as e:
        return f"Error adding image watermark: {str(e)}"

@tool
def image_remove_watermark_base64(image_base64: str, x: int, y: int, width: int, height: int, method: Literal["blur", "pixelate"] = "blur") -> str:
    """Naively remove watermark by blurring or pixelating selected rectangle; return base64 (PNG)."""
    try:
        img = _decode_image(image_base64).convert("RGBA")
        box = (x, y, x + width, y + height)
        region = img.crop(box)
        if method == "blur":
            region = region.filter(ImageFilter.GaussianBlur(radius=6))
        else:
            # pixelate
            small = region.resize((max(1, width // 10), max(1, height // 10)), resample=Image.NEAREST)
            region = small.resize((width, height), resample=Image.NEAREST)
        img.paste(region, (x, y))
        b64 = _encode_image(img.convert("RGB"), "PNG")
        return f"Watermark removed. [IMAGE:png:{b64}]"
    except Exception as e:
        return f"Error removing watermark: {str(e)}"

@tool
def image_upload_to_base64(filename: str) -> str:
    """Read uploaded image from 'uploads/' and return as base64 (PNG)."""
    try:
        path = os.path.join("uploads", filename)
        with open(path, "rb") as f:
            data = f.read()
        # Detect format roughly via Pillow
        img = Image.open(io.BytesIO(data))
        fmt = img.format or "PNG"
        # Normalize to given format when encoding
        b64 = base64.b64encode(data).decode("utf-8")
        mime = fmt.lower()
        return f"Image loaded. [IMAGE:{mime}:{b64}]"
    except Exception as e:
        return f"Error reading uploaded image: {str(e)}"

@tool
def image_crop_upload(filename: str, x: int, y: int, width: int, height: int) -> str:
    """Crop an uploaded image to a rectangle and return base64 (WEBP)."""
    try:
        path = os.path.join("uploads", filename)
        img = Image.open(path)
        box = (x, y, x + width, y + height)
        cropped = img.crop(box)
        b64 = _encode_image(cropped, "WEBP", quality=80)
        return f"Image cropped. [IMAGE:webp:{b64}]"
    except Exception as e:
        return f"Error cropping image: {str(e)}"

@tool
def image_compress_upload(filename: str, quality: int = 75, format: Literal["JPEG", "WEBP"] = "JPEG") -> str:
    """Compress an uploaded image by re-encoding with given quality; return base64."""
    try:
        path = os.path.join("uploads", filename)
        img = Image.open(path).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format=format, quality=quality, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        mime = "jpeg" if format == "JPEG" else "webp"
        return f"Image compressed. [IMAGE:{mime}:{b64}]"
    except Exception as e:
        return f"Error compressing image: {str(e)}"

@tool
def image_rotate_upload(filename: str, angle: float, expand: bool = True) -> str:
    """Rotate an uploaded image by angle degrees; return base64 (WEBP)."""
    try:
        path = os.path.join("uploads", filename)
        img = Image.open(path)
        rotated = img.rotate(angle, expand=expand)
        b64 = _encode_image(rotated, "WEBP", quality=80)
        return f"Image rotated. [IMAGE:webp:{b64}]"
    except Exception as e:
        return f"Error rotating image: {str(e)}"

@tool
def image_add_text_watermark_upload(filename: str, text: str, x: int = 10, y: int = 10, opacity: float = 0.3, font_size: int = 24) -> str:
    """Add semi-transparent text watermark to an uploaded image; return base64 (WEBP)."""
    try:
        path = os.path.join("uploads", filename)
        img = Image.open(path).convert("RGBA")
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        # Try to load a truetype font with the requested size for visibility
        font_candidates = [
            "arial.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "DejaVuSans.ttf",
        ]
        font = None
        for fp in font_candidates:
            if os.path.exists(fp):
                try:
                    font = ImageFont.truetype(fp, font_size)
                    break
                except Exception:
                    pass
        if font is None:
            # Fallback to default font if truetype is unavailable
            font = ImageFont.load_default()

        # Ensure coordinates are within image bounds considering text size
        try:
            tw, th = draw.textsize(text, font=font)
        except Exception:
            tw, th = (font_size * max(1, len(text) // 2), font_size)
        x = max(0, min(x, img.width - tw))
        y = max(0, min(y, img.height - th))

        # Choose contrasting colors: white text with black stroke improves visibility
        alpha = int(255 * opacity)
        fill = (255, 255, 255, alpha)
        stroke_fill = (0, 0, 0, alpha)

        draw.text((x, y), text, font=font, fill=fill, stroke_width=2, stroke_fill=stroke_fill)
        out = Image.alpha_composite(img, txt_layer)
        b64 = _encode_image(out.convert("RGB"), "WEBP", quality=80)
        return f"Text watermark added. [IMAGE:webp:{b64}]"
    except Exception as e:
        return f"Error adding text watermark: {str(e)}"

@tool
def image_add_image_watermark_upload(filename: str, watermark_filename: str, x: int = 10, y: int = 10, opacity: float = 0.3, scale: float = 1.0) -> str:
    """Overlay an uploaded image watermark on another uploaded image; return base64 (WEBP)."""
    try:
        base_path = os.path.join("uploads", filename)
        wm_path = os.path.join("uploads", watermark_filename)
        base = Image.open(base_path).convert("RGBA")
        wm = Image.open(wm_path).convert("RGBA")
        if scale != 1.0:
            w = int(wm.width * scale)
            h = int(wm.height * scale)
            wm = wm.resize((w, h))
        alpha = wm.split()[3]
        alpha = alpha.point(lambda p: int(p * opacity))
        wm.putalpha(alpha)
        base.paste(wm, (x, y), wm)
        b64 = _encode_image(base.convert("RGB"), "WEBP", quality=80)
        return f"Image watermark added. [IMAGE:webp:{b64}]"
    except Exception as e:
        return f"Error adding image watermark: {str(e)}"

@tool
def image_remove_watermark_upload(filename: str, x: int, y: int, width: int, height: int, method: Literal["blur", "pixelate"] = "blur") -> str:
    """Naively remove watermark from uploaded image by blurring or pixelating selected rectangle; return base64 (WEBP)."""
    try:
        path = os.path.join("uploads", filename)
        img = Image.open(path).convert("RGBA")
        box = (x, y, x + width, y + height)
        region = img.crop(box)
        if method == "blur":
            region = region.filter(ImageFilter.GaussianBlur(radius=6))
        else:
            small = region.resize((max(1, width // 10), max(1, height // 10)), resample=Image.NEAREST)
            region = small.resize((width, height), resample=Image.NEAREST)
        img.paste(region, (x, y))
        b64 = _encode_image(img.convert("RGB"), "WEBP", quality=80)
        return f"Watermark removed. [IMAGE:webp:{b64}]"
    except Exception as e:
        return f"Error removing watermark: {str(e)}"
