#!/usr/bin/env python
# * coding: utf8 *
"""
server.py
a module that can receive web requests. this will be google cloud pub sub and
possibly github web hooks
"""

import logging
import os
from time import perf_counter

from flask import Flask

from . import utils
from .main import get_tables_from_change_detection, import_data, trim, update

app = Flask(__name__)


@app.route('/scheduled', methods=['POST'])
def schedule():
    """ schedule: the post route that gcp scheduler sends when it is time to execute
    """
    logging.debug('request accepted')

    dry_run = False
    if 'IS_DEVELOPMENT' in os.environ:
        dry_run = True

    has_errors = list([])
    total_seconds = perf_counter()

    try:
        trim_seconds = perf_counter()

        trim(dry_run)

        logging.info('completed in %s', utils.format_time(perf_counter() - trim_seconds))
    except Exception as error:
        logging.error('trim failure %s', error)
        has_errors.append(error)

    try:
        skip_if_missing = False
        missing = True
        import_seconds = perf_counter()

        import_data(skip_if_missing, missing, dry_run)

        logging.info('completed in %s', utils.format_time(perf_counter() - import_seconds))

    except Exception as error:
        logging.error('app failure %s', error)
        has_errors.append(error)

    try:
        update_seconds = perf_counter()

        tables = get_tables_from_change_detection()
        update(tables, dry_run)

        logging.info('completed in %s', utils.format_time(perf_counter() - update_seconds))
    except Exception as error:
        logging.error('app failure %s', error)
        has_errors.append(error)

    if has_errors:
        return '||'.join(has_errors)

    logging.info('successful run completed in %s', utils.format_time(perf_counter() - total_seconds))

    return ('', 204)


if __name__ == '__main__':
    PORT = int(str(os.getenv('PORT'))) if os.getenv('PORT') else 8080

    # This is used when running locally. Gunicorn is used to run the
    # application on Cloud Run. See entrypoint in Dockerfile.
    app.run(host='127.0.0.1', port=PORT, debug=True)
