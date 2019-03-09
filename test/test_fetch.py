from unittest import TestCase

import os.path as op
import satfetch.fetch as fetch

from satsearch import Item


testpath = op.dirname(__file__)


class Test(TestCase):
    """ Test main module """

    def get_item(self):
        return Item.open(op.join(testpath, 'scenes-landsat.geojson'))

    def test_open_image(self):
        item = self.get_item()
        geoimg = fetch.open_image(item)

    def test_fetch(self):
        item = self.get_item()
        derived_item = fetch.fetch(item)

