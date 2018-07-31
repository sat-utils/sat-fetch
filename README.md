# SAT-FETCH

Sat-fetch is a Python 2/3 library and command line tool for fetching, warping, and clipping remote imagery datasets. Sat-fetch loads scenes from a a STAC GeoJSON file, takes in a user AOI and list of asset keys to download. Sat-fetch will then perform windowed reads of the remote imagey if possible and save a multi-band image of all the assets, clipped to the user provided AOI.

Sat-fetch provides all the same functionality as sat-search, except has some additional features that require the use of GDAL and other libraries (sat-search is very lightweight requiring nothing but the Python `requests` library).


## Using sat-fetch


$ docker run --rm -v $PWD:/home/geolambda/work -it developmentseed/sat-fetch:latest sat-fetch -h


## About
sat-search was created by [Development Seed](<http://developmentseed.org>) and is part of a collection of tools called [sat-utils](https://github.com/sat-utils).
