Shabda
======

![Shabda logo](assets/logo.png)


Shabda is a tool to fetch random samples from https://freesound.org/ based on given words, for use in impro sessions on instruments such as Tidal Cycles and Estuary.

Shabda is the Sanskrit word for "speech sound". In Sanskrit grammar, the term refers to an utterance in the sense of linguistic performance. 

Install
-------

- Install Python 3: https://www.python.org/
- Install pip: https://pypi.org/project/pip/
- Install pipenv: `pip install pipenv`
- Install dependencies: `pipenv install`
- Install ffmpeg: https://ffmpeg.org/ (e.g. Debian/Ubuntu: `apt install ffmpeg`)

Use
---

Execute in terminal `python3 shabda_cli.py <word1> <word2> <...> --num <number_of_sample_per_word>`

```
python3 shabda_cli.py spaghetti monster --num 4
```

Launch the web application:

In debug mode:
```
FLASK_APP=shabda FLASK_ENV=development pipenv run flask run
```
In production:
```
pipenv run gunicorn --workers=4 "shabda:create_app()" -b localhost:8000
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

- Explain how to use
  - https://github.com/dktr0/estuary/wiki#adding-sound-files-to-estuarywebdirt-on-the-fly-early-august-2021
- Explain how to launch on codespace / how to make port public
- Why do some samples don't work ? see https://shabda.ndre.gr/lol:2.json
- Finetune query:
  - total number of results
- Change allowed duration in definition ?
- URL: JSON + download missing resources (fresh=1?)
- List API and view
- Solidify: Retry, Queue workers, queue status?
  - https://huey.readthedocs.io/en/latest/index.html
  - https://github.com/litements/litequeue
  - (but with those there is no way to know a queue's status?)
- Communicate about throttling: https://freesound.org/docs/api/overview.html
- Communicate on Estuary Discord, twitter, Tidal Cycles club, etc.
- Prod
  - Host on free service?: separate code from assets
  - Deploy on Heroku ? Vercel ?
  - Deploy with ansible through Github Actions
- Don't cut sound ? or trim before cut ? keep beginning only ?
- Allow to rename sample ?
  - Allow emojis in sample name ?
  - Allow spaces in sample name ? special unicode spaces ? Reverse ?
- Record your voice
- Adjust amplitude normalization of samples
- Remove silence at beginning and end of samples:
  - https://www.tutorialexample.com/python-remove-silence-in-wav-using-librosa-librosa-tutorial/
  - https://librosa.org/doc/latest/generated/librosa.effects.trim.html
- Extract percussive ?
  - https://librosa.org/doc/latest/generated/librosa.effects.hpss.html
- Use advanced search in a funky way: https://freesound.org/docs/api/analysis_docs.html#analysis-docs
