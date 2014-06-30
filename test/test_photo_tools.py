import shutil
import unittest

import os
from datetime import datetime
from photo_manager import photo_tools


photo_directory = './resource/images'
valid_photo_directory = './resource/images/valid'


class TestPhotoTools(unittest.TestCase):

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

    def tearDown(self):
        # Delete the test directory if it exists
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass

    def test_get_metadata(self):
        # What happens if a non-photo is attempted?
        with self.assertRaises(ValueError):
            photo_tools.get_metadata('test_photo_tools.py')
        # Get a list of photos
        photo_filenames = os.listdir(valid_photo_directory)
        # Iterate over each, and check for metadata
        for photo_filename in photo_filenames:
            photo_path = os.path.join(valid_photo_directory, photo_filename)
            metadata = photo_tools.get_metadata(photo_path)
            assert metadata, \
                'get_metadata() should return a dict, not %s ' % type(metadata)
            assert len(metadata.keys()) > 0, \
                'get_metadata() returned a dict with no keys'

    def test_get_datetime(self):
        # What happens if a non-photo is attempted?
        with self.assertRaises(ValueError):
            photo_tools.get_datetime('test_photo_tools.py')
        # Get a list of photos
        photo_filenames = os.listdir(valid_photo_directory)
        # Iterate over each, and check for a correct datetime
        for photo_filename in photo_filenames:
            photo_path = os.path.join(valid_photo_directory, photo_filename)
            dt = photo_tools.get_datetime(photo_path)
            assert isinstance(dt, datetime), \
                'get_datetime() should return a datetime, not %s' % type(dt)

    def test_organize_photos(self):
        # Define and create the input and output directories
        input_dir = os.path.join(self.test_dir, 'input')
        output_dir = os.path.join(self.test_dir, 'output')
        os.mkdir(input_dir)
        os.mkdir(output_dir)
        # Copy the test photos to the input directory
        dirname = os.path.split(photo_directory)[1]
        shutil.copytree(photo_directory, os.path.join(input_dir, dirname))
        # Organize the photos
        for moved_file in photo_tools.organize(input_dir, output_dir):
            print moved_file

if __name__ == '__main__':
    unittest.main()