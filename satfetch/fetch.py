import json
import logging
import os
import gippy
import gippy.algorithms as algs

from satstac import Item
from satsearch import config

logger = logging.getLogger(__name__)


OPTS = {'COMPRESS': 'DEFLATE', 'PREDICTOR': '2', 'INTERLEAVE': 'BAND',
        'TILED': 'YES', 'BLOCKXSIZE': '512', 'BLOCKYSIZE': '512'}


def create_derived_item(items, geovector):
    """ Create metadata for dervied scene from multiple input scenes """
    # data provenance, iterate through links
    links = []
    for i in items:
        selflink = [l['href'] for l in i.data['links'] if i['rel'] == 'self']
        if len(selflink) > 0:
            links.append({
                'rel': 'derived_from',
                'href': selflink[0]
            })
    # calculate composite geometry and bbox
    geom = json.loads(geovector.json_geometry())
    lons = [c[0] for c in geom['coordinates'][0]]
    lats = [c[1] for c in geom['coordinates'][0]]
    bbox = [min(lons), min(lats), max(lons), max(lats)]
    # properties
    props = {
        'collection': 'sat-fetch',
        'datetime': items[0]['datetime']
    }
    collections = [item['collection'] for item in items if item['collection'] is not None]
    if len(collections) == 1:
        props['collection'] = collections[0]
    item = {
        'type': 'Feature',
        'id': '%s_%s' % (items[0]['eo:platform'], items[0].date),
        'bbox': bbox,
        'geometry': geom,
        'properties': props,
        'links': links,
        'assets': {}
    }
    return Item(item)


def fetch(items, geovector, keys=None, proj=None, res=None):
    """ This fetches data from just the AOI and clips it """
    derived_item = create_derived_item(items, geovector)

    bands = []
    for k in keys:
        bands += items[0].asset(k)['eo:bands']
    filename = items[0].get_filename(path=config.DATADIR, filename=config.FILENAME).replace('.json','.tif')
    derived_item.data['assets'] = {
        'image': {
            'type': 'image/vnd.stac.geotiff; cloud-optimized=true',
            'title': 'Clipped image',
            'href': filename,
            'eo:bands': bands
        }
    }

    if os.path.exists(filename):
        return derived_item
    try:
        geoimgs = []
        for item in items:
            geoimgs.append(open_image(item, keys))

        # default to first image res and srs
        if res is None:
            res = geoimgs[0].resolution()
            res = [res.x(), res.y()]
        elif len(res) == 1:
            res = [res[0], res[0]]
        if proj is None:
            proj = geoimgs[0].srs()
        imgout = algs.cookie_cutter(geoimgs, filename, geovector, xres=res[0], yres=res[1], 
                                    proj=proj, options=OPTS)
        logger.info("Created %s" % imgout.filename())
        return derived_item
    except Exception as err:
        print('Error: ', str(err))


def open_image(item, keys=None, nodata=0, download=False):
    """ Open these asset keys from scene as a gippy GeoImage """
    if keys is None:
        keys = item.assets.keys()
    logger.debug('Opening item %s (%s)' % (item.id, ','.join(keys)))
    assets = [item.asset(k) for k in keys]
    filenames = []
    for a in assets:
        url = a['href']
        if 's3.amazonaws.com' in a['href']:
            for v in ['https://', 'http://']:
                url = url.replace(v, '')
            parts = url.split('/')
            bucket = parts[0].replace('.s3.amazonaws.com', '')
            key = '/'.join(parts[1:])
            filenames.append('/vsis3/%s/%s' % (bucket, key))
        else:
            filenames.append(url.replace('https:/', '/vsicurl/https:/'))
    if download:
        # download items first
        fnames = item.download(keys)
        geoimg = gippy.GeoImage.open(fnames)
    else:
        geoimg = gippy.GeoImage.open(filenames, update=False)
    geoimg.set_bandnames(keys)
    geoimg.set_nodata(nodata)
    return geoimg