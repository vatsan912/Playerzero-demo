"""Convert normalized bounding boxes into image pixel coordinates and crop them.

Normalized coordinate system
----------------------------
AI models often emit bounding boxes on a resolution independent 0-1000 scale in
the order ``[ymin, xmin, ymax, xmax]``. A value of 0 is the top/left edge of the
image and 1000 is the bottom/right edge, regardless of the real image size.

Coordinate conversion
---------------------
To map a normalized value onto real pixels, divide it by 1000 (giving a 0-1
fraction of the image) and multiply by the image width (for x values) or the
image height (for y values).

Pillow crop format
------------------
``PIL.Image.crop`` expects ``(left, upper, right, lower)``, which is the same as
``(xmin, ymin, xmax, ymax)`` -- x before y, the opposite order of the normalized
box, so the axes must be swapped explicitly.
"""

import os

from PIL import Image


def normalize_to_pixels(box_1000, img_width, img_height):
    """Convert a 0-1000 normalized box into integer pixel coordinates.

    Args:
        box_1000: Bounding box as ``[ymin, xmin, ymax, xmax]`` on the 0-1000 scale.
        img_width: Real image width in pixels.
        img_height: Real image height in pixels.

    Returns:
        Tuple ``(xmin, ymin, xmax, ymax)`` in pixels, ready for Pillow's crop.
    """
    ymin, xmin, ymax, xmax = box_1000

    # x values scale with the width, y values scale with the height.
    xmin_pixel = int((xmin / 1000) * img_width)
    xmax_pixel = int((xmax / 1000) * img_width)
    ymin_pixel = int((ymin / 1000) * img_height)
    ymax_pixel = int((ymax / 1000) * img_height)

    # Note the reordering: the input is y-first, the output is x-first.
    return (xmin_pixel, ymin_pixel, xmax_pixel, ymax_pixel)


def crop_region(image_path, box_1000, save_path=None):
    """Crop the region described by a normalized box out of an image.

    Args:
        image_path: Path to the source image.
        box_1000: Bounding box as ``[ymin, xmin, ymax, xmax]`` on the 0-1000 scale.
        save_path: Optional path to write the cropped image to.

    Returns:
        The cropped region as a ``PIL.Image`` object.
    """
    image = Image.open(image_path)
    img_width, img_height = image.size

    pixel_box = normalize_to_pixels(box_1000, img_width, img_height)

    # crop() takes (left, upper, right, lower) == (xmin, ymin, xmax, ymax).
    cropped = image.crop(pixel_box)

    print("Original image size: {} x {}".format(img_width, img_height))
    print("Normalized box [ymin, xmin, ymax, xmax]: {}".format(list(box_1000)))
    print("Pixel box (xmin, ymin, xmax, ymax): {}".format(pixel_box))
    print("Cropped size: {} x {}".format(cropped.width, cropped.height))

    if save_path:
        cropped.save(save_path)
        print("Saved cropped image to: {}".format(save_path))

    return cropped


if __name__ == "__main__":
    sample_path = os.path.join("module_01", "sample_image.jpg")
    output_path = os.path.join("module_01", "cropped_output.jpg")

    # Make sure there is an image to work with, creating a plain red one if needed.
    if not os.path.exists(sample_path):
        os.makedirs(os.path.dirname(sample_path), exist_ok=True)
        Image.new("RGB", (1000, 500), "red").save(sample_path)
        print("Created synthetic sample image at: {}".format(sample_path))

    # Top-left region: half the width and half the height of the image.
    crop_region(sample_path, [0, 0, 500, 500], save_path=output_path)
