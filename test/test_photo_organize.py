import logging
import shutil
import unittest

import os
from datetime import datetime
from photo_organize import photo_organize


photo_directory = './resource/images'
valid_photo_directory = './resource/images/valid'


class TestPhotoOrganize(unittest.TestCase):

    def setUp(self):
        # Test directory
        self.test_dir = self.__class__.__name__
        # Delete the test directory if it exists
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass
        # Create the test directory
        os.mkdir(self.test_dir)
        # Set logging to debug
        logging.getLogger().setLevel(logging.INFO)

    def tearDown(self):
        # Delete the test directory if it exists
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass

    def test_get_metadata(self):
        # What happens if a non-photo is attempted?
        with self.assertRaises(ValueError):
            photo_organize.get_metadata('test_photo_organize.py')
        # Get a list of photos
        photo_filenames = os.listdir(valid_photo_directory)
        # Iterate over each, and check for metadata
        for photo_filename in photo_filenames:
            photo_path = os.path.join(valid_photo_directory, photo_filename)
            metadata = photo_organize.get_metadata(photo_path)
            self.assertIsNotNone(metadata)
            keys = [data.key for data in metadata]
            self.assertGreater(len(keys), 0)

    def test_get_datetime(self):
        # What happens if a non-photo is attempted?
        with self.assertRaises(ValueError):
            photo_organize.get_datetime('test_photo_organize.py')
        # Get a list of photos
        photo_filenames = os.listdir(valid_photo_directory)
        # Iterate over each, and check for a correct datetime
        for photo_filename in photo_filenames:
            photo_path = os.path.join(valid_photo_directory, photo_filename)
            dt = photo_organize.get_datetime(photo_path)
            self.assertIsInstance(dt, datetime)

    def test_organize_photos(self):
        # Define and create the input and output directories
        output_dir = os.path.join(self.test_dir, 'output')
        os.mkdir(output_dir)
        # Organize the photos
        moved_files = [moved_file for moved_file in
                       photo_organize.organize(photo_directory, output_dir, copy=True)]
        # Verify some shit
        self.assertEqual(len(moved_files), 11)
        for moved_file in moved_files:
            self.assertIn(output_dir, moved_file['destination'],
                          'File got moved to the wrong place')

if __name__ == '__main__':
    unittest.main()