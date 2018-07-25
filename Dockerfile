FROM developmentseed/geolambda:1.0.0

# install requirements
WORKDIR /build
COPY requirements*txt /build/
RUN \
    pip3 install -r requirements.txt; \
    pip3 install -r requirements-dev.txt

# install app
#COPY . /build
#RUN \
#    pip install . -v; \
#    rm -rf /build/*;

WORKDIR /home/geolambda
