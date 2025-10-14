#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
setup.py
A module that installs cloudb as a module
"""
from pathlib import Path

from setuptools import find_packages, setup

setup(
    name="cloudb",
    version="1.0.8",
    license="MIT",
    description="A cli to synchronize the internal sgid with the open sgid",
    long_description=(Path(__file__).parent / "src" / "readme.md").read_text(),
    long_description_content_type="text/markdown",
    author="UGRC",
    author_email="ugrc-developers@utah.gov",
    url="https://github.com/agrc/open-sgid",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Utilities",
    ],
    project_urls={
        "Issue Tracker": "https://github.com/agrc/open-sgid/issues",
    },
    keywords=["gis"],
    install_requires=[
        "colorama==0.*",
        "docopt==0.*",
        "pyodbc==5.*",
        "psycopg2-binary==2.*",
        "python-dotenv==1.*",
        "gdal==3.*",
    ],
    extras_require={
        "cloud-run": [
            "flask==3.*",
            "gunicorn==23.*",
            "google-cloud-storage==3.*",
        ],
        "tests": [
            "pytest-cov==6.*",
            "pytest-instafail==0.5.*",
            "pytest-mock==3.*",
            "pytest-ruff==0.*",
            "pytest-watch==4.*",
            "pytest==8.*",
            "ruff==0.*",
        ],
    },
    setup_requires=[
        "pytest-runner",
    ],
    entry_points={
        "console_scripts": [
            "cloudb = cloudb.main:main",
        ]
    },
)
