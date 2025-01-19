ARG BUILD_FROM=ghcr.io/home-assistant/base:3.18
FROM $BUILD_FROM

ENV LANG C.UTF-8

# Install Python + pip
RUN apk add --no-cache \
    python3 \
    py3-pip

# Copy requirements and install
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Copy our scripts/code
COPY run.sh /run.sh
COPY main.py /main.py
RUN chmod a+x /run.sh

# Expose port 5000 (optional, since we're using Ingress)
EXPOSE 5000

CMD [ "/run.sh" ]
