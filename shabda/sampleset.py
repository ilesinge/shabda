"""Utilities for managing a sample set"""

import os
import json
from glob import glob
from shabda.sound import Sound

FREESOUND = 1
TTS = 2


class SampleSet:
    """A set of sample files"""

    word = None
    master_id = None
    sounds = []
    type = FREESOUND
    samples_path = ""

    def __init__(self, word, soundtype=FREESOUND, samples_path="samples"):
        """Initialize the sample set"""
        self.word = word
        self.type = soundtype
        self.samples_path = samples_path
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
        directory = os.path.join(self.samples_path, self.word)
        if self.type == TTS:
            directory = os.path.join(self.samples_path, "speech_" + directory)
        return directory

    def list(self, max_number=None, licenses=None, gender=None, language=None):
        """List sounds for a sample name"""
        # accept None as a max_number

        sounds = []
        for sound in self.sounds:
            if (
                (licenses is None or sound["license"] in licenses)
                and (gender is None or sound["gender"] == gender)
                and (language is None or sound["language"] == language)
            ):
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
                "gender": sound.gender,
                "language": sound.language,
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
