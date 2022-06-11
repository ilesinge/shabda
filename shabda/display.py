#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Display utilities"""

from termcolor import colored


def print_error(message, exception=None):
    """Print a frigging error"""
    print("")
    print(colored(message, "red"))
    print("")
    if exception:
        print(exception)
