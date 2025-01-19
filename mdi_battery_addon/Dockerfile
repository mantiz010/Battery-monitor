ARG BUILD_FROM=ghcr.io/home-assistant/base:3.18
FROM $BUILD_FROM

ENV LANG C.UTF-8

# 1) Install necessary Alpine dev packages for pandas, matplotlib, etc.
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

# 2) Copy your Python dependencies list
COPY requirements.txt /tmp/requirements.txt

# 3) Install Python packages (the step that was failing before)
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# 4) Copy your add-on scripts/code
COPY run.sh /run.sh
COPY main.py /main.py
RUN chmod a+x /run.sh

# 5) (Optional) Expose if not only using Ingress
EXPOSE 5000

# 6) Default command
CMD [ "/run.sh" ]
