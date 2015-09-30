#!/usr/bin/env python

import argparse
import hashlib
import logging
from logging.handlers import RotatingFileHandler
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
                        '.thm',
                        '.mp4']


class LockAcquireError(IOError):
    pass


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
        try:
            fcntl.lockf(self.lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError as e:
            raise LockAcquireError(e)
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


def organize(input_root, output_root, copy=False, dry_run=False, delete_duplicates=False):
    # Find all the photos in the input_dir
    for dirpath, dirnames, filenames in os.walk(input_root):
        # Ignore hidden files and directories
        filenames = [f for f in filenames if not f[0] == '.']
        dirnames[:] = [d for d in dirnames if not d[0] == '.']
        for filename in filenames:
            # Get the extension
            filepath = os.path.join(dirpath, filename)
            logging.debug('Examining "%s"', filepath)
            extension = os.path.splitext(filepath)[1].lower()
            if extension not in supported_extensions:
                logging.info('Skipping "%s": Unsupported extension "%s"' % (filepath, extension))
                continue
            # Outer try/catch block to catch any unexpected stuff
            try:
                try:
                    # Get the EXIF datetime
                    dt = get_datetime(filepath)
                # It's not an image, or does not contain EXIF metadata
                except ValueError:
                    logging.warning('Unable to retrieve metadata for "%s"' % filepath)
                    dt = None
                # Calculate the sha1 of the file
                sha_str = file_sha1(filepath)
                # Determine the destination directory
                if dt is not None:
                    output_dirs = os.path.join(output_root, '%04d' % dt.year, '%02d' % dt.month)
                    # Create a destination file name based on the date and the file's SHA
                    destination_name = '%s_%s%s' % (dt.isoformat(), sha_str, extension)
                    destination_path = os.path.join(output_dirs, destination_name)
                else:
                    output_dirs = os.path.join(output_root, 'no_metadata')
                    # Create a destination file name based on the date and the file's SHA
                    destination_name = '%s%s' % (sha_str, extension)
                    destination_path = os.path.join(output_dirs, destination_name)
                # Check if the destination file already exists
                if os.path.isfile(destination_path) and file_sha1(destination_path) == sha_str:
                    # Duplicates can be deleted
                    if delete_duplicates:
                        logging.info('Deleting "%s": Duplicate of "%s"' % (filepath, destination_path))
                        if not dry_run:
                            try:
                                os.remove(filepath)
                            except:
                                logging.exception('Failed to delete "%s"' % filepath)
                        continue
                # Create the destination directory, if it does not already exist
                if not dry_run:
                    try:
                        os.makedirs(output_dirs)
                        logging.debug('Created "%s"', output_dirs)
                    except OSError as e:
                        if e.errno != errno.EEXIST:
                            raise e
                # Move or copy the image to the destination
                if copy:
                    logging.info('Copying "%s" to "%s"', filepath, destination_path)
                    if not dry_run:
                        shutil.copy(filepath, destination_path)
                else:
                    logging.info('Moving "%s" to "%s"', filepath, destination_path)
                    if not dry_run:
                        shutil.move(filepath, destination_path)
                # Append the paths to the list of moved files
                yield {'source': filepath,
                       'destination': destination_path}
            except Exception:
                logging.exception('Exploded working on "%s"' % filepath)
                continue
        # Cleanup - if the directory or any ancestors are empty, delete them
        path = dirpath
        while path != input_root:
            # Either remove the directory, or exit the loop
            try:
                if not dry_run:
                    os.rmdir(path)
                    logging.info('Removed empty directory "%s"' % path)
            except OSError as e:
                if e.errno != errno.ENOTEMPTY:
                    logging.exception('Failed to delete directory "%s"' % path)
                break
            # Move up to the parent
            path = os.path.split(path)[0]



if __name__ == "__main__":
    # Do parsing
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
    parser.add_argument('--delete-duplicates', action='store_true',
                        help='delete duplicate images')
    parser.add_argument('--dry-run', action='store_true',
                        help='dry-run (do not move or copy)')

    args = parser.parse_args()
    # Set up the logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    fh = RotatingFileHandler(os.path.join(args.input_directory, '.photo_organize.log'),
                             maxBytes=250 * 1024,  # 250KB
                             backupCount=3)
    formatter = logging.Formatter('%(asctime)s : %(process)5d : %(levelname)7s : %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    if args.dry_run:
        logging.info('Running in dry-run mode. No files will be moved or copied')
        logging.warning('dry-run mode is unable to check for duplicates')

    try:
        lock_path = os.path.join('/', 'tmp', args.input_directory.replace(os.sep, '_') + '.photo_organize_lock')
        with BlockLockAndDropIt(lock_path):
            for processed_file in organize(args.input_directory,
                                           args.output_directory,
                                           copy=args.copy,
                                           dry_run=args.dry_run,
                                           delete_duplicates=args.delete_duplicates):
                pass
    except LockAcquireError:
        logging.debug('An instance is already running on this directory')
    except:
        logging.exception()
