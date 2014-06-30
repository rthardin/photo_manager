import unittest

import os
from datetime import datetime
from photo_manager import photo_tools


photo_directory = './resource/images'


class TestPhotoTools(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_metadata(self):
        # Get a list of photos
        photo_filenames = os.listdir(photo_directory)
        # Iterate over each, and check for metadata
        for photo_filename in photo_filenames:
            photo_path = os.path.join(photo_directory, photo_filename)
            metadata = photo_tools.get_metadata(photo_path)
            assert metadata, \
                'get_metadata() should return a dict, not %s ' % type(metadata)
            assert len(metadata.keys()) > 0, \
                'get_metadata() returned a dict with no keys'

    def test_get_datetime(self):
        # Get a list of photos
        photo_filenames = os.listdir(photo_directory)
        # Iterate over each, and check for a correct datetime
        for photo_filename in photo_filenames:
            photo_path = os.path.join(photo_directory, photo_filename)
            dt = photo_tools.get_datetime(photo_path)
            assert isinstance(dt, datetime), \
                'get_datetime() should return a datetime, not %s' % type(dt)

if __name__ == '__main__':
    unittest.main()