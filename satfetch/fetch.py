import json
import logging
import os
import tempfile

from gippy import GeoImage, GeoVector, algorithms as algs
from satstac import Item
from satsearch import config

logger = logging.getLogger(__name__)


OPTS = {'COMPRESS': 'DEFLATE', 'PREDICTOR': '2', 'INTERLEAVE': 'BAND',
        'TILED': 'YES', 'BLOCKXSIZE': '512', 'BLOCKYSIZE': '512'}


def open_image(item, keys=None, nodata=0, download=False):
    """ Open these asset keys from scene as a gippy GeoImage """
    if keys is None:
        keys = item.assets.keys()
    logger.debug('Opening item %s (%s)' % (item.id, ','.join(keys)))
    if download:
        # download items first
        fnames = item.download(keys)
        geoimg = GeoImage.open(fnames)
    else:
        # use GDAL vsi curl driver
        filenames = [item.asset(k)['href'].replace('https:/', '/vsicurl/https:/') for k in keys]
        geoimg = GeoImage.open(filenames, update=False)
    geoimg.set_bandnames(keys)
    geoimg.set_nodata(nodata)
    return geoimg


def geometry_to_GeoVector(geometry):
    # create temporary geometry file
    with tempfile.NamedTemporaryFile(suffix='.geojson', mode='w', delete=False) as f:
        feature = {
            "type": "Feature",
            "geometry": geometry
        }
        fname = f.name
        f.write(json.dumps(feature))
    return GeoVector(fname)


def create_derived_item(items, geometry):
    """ Create metadata for dervied scene from multiple input scenes """
    # data provenance, iterate through links
    links = []
    for i in items:
        selflink = [l['href'] for l in i._data['links'] if i['rel'] == 'self']
        if len(selflink) > 0:
            links.append({
                'rel': 'derived_from',
                'href': selflink[0]
            })
    print(geometry)
    lons = [c[0] for c in geometry['coordinates'][0]]
    lats = [c[1] for c in geometry['coordinates'][0]]
    bbox = [min(lons), min(lats), max(lons), max(lats)]
    # properties
    props = {
        'datetime': items[0]['datetime']
    }
    collections = [item['collection'] for item in items if item['collection'] is not None]
    if len(collections) == 1:
        props['collection'] = collections[0]
    item = {
        'type': 'Feature',
        'id': '%s_%s' % (items[0]['eo:platform'], items[0].date),
        'bbox': bbox,
        'geometry': geometry,
        'properties': props,
        'links': links,
        'assets': {}
    }
    return Item(item)



def fetch(items, geometry, keys, proj=None, res=None):
    """ This fetches data from just the AOI and clips it """
    derived_item = create_derived_item(items, geometry)

    bands = []
    for k in keys:
        bands += items[0].asset(k).get('eo:bands', [])
    filename = items[0].get_filename(path=config.DATADIR, filename=config.FILENAME).replace('.json','.tif')
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    derived_item._data['assets'] = {
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
        geovec = geometry_to_GeoVector(geometry)
        imgout = algs.cookie_cutter(geoimgs, filename, geovec[0], xres=res[0], yres=res[1], 
                                    proj=proj, options=OPTS)
        logger.info("Created %s" % imgout.filename())
        return derived_item
    except Exception as err:
        print('Error: ', str(err))


