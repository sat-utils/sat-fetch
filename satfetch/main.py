#!/usr/bin/env python

import os
import sys
import argparse
import logging
from .version import __version__

import gippy
import gippy.algorithms as algs
from satsearch.scene import Scenes

logger = logging.getLogger(__name__)


_def = {
    'datadir': './',
}


def parse_args(args):
    desc = 'sat-fetch (v%s)' % __version__
    dhf = argparse.ArgumentDefaultsHelpFormatter
    parser0 = argparse.ArgumentParser(description=desc, formatter_class=dhf)

    parser0.add_argument('--version', help='Print version and exit', action='version', version=__version__)
    parser0.add_argument('--log', default=2, type=int,
                         help='0:all, 1:debug, 2:info, 3:warning, 4:error, 5:critical')

    parser0.add_argument('scenes', help='Filename of scenes metadata')
    parser0.add_argument('aoi', help='Filename of AOI (GeoJSON)')
    parser0.add_argument('--datadir', help='Local directory to save scenes to', default=_def['datadir'])
    parser0.add_argument('--bands', help='Bands to fetch', nargs='+', default=None)
    #parser0.add_argument('--separate', help='Do not combine bands into files', action='store_true', default=False)

    # turn Namespace into dictionary
    parsed_args = vars(parser0.parse_args(args))

    return parsed_args


def main(scenes, aoi, datadir='./', bands=None):
    scenes = Scenes.load(scenes)

    print(scenes.text_calendar())

    bname = os.path.splitext(os.path.basename(aoi))[0]

    features = gippy.GeoVector(aoi)

    if not os.path.exists(datadir):
        os.makedirs(datadir)
    gippy.Options.set_verbose(5)
    #opts = {'COMPRESS': 'DEFLATE', 'PREDICTOR': '2', 'TILED': 'YES', 'BLOCKXSIZE': '512', 'BLOCKYSIZE': '512'}
    #opts = {'COMPRESS': 'LZW', 'TILED': 'YES', 'BLOCKXSIZE': '512', 'BLOCKYSIZE': '512'}
    opts = {'TILED': 'YES', 'BLOCKXSIZE': '512', 'BLOCKYSIZE': '512'}
    for date in scenes.dates():
        _scenes = [s for s in scenes if s.date == date]
        #import pdb; pdb.set_trace()
        geoimgs = []
        for s in _scenes:
            links = s.links()
            if bands is None:
                bands = links.keys()
            filenames = [links[k].replace('https:/', '/vsicurl') for k in sorted(links) if k in bands]
            geoimg = gippy.GeoImage.open(filenames)
            geoimg.set_nodata(0)
            geoimgs.append(geoimg)
        outname = '%s_%s.tif' % (s.date, s.platform)
        fout = os.path.join(datadir, outname)
        
        if not os.path.exists(fout):
            # default to first image res and srs
            res = geoimgs[0].resolution()
            imgout = algs.cookie_cutter(geoimgs, fout, features[0], xres=res.x(), yres=res.y(), proj=geoimgs[0].srs(), options=opts)


def cli():
    args = parse_args(sys.argv[1:])
    logger.setLevel(args.pop('log') * 10)

    main(**args)


if __name__ == "__main__":
    cli()
