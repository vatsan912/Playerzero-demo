"""Tests for bbox_crop: normalized 0-1000 box conversion and image cropping.

Run from anywhere with:
    python3 -m unittest module_01.test_bbox_crop
"""

import io
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bbox_crop import crop_region, normalize_to_pixels


class NormalizeToPixelsTest(unittest.TestCase):
    def test_returns_x_first_order(self):
        # Deliberately asymmetric box on a square image: if the axes were not
        # swapped the result would be (10, 20, 30, 40) instead.
        self.assertEqual(
            normalize_to_pixels([20, 10, 40, 30], 1000, 1000), (10, 20, 30, 40)
        )

    def test_x_scales_with_width_and_y_with_height(self):
        self.assertEqual(
            normalize_to_pixels([250, 100, 750, 900], 800, 400), (80, 100, 720, 300)
        )

    def test_demo_box_on_wide_image(self):
        # The 0-1000 scale is per axis, so ymax=500 of a 500px tall image is 250px.
        self.assertEqual(
            normalize_to_pixels([0, 0, 500, 500], 1000, 500), (0, 0, 500, 250)
        )

    def test_full_scale_box_covers_whole_image(self):
        self.assertEqual(
            normalize_to_pixels([0, 0, 1000, 1000], 640, 480), (0, 0, 640, 480)
        )

    def test_same_box_maps_to_different_pixels_per_image_size(self):
        box = [0, 0, 500, 500]
        self.assertEqual(normalize_to_pixels(box, 200, 100), (0, 0, 100, 50))
        self.assertEqual(normalize_to_pixels(box, 2000, 1000), (0, 0, 1000, 500))

    def test_degenerate_box_has_zero_area(self):
        self.assertEqual(
            normalize_to_pixels([500, 500, 500, 500], 1000, 1000), (500, 500, 500, 500)
        )

    def test_fractional_values_are_truncated_to_integers(self):
        # 333 / 1000 * 100 == 33.3 -> 33
        result = normalize_to_pixels([333, 333, 666, 666], 100, 100)
        self.assertEqual(result, (33, 33, 66, 66))
        for value in result:
            self.assertIsInstance(value, int)

    def test_accepts_a_tuple_box(self):
        self.assertEqual(
            normalize_to_pixels((0, 0, 1000, 500), 100, 100), (0, 0, 50, 100)
        )


class CropRegionTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.image_path = os.path.join(self.tmpdir, "source.jpg")
        Image.new("RGB", (1000, 500), "red").save(self.image_path)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _crop(self, box, save_path=None):
        # Swallow the informational prints so test output stays readable.
        with redirect_stdout(io.StringIO()) as captured:
            cropped = crop_region(self.image_path, box, save_path=save_path)
        return cropped, captured.getvalue()

    def test_returns_pil_image_of_expected_size(self):
        cropped, _ = self._crop([0, 0, 500, 500])
        self.assertIsInstance(cropped, Image.Image)
        self.assertEqual(cropped.size, (500, 250))

    def test_crops_the_requested_region_not_the_transposed_one(self):
        # Right half of the width only; a transposed box would fail to be 500 wide.
        cropped, _ = self._crop([0, 500, 1000, 1000])
        self.assertEqual(cropped.size, (500, 500))

    def test_saves_file_when_save_path_given(self):
        save_path = os.path.join(self.tmpdir, "out.jpg")
        _, output = self._crop([0, 0, 500, 500], save_path=save_path)
        self.assertTrue(os.path.exists(save_path))
        with Image.open(save_path) as saved:
            self.assertEqual(saved.size, (500, 250))
        self.assertIn(save_path, output)

    def test_writes_nothing_when_save_path_omitted(self):
        self._crop([0, 0, 500, 500])
        self.assertEqual(os.listdir(self.tmpdir), ["source.jpg"])

    def test_source_image_is_left_unchanged(self):
        self._crop([0, 0, 500, 500])
        with Image.open(self.image_path) as source:
            self.assertEqual(source.size, (1000, 500))

    def test_reports_original_size_and_pixel_box(self):
        _, output = self._crop([0, 0, 500, 500])
        self.assertIn("1000 x 500", output)
        self.assertIn("(0, 0, 500, 250)", output)

    def test_missing_image_raises(self):
        with self.assertRaises(FileNotFoundError):
            crop_region(os.path.join(self.tmpdir, "nope.jpg"), [0, 0, 500, 500])


if __name__ == "__main__":
    unittest.main()
