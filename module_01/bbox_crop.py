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

Out of range input
------------------
Model output is not guaranteed to stay inside 0-1000. Values outside that range
are clamped to it, and the resulting pixel coordinates are clamped to the image,
so the returned box always describes a region that really exists in the image.
An inverted box (``ymin > ymax`` or ``xmin > xmax``) cannot be clamped into
something meaningful and is rejected instead.

Pillow crop format
------------------
``PIL.Image.crop`` expects ``(left, upper, right, lower)``, which is the same as
``(xmin, ymin, xmax, ymax)`` -- x before y, the opposite order of the normalized
box, so the axes must be swapped explicitly.
"""

import numbers
import os

from PIL import Image

NORMALIZED_SCALE = 1000


def _clamp(value, lowest, highest):
    return max(lowest, min(value, highest))


def _unpack_box(box_1000):
    try:
        values = tuple(box_1000)
    except TypeError:
        raise ValueError(
            "box_1000 must be an iterable of 4 values ordered "
            "[ymin, xmin, ymax, xmax], got: {!r}".format(box_1000)
        ) from None

    if len(values) != 4:
        raise ValueError(
            "box_1000 must contain exactly 4 values ordered "
            "[ymin, xmin, ymax, xmax], got {} value(s): {!r}".format(
                len(values), values
            )
        )

    for value in values:
        if isinstance(value, bool) or not isinstance(value, numbers.Real):
            raise ValueError(
                "box_1000 values must be real numbers, got: {!r}".format(values)
            )

    return values


def normalize_to_pixels(box_1000, img_width, img_height):
    """Convert a 0-1000 normalized box into integer pixel coordinates.

    Args:
        box_1000: Bounding box as ``[ymin, xmin, ymax, xmax]`` on the 0-1000 scale.
            Values outside 0-1000 are clamped to the image edges.
        img_width: Real image width in pixels.
        img_height: Real image height in pixels.

    Returns:
        Tuple ``(xmin, ymin, xmax, ymax)`` in pixels, ready for Pillow's crop.
        Every coordinate is within the image, and never inverted.

    Raises:
        ValueError: If the box is not 4 real numbers, if it is inverted, or if
            the image size is not positive.
    """
    ymin, xmin, ymax, xmax = _unpack_box(box_1000)

    for name, size in (("img_width", img_width), ("img_height", img_height)):
        if isinstance(size, bool) or not isinstance(size, numbers.Real):
            raise ValueError("{} must be a real number, got: {!r}".format(name, size))
        if size <= 0:
            raise ValueError("{} must be positive, got: {!r}".format(name, size))

    if ymin > ymax or xmin > xmax:
        raise ValueError(
            "box_1000 is inverted; expected ymin <= ymax and xmin <= xmax in "
            "[ymin, xmin, ymax, xmax], got: {!r}".format(
                (ymin, xmin, ymax, xmax)
            )
        )

    # Out of range model output is pulled back onto the 0-1000 scale first.
    ymin = _clamp(ymin, 0, NORMALIZED_SCALE)
    xmin = _clamp(xmin, 0, NORMALIZED_SCALE)
    ymax = _clamp(ymax, 0, NORMALIZED_SCALE)
    xmax = _clamp(xmax, 0, NORMALIZED_SCALE)

    # x values scale with the width, y values scale with the height.
    xmin_pixel = int((xmin / NORMALIZED_SCALE) * img_width)
    xmax_pixel = int((xmax / NORMALIZED_SCALE) * img_width)
    ymin_pixel = int((ymin / NORMALIZED_SCALE) * img_height)
    ymax_pixel = int((ymax / NORMALIZED_SCALE) * img_height)

    # Guard against rounding pushing a coordinate past the last pixel.
    xmin_pixel = _clamp(xmin_pixel, 0, int(img_width))
    xmax_pixel = _clamp(xmax_pixel, 0, int(img_width))
    ymin_pixel = _clamp(ymin_pixel, 0, int(img_height))
    ymax_pixel = _clamp(ymax_pixel, 0, int(img_height))

    # Note the reordering: the input is y-first, the output is x-first.
    return (xmin_pixel, ymin_pixel, xmax_pixel, ymax_pixel)


def crop_region(image_path, box_1000, save_path=None, verbose=True):
    """Crop the region described by a normalized box out of an image.

    Args:
        image_path: Path to the source image.
        box_1000: Bounding box as ``[ymin, xmin, ymax, xmax]`` on the 0-1000 scale.
        save_path: Optional path to write the cropped image to.
        verbose: Print the conversion details to stdout. Set to ``False`` when
            calling this as a library.

    Returns:
        The cropped region as a ``PIL.Image`` object. It is never larger than
        the source image.

    Raises:
        FileNotFoundError: If ``image_path`` does not exist.
        ValueError: If ``box_1000`` is malformed or inverted.
    """
    # The source handle is closed as soon as the pixels have been copied out.
    with Image.open(image_path) as image:
        img_width, img_height = image.size

        pixel_box = normalize_to_pixels(box_1000, img_width, img_height)

        # crop() takes (left, upper, right, lower) == (xmin, ymin, xmax, ymax).
        cropped = image.crop(pixel_box)
        cropped.load()

    if verbose:
        print("Original image size: {} x {}".format(img_width, img_height))
        print(
            "Normalized box [ymin, xmin, ymax, xmax]: {}".format(list(box_1000))
        )
        print("Pixel box (xmin, ymin, xmax, ymax): {}".format(pixel_box))
        print("Cropped size: {} x {}".format(cropped.width, cropped.height))

    if save_path:
        cropped.save(save_path)
        if verbose:
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
