import os
import pytest
from backend.app.services.image_validator import validate_artwork, ImageValidationError

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../assets"))

def test_valid_poster_passes():
    """Poster meeting 2:3 aspect ratio (~600x900) and < 200KB must pass."""
    path = os.path.join(ASSETS_DIR, "poster_good.jpg")
    with open(path, "rb") as f:
        file_bytes = f.read()

    image, meta = validate_artwork(file_bytes, "poster")
    assert meta["width"] == 600
    assert meta["height"] == 900
    assert meta["file_size_kb"] < 200.0
    assert meta["aspect_ratio"] == "2:3"

def test_poster_wrong_ratio_fails_with_editor_message():
    """Uploading 800x600 (4:3) as a poster must fail with clear aspect ratio error."""
    path = os.path.join(ASSETS_DIR, "poster_wrong_ratio.jpg")
    with open(path, "rb") as f:
        file_bytes = f.read()

    with pytest.raises(ImageValidationError) as exc_info:
        validate_artwork(file_bytes, "poster")

    err = exc_info.value
    assert "Invalid aspect ratio for poster" in err.message
    assert "2:3" in err.message
    assert err.details.get("rule") == "aspect_ratio"

def test_oversized_banner_fails():
    """Banner exceeding 200 KB must fail validation."""
    path = os.path.join(ASSETS_DIR, "banner_too_big.png")
    with open(path, "rb") as f:
        file_bytes = f.read()

    with pytest.raises(ImageValidationError) as exc_info:
        validate_artwork(file_bytes, "banner")

    err = exc_info.value
    assert "exceeds the 200 KB maximum limit" in err.message
    assert err.details.get("rule") == "file_size"

def test_tiny_thumbnail_fails():
    """Image with dimensions too small for thumbnail must fail."""
    path = os.path.join(ASSETS_DIR, "thumb_tiny.jpg")
    with open(path, "rb") as f:
        file_bytes = f.read()

    with pytest.raises(ImageValidationError) as exc_info:
        validate_artwork(file_bytes, "thumbnail")

    err = exc_info.value
    assert "too small" in err.message
    assert err.details.get("rule") in ("dimensions_too_small", "aspect_ratio")

def test_corrupted_file_fails():
    """Non-image bytes must fail format validation."""
    garbage = b"not a real jpeg file header at all"
    with pytest.raises(ImageValidationError) as exc_info:
        validate_artwork(garbage, "poster")

    err = exc_info.value
    assert "not a valid or readable image" in err.message
