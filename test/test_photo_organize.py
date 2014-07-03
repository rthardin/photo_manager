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
            assert metadata, \
                'get_metadata() should return non-None, non-empty'
            keys = [data.key for data in metadata]
            assert len(keys) > 0, \
                'get_metadata() returned an object with no keys'

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
            assert isinstance(dt, datetime), \
                'get_datetime() should return a datetime, not %s' % type(dt)

    def test_organize_photos(self):
        # Define and create the input and output directories
        output_dir = os.path.join(self.test_dir, 'output')
        os.mkdir(output_dir)
        # Organize the photos
        moved_files = [moved_file for moved_file in
                       photo_organize.organize(photo_directory, output_dir, copy=True)]
        for moved_file in moved_files:
            print moved_file
        # Verify some shit
        assert len(moved_files) == 6, \
            'Should have moved 6 files'
        for moved_file in moved_files:
            assert output_dir in moved_file['destination'], \
                'File got moved to the wrong place'

if __name__ == '__main__':
    unittest.main()