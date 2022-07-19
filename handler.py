import os

from PIL import Image
import uuid
import urllib.parse
import boto3

s3_client = boto3.client("s3")


def webp_handler(event, context):
    # get environment variables
    webp_directory = os.environ.get("WEBP_DIRECTORY_NAME")
    webp_directory = "webp/" if webp_directory is None else webp_directory
    is_delete_original = os.environ.get("IS_DELETE_ORIGINAL")
    is_delete_original = True if is_delete_original else False

    # get s3 information from event
    s3_event = event["Records"][0]["s3"]
    bucket = s3_event["bucket"]["name"]
    key = urllib.parse.unquote_plus(s3_event["object"]["key"], encoding="utf-8")

    try:
        tmp_key = key.replace("/", "")
        download_path = "/tmp/{}{}".format(uuid.uuid4(), tmp_key)
        s3_client.download_file(bucket, key, download_path)

        converted_image = convert_save_image(download_path)
        converted_image_key = webp_directory + convert_to_webp_filename(key)
        s3_client.upload_file(converted_image, bucket, converted_image_key)
        print("converted_image_key: {}".format(converted_image_key))

        if is_delete_original:
            print("original image {} is deleted".format(key))
            s3_client.delete_object(Bucket=bucket, Key=key)

    except Exception as e:
        print("Error", e)
        print(f"Error object {key} from bucket {bucket}.")
        raise e


class ImageTypeError(Exception):
    pass


def split_image_extension_name(image_path):
    image_split = image_path.split(".")
    return image_split[0], image_split[1]


def convert_save_image(image_path):
    image = Image.open(image_path)
    image = image.convert("RGB")
    webp_image_path = convert_to_webp_filename(image_path)
    image.save(webp_image_path, "webp")
    return webp_image_path


def convert_to_webp_filename(image_path):
    image_name, image_extension = split_image_extension_name(image_path)
    if image_extension in ["jpg", "png", "jpeg", "JPG", "PNG", "JPEG"]:
        return "{}.webp".format(image_name)
    else:
        raise ImageTypeError("Not supported image extension {}".format(image_extension))
