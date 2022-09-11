#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Shabda command line interface"""

import asyncio
from typing import List
from enum import Enum
import typer
from rich.console import Console
from rich import print as richprint

from shabda.dj import Dj

err_console = Console(stderr=True)

dj = Dj()


class License(str, Enum):
    """License types"""

    CC0 = "cc0"
    BY = "by"
    BY_NC = "by-nc"


def _main(
    definition: str = typer.Argument(
        ...,
        help="The sound pack definition: comma separated words with optional sample number. e.g. blue:2,red:4",
    ),
    licenses: List[License] = typer.Option(
        [],
        help="Allowed licenses - multiple options allowed. Valid values are cc0 (Public Domain), by (Attribution), by-nc (Attribution Non-commercial)",
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


if __name__ == "__main__":
    typer.run(_main)
