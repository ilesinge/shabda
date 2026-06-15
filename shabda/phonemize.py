"""ARPABET phoneme decomposition and IPA conversion"""

from functools import lru_cache

import pronouncing
import re

# Maps CMU ARPABET base phone (no stress digit) → IPA symbol.
# Source: CMU Pronouncing Dictionary phone set documentation.
ARPABET_TO_IPA = {
    # Vowels
    "AA": "ɑ",
    "AE": "æ",
    "AH": "ə",   # unstressed (0); stressed (1/2) → "ʌ" handled below
    "AO": "ɔ",
    "AW": "aʊ",
    "AY": "aɪ",
    "EH": "ɛ",
    "ER": "ɝ",
    "EY": "eɪ",
    "IH": "ɪ",
    "IY": "iː",
    "OW": "oʊ",
    "OY": "ɔɪ",
    "UH": "ʊ",
    "UW": "uː",
    # Consonants
    "B":  "b",
    "CH": "tʃ",
    "D":  "d",
    "DH": "ð",
    "F":  "f",
    "G":  "ɡ",
    "HH": "h",
    "JH": "dʒ",
    "K":  "k",
    "L":  "l",
    "M":  "m",
    "N":  "n",
    "NG": "ŋ",
    "P":  "p",
    "R":  "ɹ",
    "S":  "s",
    "SH": "ʃ",
    "T":  "t",
    "TH": "θ",
    "V":  "v",
    "W":  "w",
    "Y":  "j",
    "Z":  "z",
    "ZH": "ʒ",
}

# AH with primary/secondary stress is "ʌ" (STRUT), not schwa
_AH_STRESSED_IPA = "ʌ"


@lru_cache(maxsize=4096)
def _phones_for_word(word: str) -> tuple[str, ...]:
    """Cache CMU pronunciation lookups for repeated words."""
    phones_list = pronouncing.phones_for_word(word)
    if phones_list:
        return tuple(phones_list[0].split())
    return ()


def sentence_to_arpabet(
    sentence: str,
    overrides: dict[str, list[str]] | None = None,
) -> list[tuple[str, list[str] | None]]:
    """
    Break a sentence (underscores as spaces) into per-word ARPABET phone lists.

    Returns a list of (word, phones) tuples.  For words found in the CMU
    Pronouncing Dictionary, `phones` is a list of ARPABET tokens including
    stress digits (e.g. ["HH", "AH0", "L", "OW1"]).  For out-of-vocabulary
    words, `phones` is None — callers should fall back to whole-word synthesis.
    """
    # Treat punctuation and commas as separators so phrase definitions like
    # "foo,bar_baz" are tokenized into clean words.
    words = re.findall(r"[A-Za-z0-9]+", sentence.replace("_", " "))
    result = []
    overrides = overrides or {}
    for word in words:
        override_phones = overrides.get(word.lower())
        if override_phones:
            result.append((word, override_phones))
            continue
        phones = list(_phones_for_word(word.lower()))
        if phones:
            result.append((word, phones))
        else:
            result.append((word, None))
    return result


def arpabet_to_ipa(phone: str) -> str:
    """
    Convert a single ARPABET token (with optional stress digit) to an IPA string.

    Stress digits:
      0 → no prefix (unstressed)
      1 → ˈ (primary stress prefix)
      2 → ˌ (secondary stress prefix)

    Examples:
      "AH0" → "ə"
      "AH1" → "ˈʌ"
      "OW1" → "ˈoʊ"
      "HH"  → "h"
    """
    stress = ""
    base = phone
    if phone and phone[-1].isdigit():
        digit = phone[-1]
        base = phone[:-1]
        if digit == "1":
            stress = "ˈ"
        elif digit == "2":
            stress = "ˌ"
        # digit == "0" → no prefix

    # Special case: stressed AH (1 or 2) is STRUT vowel "ʌ", not schwa
    if base == "AH" and stress:
        ipa = _AH_STRESSED_IPA
    else:
        ipa = ARPABET_TO_IPA.get(base, base.lower())

    return stress + ipa


def is_stressed_phone(phone: str) -> bool:
    """Return True for ARPABET tokens marked with primary/secondary stress."""
    return bool(phone and phone[-1] in ("1", "2"))


def is_primary_stressed_phone(phone: str) -> bool:
    """Return True for ARPABET tokens marked with primary stress only."""
    return bool(phone and phone[-1] == "1")


def _chunk_phones_pre_stress(
    phones: list[str],
    is_chunk_boundary,
) -> list[list[str]]:
    """
    Split a phone sequence so each chunk ends right before a stressed phone.

    Example:
      ["P", "AH0", "P", "AA1"] -> [["P", "AH0", "P"], ["AA1"]]

    This creates larger, beat-alignable chunks where stressed material starts
    the following chunk.
    """
    if not phones:
        return []

    chunks = []
    start = 0

    for i, phone in enumerate(phones):
        if i > start and is_chunk_boundary(phone):
            chunks.append(phones[start:i])
            start = i

    chunks.append(phones[start:])
    chunks = [chunk for chunk in chunks if chunk]

    # Keep syllable onsets together with stressed nuclei by moving trailing
    # consonants from the previous chunk to the next chunk when the next chunk
    # starts on a stressed vowel (e.g. ["P"], ["AA1", "P"] -> ["P", "AA1", "P"]).
    for i in range(1, len(chunks)):
        curr = chunks[i]
        prev = chunks[i - 1]
        if not curr or not prev:
            continue
        if not is_chunk_boundary(curr[0]):
            continue

        move_start = len(prev)
        while move_start > 0 and not prev[move_start - 1][-1:].isdigit():
            move_start -= 1

        if move_start < len(prev):
            onset = prev[move_start:]
            chunks[i - 1] = prev[:move_start]
            chunks[i] = onset + curr

    return [chunk for chunk in chunks if chunk]


def chunk_phones_pre_primary_stress(phones: list[str]) -> list[list[str]]:
    """Split phones right before primary stress only (digit 1)."""
    return _chunk_phones_pre_stress(phones, is_primary_stressed_phone)


def chunk_phones_pre_any_stress(phones: list[str]) -> list[list[str]]:
    """Split phones right before primary or secondary stress (digits 1/2)."""
    return _chunk_phones_pre_stress(phones, is_stressed_phone)


def chunk_phones_pre_stress(phones: list[str]) -> list[list[str]]:
    """Default chunking: split phones right before primary stress only."""
    return chunk_phones_pre_primary_stress(phones)
