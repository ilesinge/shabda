#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module does blah blah."""

from functools import partial
import random
import os
import asyncio
import urllib
from glob import glob

import freesound
import pydub
from termcolor import colored
from shabda.display import print_error
from shabda.client import Client


class Dj:
    """This class does blah blah."""

    client = None

    def __init__(self):
        self.client = Client()

    def list(self, word, max):
        word_dir = "samples/" + word
        filenames = []
        if os.path.exists(word_dir):
            filenames = filenames + glob(word_dir + "/*.wav")
        return filenames

    async def fetch(self, word, num):
        word_dir = "samples/" + word
        if not os.path.exists(word_dir):
            os.makedirs(word_dir)
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
            return

        similar = None
        while not similar:
            key = random.randint(0, len(results.results) - 1)
            sound = results[key]
            name = sound.name
            print("Sound found: " + name)
            try:
                similar = sound.get_similar(
                    fields="id,name,type,duration,previews",
                    page_size=50,
                )
            except freesound.FreesoundException as e:
                if e.code == 404:
                    print_error("Missing sound, continue")
                    continue
                else:
                    print_error("Error while getting similar sounds", e)
                    raise e

        ssounds = []
        for result in similar:
            if len(ssounds) >= num:
                break
            if result.id == sound.id:
                continue
            if result.duration > 5:
                continue
            ssounds.append(result)

        # Define random common duration for word samples
        sample_duration = random.randint(200, 5000)
        print("Random sample duration: " + str(sample_duration) + "ms")
        sample_num = 0
        tasks = []
        for ssound in ssounds:
            tasks.append(self.download(word_dir, ssound, sample_duration, sample_num))
            sample_num += 1
        await asyncio.gather(*tasks)

    async def download(self, word_dir, ssound, sample_duration, sample_num):
        try:
            source_name = ssound.name + "-source"
            source_path = word_dir + "/" + source_name
            print("Dowloading " + word_dir + " sample #" + str(sample_num) + "...")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, ssound.retrieve, word_dir, source_name)

            sound = pydub.AudioSegment.from_file(source_path)
            export_name = str(sample_num) + ".wav"
            duration = len(sound)
            begin = random.randint(0, max(duration - sample_duration, 0))
            sound = sound[begin : begin + sample_duration]  # random cut
            sound.export(word_dir + "/" + export_name, format="wav")
            print("Sample " + word_dir + "#" + str(sample_num) + " downloaded!")
        except pydub.exceptions.CouldntDecodeError as e:
            print_error("Error while decoding source file", e)
        except freesound.FreesoundException as e:
            print_error("Error while downloading sound", e)
        except urllib.error.ContentTooShortError as e:
            print_error("Content to short", e)
        if os.path.exists(source_path):
            os.remove(source_path)
