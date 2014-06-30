import shutil
import errno
import os
import exifread
from datetime import datetime


def get_metadata(path):
    # Open the image and retrieve all of the metadata
    with open(path, 'rb') as img_file:
        metadata = exifread.process_file(img_file)
    # If it doesn't contain metadata, raise an Exception
    if not metadata:
        raise ValueError('%r is not an image, or does not contain EXIF metadata' % path)
    return metadata


def get_datetime(path):
    # Name of the EXIF tag that contains the photo datetime
    datetime_tag = 'EXIF DateTimeOriginal'
    # Open the image and retrieve the metadata
    with open(path, 'rb') as img_file:
        metadata = exifread.process_file(img_file, details=False, stop_tag=datetime_tag)
    # Get the datetime string
    if not metadata.get(datetime_tag):
        raise ValueError('%r is not an image, or does not contain EXIF metadata' % path)
    # Convert the datetime str into a datetime
    return datetime.strptime(str(metadata.get(datetime_tag)), '%Y:%m:%d %H:%M:%S')


def organize(input_root, output_root):
    moved_files = []
    # Find all the photos in the input_dir
    for dirpath, dirnames, filenames in os.walk(input_root):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                # Get the EXIF datetime
                dt = get_datetime(filepath)
                # Create the destination directory, if it does not exist
                output_dirs = os.path.join(output_root, str(dt.year), str(dt.month))
                try:
                    os.makedirs(output_dirs)
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        raise e
                # Move the image to the destination
                destination_path = os.path.join(output_dirs, filename)
                shutil.move(filepath, destination_path)
                # Append the paths to the list of moved files
                moved_files.append({'source': filepath,
                                    'destination': destination_path})
            # If it's not an image, or does not contain EXIF metadata, skip it
            except ValueError:
                continue
    return moved_files
