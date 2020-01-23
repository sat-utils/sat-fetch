FROM developmentseed/geolambda:1.2.0-python

# install requirements
WORKDIR /build
COPY requirements*txt /build/
RUN \
    pip install -r requirements.txt; \
    pip install -r requirements-dev.txt

# install app
COPY . /build
RUN \
    pip install . -v; \
    rm -rf /build/*;

WORKDIR /home/geolambda
