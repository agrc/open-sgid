FROM osgeo/gdal:ubuntu-small-latest

RUN apt-get update -y && apt-get upgrade -y

RUN apt-get install -y --no-install-recommends \
  build-essential \
  gnupg2 \
  && \
  apt-get clean

RUN ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
  unixodbc-dev \
  && \
  apt-get clean

RUN apt-get install -y --no-install-recommends \
  python3-dev \
  python3-pip \
  && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -

RUN curl https://packages.microsoft.com/config/ubuntu/19.10/prod.list > /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update

RUN ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
  msodbcsql17

RUN chmod +rwx /etc/ssl/openssl.cnf
RUN sed -i 's/TLSv1.2/TLSv1/g' /etc/ssl/openssl.cnf
RUN sed -i 's/SECLEVEL=2/SECLEVEL=1/g' /etc/ssl/openssl.cnf

RUN python3 -m pip install -U pip

WORKDIR /app

COPY . .

RUN pip install .[cloud-run]

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 cloudb.server:app
