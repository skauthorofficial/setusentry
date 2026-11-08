"""
Unit tests for SetuSentry image processing and validation utilities.
"""

import io
import os
import tempfile
import unittest
import sys
from PIL import Image

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from utils.image_utils import (
    generate_synthetic_concrete_image,
    save_uploaded_image,
    validate_image_upload,
)


class TestImageUtils(unittest.TestCase):

    def test_synthetic_image_generation(self):
        # Cracked image
        cracked_img = generate_synthetic_concrete_image(is_cracked=True, width=300, height=200)
        self.assertIsInstance(cracked_img, Image.Image)
        self.assertEqual(cracked_img.size, (300, 200))

        # Sound image
        sound_img = generate_synthetic_concrete_image(is_cracked=False, width=300, height=200)
        self.assertIsInstance(sound_img, Image.Image)
        self.assertEqual(sound_img.size, (300, 200))

    def test_validate_image_valid_png(self):
        img = generate_synthetic_concrete_image(is_cracked=True, width=200, height=150)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        bytes_data = buf.getvalue()

        is_valid, err = validate_image_upload(bytes_data, "test_crack.png")
        self.assertTrue(is_valid)
        self.assertEqual(err, "")

    def test_validate_image_invalid_extension(self):
        bytes_data = b"dummy text content"
        is_valid, err = validate_image_upload(bytes_data, "document.pdf")
        self.assertFalse(is_valid)
        self.assertIn("Unsupported file extension", err)

    def test_validate_image_empty_bytes(self):
        is_valid, err = validate_image_upload(b"", "empty.jpg")
        self.assertFalse(is_valid)
        self.assertIn("empty", err.lower())

    def test_save_uploaded_image(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            img = generate_synthetic_concrete_image(is_cracked=False, width=100, height=100)
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            bytes_data = buf.getvalue()

            saved_path = save_uploaded_image(bytes_data, "upload.jpg", tmp_dir)
            self.assertTrue(os.path.exists(saved_path))
            self.assertTrue(saved_path.endswith(".jpg"))


if __name__ == "__main__":
    unittest.main()
