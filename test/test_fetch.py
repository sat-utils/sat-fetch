from unittest import TestCase

import os.path as op

from satfetch import fetch, open_image
from satstac import Items
from pdb import set_trace

testpath = op.dirname(__file__)


class Test(TestCase):
    """ Test main module """

    def get_items(self):
        return Items.load(op.join(testpath, 'items-landsat.geojson'))

    def test_open_image(self):
        item = self.get_items()[0]
        geoimg = open_image(item, keys=['red'])
        assert(geoimg.nbands() == 1)
        assert(geoimg.xsize() == 7701)

    def test_fetch(self):
        items = self.get_items()
        
        derived_item = fetch(items)

