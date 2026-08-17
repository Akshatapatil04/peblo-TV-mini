"""
Asset generator for test suite and seed images.
Generates images with exact dimensions and color branding for testing all positive and negative upload cases.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../assets"))
os.makedirs(ASSETS_DIR, exist_ok=True)

def create_image(filename, width, height, bg_color, text, target_size_kb=None, format="JPEG", quality=85):
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw simple design with text and border
    draw.rectangle([(10, 10), (width - 10, height - 10)], outline=(255, 255, 255), width=4)
    # Simple centered text
    draw.text((width // 4, height // 2 - 20), text, fill=(255, 255, 255))
    draw.text((width // 4, height // 2 + 10), f"{width}x{height}", fill=(220, 220, 220))
    
    filepath = os.path.join(ASSETS_DIR, filename)
    
    if target_size_kb and target_size_kb > 200:
        # Create larger uncompressed data to exceed 200KB limit
        img_noise = Image.new("RGB", (width, height), color=bg_color)
        import random
        # Fill noise to prevent compression
        pixels = img_noise.load()
        for x in range(0, width, 2):
            for y in range(0, height, 2):
                pixels[x, y] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        img_noise.save(filepath, format="PNG")
    else:
        img.save(filepath, format=format, quality=quality)
    
    file_size_kb = os.path.getsize(filepath) / 1024
    print(f"Created {filename}: {width}x{height}, {file_size_kb:.1f} KB")

def main():
    # 1. Poster good (600x900, 2:3, < 200KB)
    create_image("poster_good.jpg", 600, 900, (41, 128, 185), "PEBLO POSTER")
    
    # 2. Poster wrong ratio (800x600, 4:3)
    create_image("poster_wrong_ratio.jpg", 800, 600, (192, 57, 43), "WRONG RATIO 4:3")
    
    # 3. Banner good (1280x720, 16:9, < 200KB)
    create_image("banner_good.jpg", 1280, 720, (39, 174, 96), "PEBLO BANNER")
    
    # 4. Banner too big (> 200KB)
    create_image("banner_too_big.png", 1280, 720, (142, 68, 173), "OVERSIZED BANNER", target_size_kb=350, format="PNG")
    
    # 5. Thumb good (640x360, 16:9, < 200KB)
    create_image("thumb_good.jpg", 640, 360, (230, 126, 34), "PEBLO THUMB")
    
    # 6. Thumb tiny (100x50, wrong resolution)
    create_image("thumb_tiny.jpg", 100, 50, (127, 140, 141), "TINY")

if __name__ == "__main__":
    main()
