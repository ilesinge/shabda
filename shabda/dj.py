#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Shabda engine"""

from functools import partial
import random
import os
import asyncio
import urllib

import freesound
import pydub
from termcolor import colored
from shabda.display import print_error
from shabda.client import Client
from shabda.sampleset import SampleSet


class Dj:
    """Shabda engine"""

    client = None

    def __init__(self):
        self.client = Client()

    def list(self, word, max_number=None):
        """List files for a sample name"""
        sampleset = SampleSet(word)
        return sampleset.list(max_number)

    async def fetch(self, word, num):
        """Fetch a collection of samples"""
        sound = None
        sampleset = SampleSet(word)

        existing_samples = sampleset.list(num)
        existing_number = len(existing_samples)
        if existing_number >= num:
            return True

        master_id = sampleset.master_id
        if master_id:
            sound = self.client.get_sound(
                master_id, fields="id,name,type,duration,previews"
            )
            print(colored("Master sound exists...", "green"))

        if not sound:
            sound = await self.search_master_sound(word)

        if not sound:
            sampleset.clean()
            return False

        sampleset.master_id = sound.id

        print("Sound found: " + sound.name)

        similar = sound.get_similar(
            fields="id,name,type,duration,previews",
            page_size=50,
        )

        print("Found " + str(len(similar.results)) + " similar sounds.")

        ssounds = []
        for result in similar:
            if existing_number >= num:
                break
            if result.id == sound.id:
                continue
            if result.duration > 5:
                continue
            if result.id in sampleset.sounds:
                continue
            ssounds.append(result)
            existing_number += 1

        print("Remaining " + str(len(ssounds)) + " similar sounds after filtering.")

        sample_num = len(existing_samples)
        tasks = []
        for ssound in ssounds:
            tasks.append(self.download(sampleset, ssound, sample_num))
            sample_num += 1
        await asyncio.gather(*tasks)

        sampleset.saveconfig()

        if len(sampleset.list()) == 0:
            sampleset.clean()
            return False

        return True

    def random_word(self):
        """Choose a random word"""
        file = os.path.dirname(__file__) + "/" + "1000nouns.txt"
        words = open(file, "r", encoding="utf-8").read().splitlines()
        word = random.choice(words)
        return word

    async def search_master_sound(self, word):
        """Search master sound for a word"""
        found = None
        while found is None:
            print("")
            print(colored('Searching freesound for "' + word + '"...', "green"))
            print("")
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                partial(
                    self.client.text_search,
                    query=word,
                    fields="id,name,type,duration,previews",
                    page_size=10,
                    filter="duration:[* TO 1]",
                ),
            )

            if len(results.results) == 0:
                print_error("No found samples.")
                word = self.random_word()
            else:
                found = True

        key = random.randint(0, len(results.results) - 1)
        sound = results[key]
        return sound

    async def download(self, sampleset, ssound, sample_num):
        """Download a sample, normalize and cut it"""

        def match_target_amplitude(sound, target_dbfs):
            change_in_dbfs = target_dbfs - sound.dBFS
            return sound.apply_gain(change_in_dbfs)

        word_dir = sampleset.dir()
        try:
            source_name = str(sample_num) + "-source"
            source_path = word_dir + "/" + source_name
            export_name = str(sample_num) + ".wav"
            export_path = word_dir + "/" + export_name

            print("Dowloading " + word_dir + " sample #" + str(sample_num) + "...")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, ssound.retrieve, word_dir, source_name)

            sound = pydub.AudioSegment.from_file(source_path)
            sound = sound.set_frame_rate(44100)
            sound = sound.set_channels(1)
            sound = sound.set_sample_width(2)
            sound = match_target_amplitude(sound, -20.0)
            sound.export(export_path, format="wav")

            sampleset.add(ssound.id)
            print("Sample " + word_dir + "#" + str(sample_num) + " downloaded!")
        except pydub.exceptions.CouldntDecodeError as exception:
            print_error("Error while decoding source file", exception)
        except freesound.FreesoundException as exception:
            print_error("Error while downloading sound", exception)
        except urllib.error.ContentTooShortError as exception:
            print_error("Content to short", exception)
        if os.path.exists(source_path):
            os.remove(source_path)
