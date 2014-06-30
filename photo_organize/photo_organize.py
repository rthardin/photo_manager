import hashlib
import shutil
import errno
import os
import exifread
from datetime import datetime


def read_in_chunks(path, chunk_size=1048576):
    with open(path, 'rb') as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data


def file_sha1(path):
    sha1 = hashlib.sha1()
    sha1.update('blob %s\0' % os.path.getsize(path))
    for chunk in read_in_chunks(path):
        sha1.update(chunk)
    return sha1.hexdigest()


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
            # Get the extension
            extension = os.path.splitext(filename)[1].lower()
            filepath = os.path.join(dirpath, filename)
            try:
                # Get the EXIF datetime
                dt = get_datetime(filepath)
                # Determine the destination directory
                output_dirs = os.path.join(output_root, str(dt.year), str(dt.month))
                # Create a destination file name based on the date and the file's SHA
                destination_name = '%s_%s%s' % (dt.isoformat(), file_sha1(filepath), extension)
                destination_path = os.path.join(output_dirs, destination_name)
                # Check if the destination file already exists, and if it does, skip it
                if os.path.isfile(destination_path):
                    # Logging would be nice
                    continue
                # Create the destination directory, if it does not already exist
                try:
                    os.makedirs(output_dirs)
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        raise e
                # Move the image to the destination
                shutil.move(filepath, destination_path)
                # Append the paths to the list of moved files
                moved_files.append({'source': filepath,
                                    'destination': destination_path})
            # If it's not an image, or does not contain EXIF metadata, skip it
            except ValueError:
                continue
            except Exception as e:
                # Logging would be nice
                continue
    return moved_files
