ARG BUILD_FROM=ghcr.io/home-assistant/base:3.18
FROM $BUILD_FROM

# Set a UTF-8 locale
ENV LANG C.UTF-8

# 1) Install Alpine packages required to compile data/plotting libraries
#    (pandas, numpy, matplotlib, etc.)
RUN apk add --no-cache \
    python3 \
    py3-pip \
    build-base \
    musl-dev \
    freetype-dev \
    libpng-dev \
    openblas-dev \
    gfortran \
    pkgconf

# 2) Copy your Python dependencies list
COPY requirements.txt /tmp/requirements.txt

# 3) Install Python dependencies
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# 4) Copy your add-on scripts/code
COPY run.sh /run.sh
COPY main.py /main.py
RUN chmod a+x /run.sh

# 5) (Optional) Expose if you’re not using Ingress only
EXPOSE 5000

# 6) Set default command
CMD [ "/run.sh" ]
