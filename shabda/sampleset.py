"""Utilities for managing a sample set"""

import os
import json
from glob import glob
from shabda.sound import Sound


class SampleSet:
    """A set of sample files"""

    word = None
    master_id = None
    sounds = []

    def __init__(self, word):
        """Initialize the sample set"""
        self.word = word
        directory = self.dir()
        if not os.path.exists(directory):
            os.makedirs(directory)
        else:
            try:
                with open(directory + "/config", encoding="utf-8") as config_file:
                    config = json.load(config_file)
                    self.master_id = config["master"]
                    self.sounds = config["sounds"]
            except IOError:
                self.master_id = None
                self.sounds = []

    def dir(self):
        """Return the directory for this sample set"""
        return "samples/" + self.word

    def list(self, max_number=None, licenses=None):
        """List sounds for a sample name"""
        # accept None as a max_number

        sounds = []
        for sound in self.sounds:
            if licenses is None or sound["license"] in licenses:
                sounds.append(Sound(configsound=sound))
        if max_number is not None:
            sounds = sounds[0:max_number]

        return sounds

    def add(self, sound):
        """Add a sound to the sample set"""
        self.sounds.append(
            {
                "id": sound.id,
                "url": sound.url,
                "username": sound.username,
                "license": sound.licensename,
                "file": sound.file,
            }
        )

    def contains(self, sound_id):
        """Check if a sound id is contained in the sample set"""
        for sound in self.sounds:
            if sound["id"] == sound_id:
                return True
        return False

    def clean(self):
        """Clean the sample set"""
        directory = self.dir()
        if not glob(directory + "/*.wav"):
            os.rmdir(directory)

    def saveconfig(self):
        """Save the master sound ID"""
        directory = self.dir()
        with open(directory + "/config", "w", encoding="utf-8") as config_file:
            json.dump({"master": self.master_id, "sounds": self.sounds}, config_file)
