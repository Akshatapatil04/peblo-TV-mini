import io
from typing import Tuple, Dict, Any, Optional
from PIL import Image

class ImageValidationError(Exception):
    """Exception raised when an uploaded image fails validation."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

ARTWORK_SPECS = {
    "poster": {
        "aspect_name": "2:3",
        "expected_aspect_ratio": 2.0 / 3.0,  # ~0.6667
        "target_px": (600, 900),
        "min_px": (400, 600),
        "max_kb": 200,
        "description": "Show Poster (Portrait, 2:3 ratio, ~600x900px, max 200KB)"
    },
    "banner": {
        "aspect_name": "16:9",
        "expected_aspect_ratio": 16.0 / 9.0,  # ~1.7778
        "target_px": (1280, 720),
        "min_px": (960, 540),
        "max_kb": 200,
        "description": "Show Hero Banner (Landscape, 16:9 ratio, ~1280x720px, max 200KB)"
    },
    "thumbnail": {
        "aspect_name": "16:9",
        "expected_aspect_ratio": 16.0 / 9.0,  # ~1.7778
        "target_px": (640, 360),
        "min_px": (320, 180),
        "max_kb": 200,
        "description": "Episode Thumbnail (Landscape, 16:9 ratio, ~640x360px, max 200KB)"
    }
}

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

def validate_artwork(
    file_bytes: bytes,
    slot_type: str,
    aspect_tolerance: float = 0.04
) -> Tuple[Image.Image, Dict[str, Any]]:
    """
    Validate artwork image against slot specifications in reference.json.
    Returns the parsed PIL Image and metadata dict if valid, raises ImageValidationError with editor-friendly messages.
    """
    slot_type = slot_type.lower()
    if slot_type not in ARTWORK_SPECS:
        raise ImageValidationError(
            f"Unknown artwork slot '{slot_type}'. Allowed slots are: {', '.join(ARTWORK_SPECS.keys())}."
        )

    spec = ARTWORK_SPECS[slot_type]
    file_size_bytes = len(file_bytes)
    file_size_kb = file_size_bytes / 1024.0

    # 1. Enforce 200 KB ceiling
    max_kb = spec["max_kb"]
    if file_size_kb > max_kb:
        raise ImageValidationError(
            f"File size is {file_size_kb:.1f} KB, which exceeds the {max_kb} KB maximum limit. "
            f"Please compress or resize the image before uploading.",
            details={
                "slot_type": slot_type,
                "file_size_kb": round(file_size_kb, 1),
                "max_kb": max_kb,
                "rule": "file_size"
            }
        )

    # 2. Inspect Image format and readability
    try:
        image = Image.open(io.BytesIO(file_bytes))
        image.load()
    except Exception:
        raise ImageValidationError(
            "The uploaded file is not a valid or readable image. "
            "Please upload a standard JPEG, PNG, or WebP image file.",
            details={"slot_type": slot_type, "rule": "format"}
        )

    img_format = (image.format or "").upper()
    if img_format not in ALLOWED_FORMATS:
        raise ImageValidationError(
            f"Unsupported image format '{img_format}'. Please upload a JPEG, PNG, or WebP image.",
            details={"slot_type": slot_type, "format": img_format, "rule": "format"}
        )

    width, height = image.size
    if width <= 0 or height <= 0:
        raise ImageValidationError(
            "Invalid image dimensions (0px). Please check the file.",
            details={"slot_type": slot_type, "rule": "dimensions"}
        )

    # 3. Check Minimum Dimensions
    min_w, min_h = spec["min_px"]
    target_w, target_h = spec["target_px"]
    if width < min_w or height < min_h:
        raise ImageValidationError(
            f"Image dimensions ({width}×{height}px) are too small for {slot_type}. "
            f"Target size is ~{target_w}×{target_h}px (minimum {min_w}×{min_h}px).",
            details={
                "slot_type": slot_type,
                "actual_dimensions": f"{width}x{height}",
                "target_dimensions": f"{target_w}x{target_h}",
                "min_dimensions": f"{min_w}x{min_h}",
                "rule": "dimensions_too_small"
            }
        )

    # 4. Validate Aspect Ratio
    actual_ratio = width / float(height)
    expected_ratio = spec["expected_aspect_ratio"]
    aspect_diff = abs(actual_ratio - expected_ratio) / expected_ratio

    if aspect_diff > aspect_tolerance:
        ratio_name = f"{width}:{height}" if width < height else f"{width//10}:{height//10}"
        raise ImageValidationError(
            f"Invalid aspect ratio for {slot_type}: The image is {width}×{height}px (ratio {actual_ratio:.2f}). "
            f"{slot_type.capitalize()} requires a {spec['aspect_name']} aspect ratio (~{target_w}×{target_h}px).",
            details={
                "slot_type": slot_type,
                "actual_dimensions": f"{width}x{height}",
                "actual_ratio": round(actual_ratio, 2),
                "expected_ratio": spec["aspect_name"],
                "target_dimensions": f"{target_w}x{target_h}",
                "rule": "aspect_ratio"
            }
        )

    mime_type = "image/jpeg"
    if img_format == "PNG":
        mime_type = "image/png"
    elif img_format == "WEBP":
        mime_type = "image/webp"

    metadata = {
        "slot_type": slot_type,
        "width": width,
        "height": height,
        "file_size_bytes": file_size_bytes,
        "file_size_kb": round(file_size_kb, 1),
        "mime_type": mime_type,
        "format": img_format,
        "aspect_ratio": spec["aspect_name"]
    }

    return image, metadata
