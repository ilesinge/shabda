Shabda
======

A tool to fetch random samples from https://freesound.org/ based on given words, for use in impro sessions on instruments such as Tidal Cycles.

Install
-------

- Install Python 3: https://www.python.org/
- Install pip: https://pypi.org/project/pip/
- Install pipenv: `pip install pipenv`
- Install dependencies: `pipenv install`

Use
---

Execute in terminal `python3 shabda_cli.py <word1> <word2> <...> --num <number_of_sample_per_word>`

```
python3 shabda_cli.py spaghetti monster --num 4
```

Launch the web application:

In debug mode:
```
pipenv shell
FLASK_APP=shabda FLASK_ENV=development flask run
```

Scenario
--------

- Provide some words
- For each word
    - Create a sample directory for this word
    - Define a random sample duration
    - Search a list of 100 sounds containing this word
    - Pick one random sound
    - Get 100 similar sounds to this sound
    - Pick 5 random sounds from those
    - For each of those random similar sounds
        - Download sound
        - Cut a sample of X seconds, with random position
        - Save in the word samples directory in wav format
- Have fun :)

To do
-----

- Remove Docker / Docker-compose if not needed ?
- Shabda web for Estuary dynamic samples
  - https://github.com/dktr0/estuary/wiki#adding-sound-files-to-estuarywebdirt-on-the-fly-early-august-2021
    - JSON + expose assets
  - URL: Preparatory screen
  - Number of samples in query definition
  - Finetune: length, etc.
  - URL: JSON (check only downloaded resources)
  - URL: JSON + download missing resources (fresh=1?)
  - Solidify: Retry, Queue workers, queue status ?
    - https://huey.readthedocs.io/en/latest/index.html
    - https://github.com/litements/litequeue
    - (but with those there is no way to know a queue's status ?)
  - Serve assets
  - Host on free service: separate code from assets
  - Change name
  - Beware Throttling: https://freesound.org/docs/api/overview.html
- Download as zip
- Random word from dictionary
- Normalize samples volume
    - How to normalize sound:
    - peak_amplitude = sound.max
    - sound_gain_6db = sound + 6
    - https://www.pydoc.io/pypi/pydub-0.9.5/autoapi/effects/index.html
    - https://github.com/jiaaro/pydub/issues/90
    - https://stackoverflow.com/questions/42492246/how-to-normalize-the-volume-of-an-audio-file-in-python-any-packages-currently-a/42496373
- Use advanced search in a funky way: https://freesound.org/docs/api/analysis_docs.html#analysis-docs
- record your voice
