import subprocess
import tempfile
import sys
import os
from b2sdk.v2 import InMemoryAccountInfo
from b2sdk.v2 import B2Api


info = InMemoryAccountInfo()  # store credentials, tokens and cache in memory
b2_api = B2Api(info)
application_key_id = os.environ["B2_APPLICATION_KEY_ID"]
application_key = os.environ["B2_APPLICATION_KEY"]
b2_api.authorize_account("production", application_key_id, application_key)

BUCKET_PREFIX = os.environ["BUCKET_URL"]
nino_public = b2_api.get_bucket_by_name(os.environ["BUCKET_NAME"])


def scale_image(path):
    try:
        subprocess.run(["convert", path, "-resize", "800x800>", path], check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Image scaling failed: {e}")
    except FileNotFoundError:
        raise RuntimeError("ImageMagick not found.")


def optimise_images(paths):
    """Optimise multiple images with ImageOptim"""

    if not paths:
        raise ValueError()

    imageoptim = "/Applications/ImageOptim.app/Contents/MacOS/ImageOptim"

    try:
        subprocess.run([imageoptim, *paths], check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ImageOptim optimisation failed: {e}")
    except FileNotFoundError:
        raise RuntimeError("ImageOptim not found.")


def process_file(path, alt_text):
    """
    Given a file path:
    - Copy the file to two tmp files.
    - Resize one of them to a smaller resolution with scale_image.
    - Run ImageOptim on both of them with optimise_images.
    - Upload both of them to B2.
    - Return an HTML snippet.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    filename = os.path.basename(path)
    name, ext = os.path.splitext(filename)

    with tempfile.NamedTemporaryFile(
        suffix=ext, delete=False
    ) as full_tmp, tempfile.NamedTemporaryFile(suffix=ext, delete=False) as thumb_tmp:
        with open(path, "rb") as src:
            data = src.read()
            full_tmp.write(data)
            thumb_tmp.write(data)

        full_path = full_tmp.name
        thumb_path = thumb_tmp.name

    try:
        scale_image(thumb_path)
        optimise_images([full_path, thumb_path])

        full_name = f"{name}_full{ext}"
        thumb_name = f"{name}_thumb{ext}"

        with open(full_path, "rb") as full_file, open(thumb_path, "rb") as thumb_file:
            print("uploading now…")
            full_upload = nino_public.upload_bytes(
                full_file.read(), f"images/{full_name}"
            )
            thumb_upload = nino_public.upload_bytes(
                thumb_file.read(), f"images/{thumb_name}"
            )

        html = f'<a href="{BUCKET_PREFIX}{full_upload.file_name}"><img src="{BUCKET_PREFIX}{thumb_upload.file_name}" alt="{alt_text}"></a>'
        subprocess.run(["pbcopy"], input=html.encode(), check=True)

        return html

    finally:
        os.unlink(full_path)
        os.unlink(thumb_path)


if __name__ == "__main__":
    file_path = sys.argv[1]
    alt_text = sys.argv[2]
    if not file_path:
        print("No file path provided.")

    print(process_file(file_path, alt_text))
