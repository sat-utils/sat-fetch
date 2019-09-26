import os
import os.path as op

from satsearch import config
from satfetch import fetch, open_image
from satstac import ItemCollection
from unittest import TestCase

testpath = op.dirname(__file__)


class Test(TestCase):
    """ Test main module """

    def get_items(self):
        return ItemCollection.load(op.join(testpath, 'items-landsat.geojson'))

    def test_open_image(self):
        item = self.get_items()[0]
        geoimg = open_image(item, keys=['red'])
        assert(geoimg.nbands() == 1)
        assert(geoimg.xsize() == 7701)

    def test_fetch(self):
        items = self.get_items()
        bands = ['BQA']
        config.DATADIR = ''
        config.FILENAME = os.path.join(testpath, 'test_fetch/${collection}_${date}')
        new_items = fetch(items, items._search.get('parameters', {}).get('intersects', {}), bands)

