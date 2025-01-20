ARG BUILD_FROM=ghcr.io/home-assistant/base:3.18
FROM $BUILD_FROM

ENV LANG C.UTF-8
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# Install dependencies
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

# Install Python packages
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Copy application code
COPY main.py /app/main.py

# Copy s6 service configuration
COPY etc/services.d/battery-service/run /etc/services.d/battery-service/run
RUN chmod +x /etc/services.d/battery-service/run

EXPOSE 5000
