"""
SetuSentry Image Utilities
Provides image validation, synthetic test image generation (cracked and sound concrete),
and upload management.
"""

from __future__ import annotations
import io
import os
import time
from typing import Optional, Tuple
import cv2
import numpy as np
from PIL import Image, ImageDraw


def validate_image_upload(file_bytes: bytes, filename: str, max_size_mb: int = 15) -> Tuple[bool, str]:
    """
    Validate uploaded image bytes for format, corruption, and reasonable dimensions.
    Returns (is_valid, error_message).
    """
    if not file_bytes:
        return False, "File is empty."

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > max_size_mb:
        return False, f"File size ({size_mb:.1f} MB) exceeds maximum allowed limit of {max_size_mb} MB."

    allowed_exts = {".jpg", ".jpeg", ".png"}
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_exts:
        return False, f"Unsupported file extension '{ext}'. Only JPG, JPEG, and PNG are allowed."

    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()  # Verify integrity
        # Re-open after verify() closes the file
        img = Image.open(io.BytesIO(file_bytes))
        w, h = img.size
        if w < 50 or h < 50:
            return False, f"Image dimensions too small ({w}x{h} px). Minimum required is 50x50 px."
        if w > 8000 or h > 8000:
            return False, f"Image dimensions too large ({w}x{h} px). Maximum allowed is 8000x8000 px."
    except Exception as e:
        return False, f"Invalid or corrupted image file: {str(e)}"

    return True, ""


def save_uploaded_image(file_bytes: bytes, original_filename: str, upload_dir: str) -> str:
    """
    Save uploaded image to the target directory with a unique timestamped name.
    Returns the saved absolute file path.
    """
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(original_filename)[1].lower()
    timestamp = int(time.time() * 1000)
    clean_name = f"inspection_{timestamp}{ext}"
    target_path = os.path.join(upload_dir, clean_name)

    with open(target_path, "wb") as f:
        f.write(file_bytes)

    return target_path


def generate_synthetic_concrete_image(is_cracked: bool = True, width: int = 600, height: int = 400) -> Image.Image:
    """
    Generate a realistic synthetic concrete slab texture.
    If is_cracked is True, adds realistic meandering dark fractures with micro-branches.
    Useful for demonstration, automated testing, and offline trials.
    """
    np.random.seed(42 if is_cracked else 100)

    # Base gray concrete tone with noise
    base_color = 160
    noise = np.random.normal(0, 18, (height, width)).astype(np.float32)
    slab = np.clip(base_color + noise, 0, 255).astype(np.uint8)

    # Convert to 3-channel BGR for OpenCV processing
    slab_bgr = cv2.cvtColor(slab, cv2.COLOR_GRAY2BGR)

    # Add aggregate speckles (dark and light spots)
    num_speckles = 1200
    for _ in range(num_speckles):
        sx = np.random.randint(0, width)
        sy = np.random.randint(0, height)
        radius = np.random.randint(1, 4)
        shade = int(np.random.choice([70, 90, 220, 240]))
        cv2.circle(slab_bgr, (sx, sy), radius, (shade, shade, shade), -1)

    # Slight blur to blend aggregates naturally into concrete matrix
    slab_bgr = cv2.GaussianBlur(slab_bgr, (3, 3), 0)

    if is_cracked:
        # Generate primary jagged crack path
        start_x = int(width * 0.15)
        start_y = int(height * 0.2)
        end_x = int(width * 0.85)
        end_y = int(height * 0.8)

        steps = 35
        xs = np.linspace(start_x, end_x, steps)
        ys = np.linspace(start_y, end_y, steps)

        points = []
        for i in range(steps):
            jitter_x = int(xs[i] + np.random.randint(-15, 15))
            jitter_y = int(ys[i] + np.random.randint(-20, 20))
            points.append((jitter_x, jitter_y))

        # Draw main jagged fracture with varying thickness
        for i in range(len(points) - 1):
            thickness = np.random.randint(2, 4)
            crack_color = (int(np.random.randint(25, 45)), int(np.random.randint(25, 45)), int(np.random.randint(25, 45)))
            cv2.line(slab_bgr, points[i], points[i + 1], crack_color, thickness)

            # Draw occasional micro-branching crack
            if i % 7 == 0 and i > 0:
                branch_len = np.random.randint(25, 55)
                bx = points[i][0] + np.random.randint(-branch_len, branch_len)
                by = points[i][1] + np.random.randint(-branch_len, branch_len)
                cv2.line(slab_bgr, points[i], (bx, by), (40, 40, 40), 1)

        # Draw secondary smaller fracture
        sec_points = [
            (int(width * 0.65), int(height * 0.25)),
            (int(width * 0.72), int(height * 0.35)),
            (int(width * 0.78), int(height * 0.50)),
        ]
        for i in range(len(sec_points) - 1):
            cv2.line(slab_bgr, sec_points[i], sec_points[i + 1], (35, 35, 35), 2)

    # Convert BGR back to PIL RGB
    img_rgb = cv2.cvtColor(slab_bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(img_rgb)
