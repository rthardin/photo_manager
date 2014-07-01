#!/usr/bin/env python

import argparse
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


def organize(input_root, output_root, copy=False, dry_run=False):
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
                output_dirs = os.path.join(output_root, '%04d' % dt.year, '%02d' % dt.month)
                # Create a destination file name based on the date and the file's SHA
                destination_name = '%s_%s%s' % (dt.isoformat(), file_sha1(filepath), extension)
                destination_path = os.path.join(output_dirs, destination_name)
                # Check if the destination file already exists, and if it does, skip it
                if os.path.isfile(destination_path):
                    # Logging would be nice
                    continue
                if not dry_run:
                    # Create the destination directory, if it does not already exist
                    try:
                        os.makedirs(output_dirs)
                    except OSError as e:
                        if e.errno != errno.EEXIST:
                            raise e
                    # Move or copy the image to the destination
                    if copy:
                        shutil.copy(filepath, destination_path)
                    else:
                        shutil.move(filepath, destination_path)
                # Append the paths to the list of moved files
                yield {'source': filepath,
                       'destination': destination_path}
            # If it's not an image, or does not contain EXIF metadata, skip it
            except ValueError:
                continue
            except Exception as e:
                # Logging would be nice
                continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Organize photos')
    parser.add_argument('input_directory', type=str,
                        help='directory to read files from')
    parser.add_argument('output_directory', type=str,
                        help='directory to move or copy files to')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='enable verbose output')
    parser.add_argument('-c', '--copy', action='store_true',
                        help='copy files instead of moving them')
    parser.add_argument('--dry-run', action='store_true',
                        help='dry-run (do not perform move or copy)')

    args = parser.parse_args()

    if args.dry_run:
        print 'Running in dry-run mode. No files will be moved or copied. Warning: dry-run mode ' \
              'is unable to check for duplicates.\n'

    moved_files = 0
    verb = 'Copied' if args.copy else 'Moved'
    for moved_file in organize(args.input_directory, args.output_directory,
                               copy=args.copy, dry_run=args.dry_run):
        if args.verbose:
            print '%s %r --> %r' % (verb, moved_file['source'], moved_file['destination'])
        moved_files += 1

    print '\nSuccessfully %s %d files into %r' % (verb.lower(), moved_files, args.output_directory)