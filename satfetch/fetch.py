import json
import logging
import os
import gippy
import gippy.algorithms as algs
from satsearch import Scene

logger = logging.getLogger(__name__)


def fetch(scenes, assets, geovector, basename='image'):
    """ This fetches data from just the AOI and clips it """
    opts = {'COMPRESS': 'DEFLATE', 'PREDICTOR': '2', 'INTERLEAVE': 'BAND',
            'TILED': 'YES', 'BLOCKXSIZE': '512', 'BLOCKYSIZE': '512'}
    path = scenes[0].get_path()
    fname = scenes[0].get_filename()
    # TODO - different paths for sat-fetch ?
    fout = os.path.join(path, fname + '.tif')

    # create derived scene metadata
    derived_scene = Scene.create_derived(scenes)
    derived_scene.feature['geometry'] = json.loads(geovector.json_geometry())
    # add asset(s) to derived scene
    bands = []
    for a in assets:
        bands += scenes[0].asset(a)['eo:bands']
    derived_scene.feature['assets'][basename] = {
        'href': fout,
        'eo:bands': bands
    }

    if os.path.exists(fout):
        return gippy.GeoImage(fout)
    try:
        geoimgs = []
        for s in scenes:
            geoimgs.append(open_image(s, assets))

        # default to first image res and srs
        res = geoimgs[0].resolution()
        imgout = algs.cookie_cutter(geoimgs, fout, geovector, xres=res.x(), yres=res.y(), proj=geoimgs[0].srs(), options=opts)
        logger.info("Created %s" % imgout.filename())
        return derived_scene
    except Exception as err:
        print('Error: ', str(err))


def open_image(scene, keys=None, download=False):
    """ Open these asset keys from scene as a gippy GeoImage """
    if keys is None:
        keys = scene.name_to_band.keys()
    logger.debug('Opening scene %s (%s)' % (scene.id, ','.join(keys)))
    assets = [scene.asset(k) for k in keys]
    filenames = [a['href'].replace('https:/', '/vsicurl/https:/') for a in assets]
    geoimg = gippy.GeoImage.open(filenames, update=False)
    geoimg.set_nodata(0)
    if download:
        # download scenes first
        fnames = scene.download(keys)
        return gippy.GeoImage.open(fnames)
    else:
        return geoimg