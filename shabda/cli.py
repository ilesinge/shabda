#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Shabda command line interface"""

import asyncio
from typing import List
from enum import Enum
import os
from configparser import ConfigParser

import typer
from rich.console import Console
from rich import print as richprint

from shabda.dj import Dj


shabda_path = os.path.expanduser("~/.shabda/")
config_file = shabda_path + "config.ini"
os.makedirs(shabda_path, exist_ok=True)
open(config_file, "a+", encoding="utf-8").close()
config_parser = ConfigParser()
config_parser.read(config_file)

samples_path = config_parser.get("shabda", "samples_path", fallback="samples/")
speech_sample_path = config_parser.get(
    "shabda", "speech_sample_path", fallback="speech_samples/"
)

err_console = Console(stderr=True)

dj = Dj(shabda_path, samples_path, speech_sample_path)


class License(str, Enum):
    """License types"""

    CC0 = "cc0"
    BY = "by"
    BY_NC = "by-nc"


def _main(
    definition: str = typer.Argument(
        ...,
        help="""The sound pack definition: comma separated words with optional sample number.
e.g. blue:2,red:4""",
    ),
    licenses: List[License] = typer.Option(
        [],
        help="""Allowed licenses - multiple options allowed.
Valid values are cc0 (Public Domain), by (Attribution), by-nc (Attribution Non-commercial)""",
        show_default="All",
    ),
):
    """Fetch random samples from freesound.org based on given words"""
    asyncio.run(main(definition, licenses))


async def fetch_one(word, number, licenses):
    """Fetch a single sample set"""
    return await dj.fetch(word, number, licenses)


async def main(definition, licenses):
    """CLI router"""

    try:
        words = dj.parse_definition(definition)
    except ValueError as ex:
        err_console.print("[bold red]" + str(ex) + "[/bold red]")
        raise typer.Exit(code=1)

    tasks = []
    for word, number in words.items():
        if number is None:
            number = 1
        tasks.append(fetch_one(word, number, licenses))
    await asyncio.gather(*tasks)

    richprint("[bold green]Done![/bold green]")


def cli():
    """CLI router"""
    typer.run(_main)


if __name__ == "__main__":
    typer.run(_main)
