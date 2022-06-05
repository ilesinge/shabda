#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This CLI does blah blah."""

import argparse
import asyncio

from djmf.dj import Dj


async def main():
    parser = argparse.ArgumentParser(description="Dawnlods som ear shiiz")
    parser.add_argument("w00t", nargs="+", help="Waddyawant?")
    parser.add_argument("--num", type=int, default=5, nargs="?", help="Ow many?")
    args = parser.parse_args()

    dj = Dj()
    for word in args.w00t:
        await dj.fetch(word, args.num)

    print("")
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
