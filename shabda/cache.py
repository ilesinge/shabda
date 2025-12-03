#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Simple cache engine."""

import time
import pickle
import os

CACHE_PATH = os.path.expanduser("~/.shabda/cache/")
os.makedirs(CACHE_PATH, exist_ok=True)


def save(key, value, ttl=60 * 60 * 24):
    """Write a key:value pair to cache."""
    # ttl is "time to live" of the item in seconds
    filepath = os.path.normpath(os.path.join(CACHE_PATH, key))
    # Ensure the normalized filepath is within CACHE_PATH
    if not filepath.startswith(os.path.normpath(CACHE_PATH)):
        raise Exception("Invalid cache key: path traversal detected")
    expiry = int(time.time() + ttl)
    cache = (expiry, value)
    with open(filepath, "w+b") as file:
        pickle.dump(cache, file)


def load(key):
    """Read the value for given key from cache."""
    filepath = os.path.normpath(os.path.join(CACHE_PATH, key))
    # Ensure the normalized filepath is within CACHE_PATH
    if not filepath.startswith(os.path.normpath(CACHE_PATH)):
        raise Exception("Invalid cache key: path traversal detected")
    try:
        with open(filepath, "r+b") as file:
            expiry, value = pickle.load(file)
    except FileNotFoundError:
        return None

    if time.time() > expiry:
        # Expired key, delete it
        os.remove(filepath)
        return None
    return value
