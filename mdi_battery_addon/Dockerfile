ARG BUILD_FROM=ghcr.io/home-assistant/base:3.18
FROM $BUILD_FROM

ENV LANG C.UTF-8

# 1) Bypass PEP 668's externally-managed check
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# 2) Install Alpine dev packages for data/plot libs
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

# 3) Copy requirements & install Python libs
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# 4) Copy your Python code
COPY main.py /app/main.py

# 5) Copy the s6 service run script
COPY etc/services.d/battery-service/run /etc/services.d/battery-service/run
RUN chmod +x /etc/services.d/battery-service/run

# 6) Expose if you want direct port usage (optional)
EXPOSE 5000

# 7) No custom ENTRYPOINT or CMD. We rely on the s6 overlay from the base image.
