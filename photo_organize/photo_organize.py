#!/usr/bin/env python

import argparse
import hashlib
import shutil
import errno
import fcntl
import os
from hachoir_metadata import extractMetadata
from hachoir_core.cmd_line import unicodeFilename
from hachoir_parser import createParser
from hachoir_core.error import HachoirError

# Turn off warnings
import hachoir_core.config
hachoir_core.config.quiet = True

supported_extensions = ['.jpg',
                        '.jpeg',
                        '.mov',
                        '.avi',
                        '.thm']


class BlockLockAndDropIt:
    """
    Context manager for locking a file. Blocks on __enter__ until a
    lock is acquired. Unlocks and closes the file handle on __exit__
    """

    def __init__(self, filepath):
        self.lf = None
        self.filepath = filepath

    # Open the file and acquire the lock
    def __enter__(self):
        # Open the lock file
        self.lf = open(self.filepath, 'w')
        # Attempt to acquire the lock, and raise an IOError if lock fails
        fcntl.lockf(self.lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True

    # Always unlock and close file on clean or unclean exit
    def __exit__(self, *args):
        fcntl.lockf(self.lf, fcntl.LOCK_UN)
        self.lf.close()


def read_in_chunks(path, chunk_size=4194304):
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
    # Create a parser for the file
    parser = createParser(unicodeFilename(path), path)
    if not parser:
        raise ValueError('Unable to parse %r' % path)
    # Read the metadata
    try:
        metadata = extractMetadata(parser)
    except HachoirError as e:
        raise ValueError('Metadata extraction error: %s' % e)
    # Check that there really was metadata
    if not metadata:
        raise ValueError('Unable to extract metadata for %r' % path)
    return metadata


def get_datetime(path):
    # Pull the datetime from the file's metadata, and let exceptions bubble up
    try:
        return get_metadata(path).get('creation_date')
    except ValueError as e:
        raise ValueError('Unable to extract creation date for %r: %s' % (path, e))


def organize(input_root, output_root, copy=False, dry_run=False):
    # Find all the photos in the input_dir
    for dirpath, dirnames, filenames in os.walk(input_root):
        for filename in filenames:
            # Get the extension
            extension = os.path.splitext(filename)[1].lower()
            if extension not in supported_extensions:
                continue
            filepath = os.path.join(dirpath, filename)
            try:
                # Get the EXIF datetime
                dt = get_datetime(filepath)
                # Determine the destination directory
                output_dirs = os.path.join(output_root, '%04d' % dt.year, '%02d' % dt.month)
                # Create a destination file name based on the date and the file's SHA
                destination_name = '%s_%s%s' % (dt.isoformat(), file_sha1(filepath), extension)
                # Check if the destination file already exists, and if it does, move it to the
                # duplicates directory
                destination_path = os.path.join(output_dirs, destination_name)
                if os.path.isfile(destination_path):
                    output_dirs = os.path.join(output_root, 'Duplicates')
                    destination_path = os.path.join(output_dirs, destination_name)
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
    description = 'Find media files in a directory, and organize them by date.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('input_directory', type=str,
                        help='directory to read files from')
    parser.add_argument('output_directory', type=str,
                        help='directory to move or copy files to')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='enable verbose output')
    parser.add_argument('-c', '--copy', action='store_true',
                        help='copy files instead of moving them')
    parser.add_argument('--dry-run', action='store_true',
                        help='dry-run (do not move or copy)')

    args = parser.parse_args()

    if args.dry_run:
        print 'Running in dry-run mode. No files will be moved or copied.\n' \
              'Warning: dry-run mode is unable to check for duplicates.\n'

    moved_files = 0
    verb = 'copied' if args.copy else 'moved'
    try:
        with BlockLockAndDropIt(os.path.join(args.input_directory, '.photo_organize_lock')):
            for moved_file in organize(args.input_directory, args.output_directory,
                                       copy=args.copy, dry_run=args.dry_run):
                if args.verbose:
                    print '%s %r --> %r' % (verb.title(),
                                            moved_file['source'], moved_file['destination'])
                moved_files += 1

            if moved_files:
                print '\nSuccessfully %s %d files into %r' % (verb,
                                                              moved_files, args.output_directory)
    except IOError:
        print '\nAn instance is already running on this directory'