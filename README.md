# sat-fetch

Sat-fetch is a Python 2/3 library and command line tool for fetching, warping, and clipping remote imagery datasets. Sat-fetch loads scenes from a a STAC GeoJSON file, takes in a user AOI and list of asset keys to download. Sat-fetch will then perform windowed reads of the remote imagey if possible and save a multi-band image of all the assets, clipped to the user provided AOI.

## About
sat-fetch was created by [Development Seed](<http://developmentseed.org>)
