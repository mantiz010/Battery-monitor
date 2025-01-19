ARG BUILD_FROM=ghcr.io/home-assistant/base:3.18
FROM $BUILD_FROM

ENV LANG C.UTF-8

# PEP 668 override: allow pip to install system-wide in a managed environment
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# Install Alpine dev packages for data libs (pandas, matplotlib, etc.)
RUN apk add --no-cache \
    python3 \
    py3-pip \
    build-base \
    musl-dev \
    python3-dev \
    freetype-dev \
    libpng-dev \
    openblas-dev \
    gfortran \
    pkgconf \
    cython \
    jpeg-dev \
    zlib-dev

COPY requirements.txt /tmp/requirements.txt

RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

COPY run.sh /run.sh
COPY main.py /main.py
RUN chmod a+x /run.sh

EXPOSE 5000
CMD [ "/run.sh" ]
