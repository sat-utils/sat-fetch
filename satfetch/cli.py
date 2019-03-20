#!/usr/bin/env python3

import argparse
import json
import logging
import os
import sys
import tempfile
from .version import __version__
import gippy

import satsearch.config as config
from satsearch import Search
from satsearch.main import main as satsearch
from satsearch.parser import SatUtilsParser
from satstac import Collection, Item, Items
from satfetch import fetch as satfetch


logger = logging.getLogger(__name__)


class SatFetchParser(SatUtilsParser):

    def __init__(self, *args, **kwargs):
        # change defaults from sat-search
        # data directory to store downloaded imagery
        config.DATADIR = os.getenv('SATUTILS_DATADIR', './')
        # filename pattern for saving files
        config.FILENAME = os.getenv('SATUTILS_FILENAME', '${collection}_${date}')
        super().__init__(*args, **kwargs)
        self.download_group.add_argument('--fetch', help='Fetch and clip to AOI', default=None, nargs='*')


def main(items=None, fetch=None, save=None, **kwargs):
    """ Main function for performing a search """
    _save = save if items is None else None
    items = satsearch(items, save=_save, **kwargs)
    # if not downloading nothing more to do
    if fetch is None:
        return
    
    # check that there is a valid geometry for clipping
    feature = items._search.get('intersects', None)
    if feature is None:
        raise Exception('No geometry provided')

    # create temporary geometry file
    with tempfile.NamedTemporaryFile(suffix='.geojson', mode='w', delete=False) as f:
        aoiname = f.name
        aoistr = json.dumps(feature)
        f.write(aoistr)
    geovec = gippy.GeoVector(aoiname)

    derived_items = []
    # for each date, combine scenes
    for date in items.dates():
        print('Processing files for %s' % date)
        _items = [s for s in items if s.date == date]
        # TODO - split out by user specified metadata (e.g., platform, collection)
        item = satfetch(_items, geovec[0], keys=fetch)
        derived_items.append(item)
        break

    # this needs update to sat-stac to support adding metadata to Items
    # see https://github.com/sat-utils/sat-stac/issues/39
    #props = {
    #    'software': 'sat-fetch v%s' % __version__
    #}
    
    col = Collection.create()
    col.data['id'] = 'sat-fetch'
    col.data['description'] = 'Fetch items created by sat-fetch'
    col.data['links'].append({'rel': 'about', 'href': 'https://github.com/sat-utils/sat-fetch'})
    derived_items = Items(derived_items, collections=[col])
    if save is not None:
        derived_items.save(save)
    return derived_items


def cli():
    parser = SatFetchParser.newbie(description='sat-fetch (v%s)' % __version__)
    args = parser.parse_args(sys.argv[1:])

    cmd = args.pop('command', None)
    if cmd is not None:
        main(**args)


if __name__ == "__main__":
    cli()
