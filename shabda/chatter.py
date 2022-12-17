"""Text to speech functions"""

import random
import shabda.cache


def pick_voice(language, ssml_gender, client):
    """Pick voice based on language and gender"""
    cache_key = language + "_" + str(ssml_gender)
    voice_name = shabda.cache.load(cache_key)
    if voice_name is None:
        voices = _get_voices(client)
        available_voices = []
        selected_voices = []
        preferred_voices = []
        for voice in voices:
            if voice["language_code"] == language:
                available_voices.append(voice)
        for voice in available_voices:
            if voice["ssml_gender"] == ssml_gender:
                selected_voices.append(voice)
        if len(selected_voices) == 0:
            selected_voices = available_voices
        for voice in selected_voices:
            if "Wavenet" in voice["name"] or "Neural" in voice["name"]:
                preferred_voices.append(voice)
        if len(preferred_voices) == 0:
            preferred_voices = selected_voices

        voice_name = random.choice(preferred_voices)["name"]
        shabda.cache.save(cache_key, voice_name)
    return voice_name


def _get_voices(client):
    """Get all available voices"""
    dict_voices = shabda.cache.load("voices")
    if dict_voices is None:
        voices = client.list_voices().voices
        dict_voices = []
        for voice in voices:
            dict_voices.append(
                {
                    "name": voice.name,
                    "language_code": voice.language_codes[0],
                    "ssml_gender": voice.ssml_gender,
                }
            )
        shabda.cache.save("voices", dict_voices)
    return dict_voices
