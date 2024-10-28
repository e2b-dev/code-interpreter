from typing import Any, io

from IPython.core.display_functions import display
from PIL import ImageShow
from PIL.Image import Image

original_show = ImageShow.show


def show_file(self, path: str, **options: Any) -> int:
    # To prevent errors from trying to display image without any display
    return 0


ImageShow.show_file = show_file

original_save = Image.save


# To prevent circular save and display calls
def __repr_image(self, image_format: str, **kwargs: Any) -> bytes | None:
    """Helper function for iPython display hook.

    :param image_format: Image format.
    :returns: image as bytes, saved into the given format.
    """
    b = io.BytesIO()
    try:
        original_save(self, b, image_format, **kwargs)
    except Exception:
        return None
    return b.getvalue()


Image._repr_image = __repr_image


def save(image, fp, format=None, **options):
    display(image)
    original_save(image, fp, format, **options)


Image.save = save
