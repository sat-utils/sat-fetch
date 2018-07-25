#!/usr/bin/env python3

import argparse
import json
import logging
import os
import sys
import tempfile
from .version import __version__

from osgeo import gdal
import gippy
import gippy.algorithms as algs
import satsearch.config as config
from satsearch import Search, Scenes
from satsearch.parser import SatUtilsParser
from satsearch.scene import Scenes

logger = logging.getLogger(__name__)

from pdb import set_trace

class SatFetchParser(SatUtilsParser):

    def __init__(self, *args, **kwargs):
        # change defaults from sat-search
        # data directory to store downloaded imagery
        config.DATADIR = os.getenv('SATUTILS_DATADIR', './')
        # filename pattern for saving files
        config.FILENAME = os.getenv('SATUTILS_FILENAME', '${date}_${c:id}')
        super().__init__(*args, **kwargs)
        self.download_group.add_argument('--separate', help='Do not combine bands into files', action='store_true', default=False)


def derived_stac_item(items):
    """ Create a derived STAC item from these """
    # data provenance, iterate through links
    links = {'parent-%s' % i: i['link']['self'] for i, item in enumerate(items)}
    # calculate composite geometry and bbox
    # properties
    props = items[0]['properties']
    props = {
        'id': '--'.join([i['properties'] for i in items]),
        'datetime': items[0]['properties']['datetime'],
    }
    item = {
        'properties': props,
        'bbox': bbox,
        'geometry': geom,
        'links': links,
        'assets': {}
    }
    return item


def main(scenes=None, review=False, print_md=None, print_cal=False,
         save=None, append=False, download=None, **kwargs):
    """ Main function for performing a search """
    if scenes is None:
        # get scenes from search
        search = Search(**kwargs)
        scenes = Scenes(search.scenes(), properties=kwargs)
    else:
        scenes = Scenes.load(scenes)

    # print metadata
    if print_md is not None:
        scenes.print_scenes(print_md)

    # print calendar
    if print_cal:
        print(scenes.text_calendar())

    # save all metadata in JSON file
    if save is not None:
        scenes.save(filename=save, append=append)

    print('%s scenes found' % len(scenes))

    # download files given keys
    if download is None:
        return

    feature = scenes.properties.get('intersects', {})
    if not feature:
        raise Exception('No geometry provided')
    with tempfile.NamedTemporaryFile(suffix='.geojson', mode='w', delete=False) as f:
        aoiname = f.name
        aoistr = json.dumps(feature)
        f.write(aoistr)
    from pdb import set_trace
    geovec = gippy.GeoVector(aoiname)

    #opts = {'COMPRESS': 'DEFLATE', 'PREDICTOR': '2', 'TILED': 'YES', 'BLOCKXSIZE': '512', 'BLOCKYSIZE': '512'}
    #opts = {'COMPRESS': 'LZW', 'TILED': 'YES', 'BLOCKXSIZE': '512', 'BLOCKYSIZE': '512'}
    opts = {'TILED': 'YES', 'BLOCKXSIZE': '512', 'BLOCKYSIZE': '512'}
    for date in scenes.dates()[0:1]:
        _scenes = [s for s in scenes if s.date == date]
        # TODO - seperate out by platform

        path = _scenes[0].get_path()
        fname = _scenes[0].get_filename()
        # TODO - do not hardcode tif 
        fout = os.path.join(path, fname + '.tif')
        gippy.Options.set_verbose(5)
        if not os.path.exists(fout):
            try:
                with tempfile.TemporaryDirectory() as outdir:
                    geoimgs = []
                    for s in _scenes:
                        geoimgs.append(make_vrt(s, download, outdir='./'))
                        #geoimgs.append(open_image(s, download))

                    # default to first image res and srs
                    res = geoimgs[0].resolution()
                    imgout = algs.cookie_cutter(geoimgs, fout, geovec[0], xres=res.x(), yres=res.y(), proj=geoimgs[0].srs(), options=opts)
                    print(imgout.info())
            except Exception as err:
                print('Error: ', str(err))


def open_image(scene, keys=None, download=False):
    print('opening image')
    if keys is None:
        keys = scene.name_to_band.keys()
    assets = [scene.asset(k) for k in keys]
    filenames = [a['href'] for a in assets]
    geoimg = gippy.GeoImage.open(filenames)
    if download:
        geoimg = geoimg.save('test.tif')
        geoimg = None
        return gippy.GeoImage('test.tif')
    else:
        return geoimg


def make_vrt(scene, keys=None, outdir='./'):
    """ Build a VRT from these assets """
    if keys is None:
        keys = scene.name_to_band.keys()
    assets = [scene.asset(k) for k in keys]
    filenames = [a['href'] for a in assets]
    fout = os.path.join(outdir, scene.id + '.vrt')
    gdal.BuildVRT(fout, filenames, separate=True, srcNodata=0)
    geoimg = gippy.GeoImage(fout)
    return geoimg


def cli():
    parser = SatFetchParser.newbie(description='sat-fetch (v%s)' % __version__)
    args = parser.parse_args(sys.argv[1:])

    cmd = args.pop('command', None)
    if cmd is not None:
        main(**args)


if __name__ == "__main__":
    cli()
