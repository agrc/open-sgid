#!/usr/bin/env python
# * coding: utf8 *
"""
test_index - A script that tests the index.py file
"""

from cloudb import index


def test_index_creation():
    """
    Tests the creation of the indices
    """
    assert len(index.INDEXES) == 34
