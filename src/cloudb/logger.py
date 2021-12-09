#!/usr/bin/env python
# * coding: utf8 *
"""
logger.py
A module that lets you filter log statements
"""
import datetime


class Logger():
    """a very stupid logger
    """
    severity = ['VERBOSE', 'DEBUG', 'INFO', 'WARNING', 'FATAL']
    verbosity = 'INFO'

    def init(self, verbosity='INFO'):
        """initialize the logger
        """
        if not verbosity:
            return

        self.verbosity = verbosity

    def verbose(self, value):
        """log level console items
        """
        self._print(value, 'VERBOSE')

    def debug(self, value):
        """log level console items
        """
        self._print(value, 'DEBUG')

    def info(self, value):
        """log level console items
        """
        self._print(value, 'INFO')

    def warn(self, value):
        """log level console items
        """
        self._print(value, 'WARNING')

    def fatal(self, value):
        """log level console items
        """
        self._print(value, 'FATAL')

    def _print(self, value, verbosity):
        if self.severity.index(verbosity) >= self.severity.index(self.verbosity):
            print(f'[{datetime.datetime.now().strftime("%m-%d-%Y %H:%M:%S")}] {value}')
