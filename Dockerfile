FROM ghcr.io/osgeo/gdal:ubuntu-full-3.12.4 AS base

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
  gnupg2 \
  lsb-release \
  && \
  apt-get clean

RUN apt reinstall ca-certificates -y

RUN curl -s https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc
RUN curl -s https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
RUN curl -s https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | tee /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update && apt install -y apt-utils

RUN ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
  msodbcsql17 && apt-get clean

FROM base AS test

WORKDIR /app

COPY . .

RUN pip install -e ".[dev]"

FROM base AS prod

WORKDIR /app

COPY . .

RUN pip install .

CMD ["cloudb", "sync"]
