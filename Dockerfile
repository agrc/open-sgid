FROM ghcr.io/osgeo/gdal:ubuntu-full-3.13.3 AS base

RUN chmod +rwx /etc/ssl/openssl.cnf
RUN sed -i 's/TLSv1.2/TLSv1/g' /etc/ssl/openssl.cnf
RUN sed -i 's/SECLEVEL=2/SECLEVEL=1/g' /etc/ssl/openssl.cnf

RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

RUN apt-get update -y

RUN apt-get install -y --no-install-recommends \
  python3-pip \
  && \
  apt-get clean

RUN apt-get install -y --no-install-recommends \
  unixodbc-dev \
  && \
  apt-get clean

RUN apt-get install -y --no-install-recommends \
  curl \
  gnupg2 \
  lsb-release \
  && \
  apt-get clean

RUN apt reinstall ca-certificates -y

RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc -o /tmp/microsoft.asc \
  && curl -fsSL https://packages.microsoft.com/keys/microsoft-2025.asc >> /tmp/microsoft.asc \
  && gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg /tmp/microsoft.asc \
  && rm /tmp/microsoft.asc
RUN curl -fsSL https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list -o /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update && apt install -y apt-utils

RUN ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
  msodbcsql18 && apt-get clean

FROM base AS test

WORKDIR /app

COPY . .

RUN pip install --break-system-packages -e ".[dev]"

FROM base AS prod

WORKDIR /app

COPY . .

RUN pip install --break-system-packages .

CMD ["cloudb", "sync"]
