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
from satsearch import Search, Scene, Scenes
from satsearch.main import main as satsearch
from satsearch.parser import SatUtilsParser
from satfetch import fetch


logger = logging.getLogger(__name__)


class SatFetchParser(SatUtilsParser):

    def __init__(self, *args, **kwargs):
        # change defaults from sat-search
        # data directory to store downloaded imagery
        config.DATADIR = os.getenv('SATUTILS_DATADIR', './')
        # filename pattern for saving files
        config.FILENAME = os.getenv('SATUTILS_FILENAME', '${date}_${c:id}')
        super().__init__(*args, **kwargs)
        self.download_group.add_argument('--fetch', help='Fetch and clip to AOI', default=None, nargs='*')
        self.download_group.add_argument('--separate', help='Do not combine bands into files', action='store_true', default=False)


def main(items=None, fetch=None, save=None, **kwargs):
    """ Main function for performing a search """
    items = satsearch(items, **kwargs)

    # if not downloading nothing more to do
    if fetch is None:
        return

    # check that there is a valid geometry for clipping
    feature = items.properties.get('intersects', {})
    if not feature:
        raise Exception('No geometry provided')
    with tempfile.NamedTemporaryFile(suffix='.geojson', mode='w', delete=False) as f:
        aoiname = f.name
        aoistr = json.dumps(feature)
        f.write(aoistr)
    geovec = gippy.GeoVector(aoiname)

    derived_scenes = []
    # for each date, combine scenes
    for date in items.dates():
        print('Processing files for %s' % date)
        _items = [s for s in items if s.date == date]
        # TODO - split out by user specified metadata (e.g., platform, collection)
        item = fetch(_items, fetch, geovec[0])
        derived_scenes.append(item)

    props = {
        'software': 'sat-fetch v%s' % __version__
    }
    derived_scenes = Scenes(derived_scenes, props)
    if save is not None:
        derived_scenes.save(save)
    return derived_scenes


def cli():
    parser = SatFetchParser.newbie(description='sat-fetch (v%s)' % __version__)
    args = parser.parse_args(sys.argv[1:])

    cmd = args.pop('command', None)
    if cmd is not None:
        main(**args)


if __name__ == "__main__":
    cli()
