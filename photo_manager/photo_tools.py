import os
import exifread
from datetime import datetime


def get_metadata(path):
    # Open the image and retrieve all of the metadata
    with open(path, 'rb') as img_file:
        return exifread.process_file(img_file)


def get_datetime(path):
    # Name of the EXIF tag that contains the photo datetime
    datetime_tag = 'EXIF DateTimeOriginal'
    # Open the image and retrieve the metadata
    with open(path, 'rb') as img_file:
        metadata = exifread.process_file(img_file, details=False, stop_tag=datetime_tag)
    # Get the datetime string
    if not metadata.get(datetime_tag):
        return None
    # Convert the datetime str into a datetime
    return datetime.strptime(str(metadata.get(datetime_tag)), '%Y:%m:%d %H:%M:%S')
