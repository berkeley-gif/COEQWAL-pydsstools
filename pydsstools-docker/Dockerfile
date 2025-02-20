FROM --platform=linux/amd64 python:3.10-slim

# Install system build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    zlib1g-dev \
    gfortran \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /pydsstools/src/external/dss/linux64 \
    && mkdir -p /pydsstools/src/external/gridv6/headers \
    && mkdir -p /pydsstools/src/external/zlib

# Copy heclib.a from the local directory
COPY heclib/heclib.a /pydsstools/src/external/dss/linux64/

# Install specific versions of Python dependencies (found through trial and error)
RUN pip install numpy==1.23.5 pandas==1.5.3 setuptools wheel

# Set environment variables for compilation
ENV CFLAGS="-I/usr/include -I/pydsstools/src/external/dss/headers -I/pydsstools/src/external/gridv6/headers"
ENV LDFLAGS="-L/usr/lib/x86_64-linux-gnu -L/pydsstools/src/external/dss/linux64"

# Install pydsstools
RUN pip install pydsstools

# Set the default command
CMD ["python"]