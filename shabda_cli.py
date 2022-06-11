#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Shabda command line interface"""

import argparse
import asyncio

from shabda.dj import Dj


async def main():
    """CLI router"""
    parser = argparse.ArgumentParser(description="Dawnlods som ear stofu")
    parser.add_argument("word", nargs="+", help="Waddyawant?")
    parser.add_argument("--num", type=int, default=5, nargs="?", help="Ow many?")
    args = parser.parse_args()

    dj = Dj()
    for word in args.word:
        await dj.fetch(word, args.num)

    print("")
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
