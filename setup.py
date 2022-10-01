#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
setup.py
A module that installs cloudb as a module
"""
from glob import glob
from os.path import basename, splitext

from setuptools import find_packages, setup

setup(
    name='cloudb',
    version='1.2.2',
    license='MIT',
    description='A cli to synchronize the internal sgid with the open sgid',
    author='UGRC',
    author_email='ugrc-developers@utah.gov',
    url='https://github.com/agrc/open-sgid',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
    ],
    project_urls={
        'Issue Tracker': 'https://github.com/agrc/open-sgid/issues',
    },
    keywords=['gis'],
    install_requires=[
        'colorama==0.*', 'docopt==0.*', 'pyodbc==4.*', 'psycopg2-binary==2.*', 'python-dotenv==0.*', 'gdal==3.*'
    ],
    extras_require={
        'cloud-run': [
            'flask==2.*',
            'gunicorn==20.*',
            'google-cloud-storage==2.*',
        ],
        'tests': [
            'pylint-quotes~=0.2',
            'pylint~=2.11',
            'pytest-cov>=3,<5',
            'pytest-instafail~=0.4',
            'pytest-isort~=3.0',
            'pytest-pylint~=0.18',
            'pytest-watch~=4.2',
            'pytest~=7.0',
            'yapf~=0.31',
        ]
    },
    setup_requires=[
        'pytest-runner',
    ],
    entry_points={'console_scripts': [
        'cloudb = cloudb.main:main',
    ]},
)
