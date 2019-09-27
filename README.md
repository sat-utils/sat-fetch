# sat-fetch

Sat-fetch is a Python 3 library and command line tool for fetching, warping, and clipping remote imagery datasets. Sat-fetch loads scenes from a a STAC GeoJSON file, takes in a user AOI and list of asset keys to download. Sat-fetch will then perform windowed reads of the remote imagey if possible and save a multi-band image of all the assets, clipped to the user provided AOI.

Sat-fetch provides all the same functionality as sat-search, except has some additional features that require the use of GDAL and other libraries (sat-search is very lightweight requiring nothing but the Python `requests` library).

## Installing

Install from PyPi

$ pip install sat-fetch

Sat-fetch has a several dependencies on geospatial libraries, so to ease installation a Docker image is also available.

$ docker fetch sat-utils/sat-fetch:latest

## Using sat-fetch

The sat-fetch Command Line Interface (CLI) can be used just as the [sat-search](https://github.com/sat-utils/sat-search) CLI:

$ docker run --rm -v $PWD:/home/geolambda/work -it sat-utils/sat-fetch:latest sat-fetch -h

with the only difference being the addition of a new argument to the CLI, `fetch`. Whereas `download` downloads the original file as is, `fetch` only gets the area of the image within the `intersects` AOI, clips the output image to to the AOI, and stacks all the bands desired into a single file.


## Development

$ docker build . -t sat-utils/sat-fetch:latest


$ docker run -v ${PWD}:/work --rm -it sat-utils/sat-fetch:latest


## Known issues

- sat-fetch does not work with GDAL 2.2.3 (and perhaps earlier versions) due to [this bug](https://github.com/OSGeo/gdal/pull/295) which was fixed in 2.2.4. GDAL 2.2.3 is the default version on Ubuntu 18.04, use the [UbuntuGIS unstable repository](https://launchpad.net/~ubuntugis/+archive/ubuntu/ubuntugis-unstable) to update GDAL.


## About
sat-fetch is part of a collection of tools called [sat-utils](https://github.com/sat-utils).
