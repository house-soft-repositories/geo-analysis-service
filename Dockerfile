FROM python:3.11-slim

# GDAL system dependencies
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    binutils \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Instala GDAL Python na mesma versão do sistema antes das demais deps
RUN GDAL_VERSION=$(gdal-config --version) && \
    pip install --no-cache-dir "GDAL==${GDAL_VERSION}" && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
