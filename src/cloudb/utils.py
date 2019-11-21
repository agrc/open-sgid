#!/usr/bin/env python
# * coding: utf8 *
'''
utils.py
A module that helps out
'''


def format_time(seconds):
    '''seconds: number
    returns a human-friendly string describing the amount of time
    '''
    minute = 60.00
    hour = 60.00 * minute

    if seconds < 30:
        return '{} ms'.format(int(seconds * 1000))

    if seconds < 90:
        return '{} seconds'.format(round(seconds, 2))

    if seconds < 90 * minute:
        return '{} minutes'.format(round(seconds / minute, 2))

    return '{} hours'.format(round(seconds / hour, 2))
