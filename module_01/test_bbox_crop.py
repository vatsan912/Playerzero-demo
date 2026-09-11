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
from unittest import mock

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bbox_crop
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

    def test_out_of_range_box_never_exceeds_the_source_image(self):
        cropped, _ = self._crop([0, 0, 2500, 2500])
        self.assertEqual(cropped.size, (1000, 500))

    def test_verbose_false_prints_nothing(self):
        with redirect_stdout(io.StringIO()) as captured:
            crop_region(self.image_path, [0, 0, 500, 500], verbose=False)
        self.assertEqual(captured.getvalue(), "")

    def test_verbose_false_still_saves_when_asked(self):
        save_path = os.path.join(self.tmpdir, "quiet.jpg")
        with redirect_stdout(io.StringIO()) as captured:
            crop_region(
                self.image_path, [0, 0, 500, 500], save_path=save_path, verbose=False
            )
        self.assertTrue(os.path.exists(save_path))
        self.assertEqual(captured.getvalue(), "")

    def test_source_handle_is_closed_before_returning(self):
        real_open = Image.open
        opened = []

        def tracking_open(*args, **kwargs):
            image = real_open(*args, **kwargs)
            opened.append(image)
            return image

        with mock.patch.object(bbox_crop.Image, "open", tracking_open):
            cropped, _ = self._crop([0, 0, 500, 500])

        self.assertEqual(len(opened), 1)
        self.assertIsNone(opened[0].fp)
        # The pixels must survive the source being closed.
        self.assertEqual(cropped.size, (500, 250))
        self.assertIsNotNone(cropped.getpixel((0, 0)))

    def test_inverted_box_is_rejected_before_reaching_pillow(self):
        with self.assertRaises(ValueError) as ctx:
            crop_region(self.image_path, [800, 800, 200, 200], verbose=False)
        self.assertIn("inverted", str(ctx.exception))


class OutOfRangeBoxTest(unittest.TestCase):
    def test_values_above_the_scale_are_clamped_to_the_image(self):
        self.assertEqual(
            normalize_to_pixels([0, 0, 1200, 1200], 640, 480), (0, 0, 640, 480)
        )

    def test_negative_values_are_clamped_to_the_origin(self):
        self.assertEqual(
            normalize_to_pixels([-100, -100, 500, 500], 640, 480), (0, 0, 320, 240)
        )

    def test_box_far_outside_the_scale_becomes_the_whole_image(self):
        self.assertEqual(
            normalize_to_pixels([-5000, -5000, 5000, 5000], 640, 480), (0, 0, 640, 480)
        )

    def test_clamped_box_is_still_x_first_and_ordered(self):
        xmin, ymin, xmax, ymax = normalize_to_pixels([-10, 1200, 1200, 1300], 800, 400)
        self.assertLessEqual(xmin, xmax)
        self.assertLessEqual(ymin, ymax)
        self.assertEqual((xmin, ymin, xmax, ymax), (800, 0, 800, 400))


class InvalidInputTest(unittest.TestCase):
    def test_inverted_y_axis_raises(self):
        with self.assertRaises(ValueError) as ctx:
            normalize_to_pixels([900, 0, 100, 500], 640, 480)
        self.assertIn("inverted", str(ctx.exception))

    def test_inverted_x_axis_raises(self):
        with self.assertRaises(ValueError) as ctx:
            normalize_to_pixels([0, 900, 500, 100], 640, 480)
        self.assertIn("inverted", str(ctx.exception))

    def test_wrong_number_of_values_raises_a_clear_error(self):
        with self.assertRaises(ValueError) as ctx:
            normalize_to_pixels([0, 0, 500], 640, 480)
        self.assertIn("exactly 4", str(ctx.exception))

    def test_non_iterable_box_raises_a_clear_error(self):
        with self.assertRaises(ValueError) as ctx:
            normalize_to_pixels(500, 640, 480)
        self.assertIn("iterable of 4", str(ctx.exception))

    def test_non_numeric_values_raise(self):
        with self.assertRaises(ValueError) as ctx:
            normalize_to_pixels([0, 0, "500", 500], 640, 480)
        self.assertIn("real numbers", str(ctx.exception))

    def test_zero_or_negative_image_size_raises(self):
        for width, height in ((0, 480), (640, 0), (-640, 480), (640, -480)):
            with self.subTest(width=width, height=height):
                with self.assertRaises(ValueError) as ctx:
                    normalize_to_pixels([0, 0, 500, 500], width, height)
                self.assertIn("must be positive", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
