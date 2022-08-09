Shabda
======

![Shabda logo](assets/logo.png)


Shabda is a tool to fetch random samples from https://freesound.org/ based on given words, for use in impro sessions on instruments such as Tidal Cycles and Estuary.

[Shabda](https://en.wikipedia.org/wiki/Shabda) is the Sanskrit word for "speech sound". In Sanskrit grammar, the term refers to an utterance in the sense of linguistic performance. 

Install
-------

- Install Python 3: https://www.python.org/
- Install pip: https://pypi.org/project/pip/
- Install pipenv: `pip install pipenv`
- Install dependencies: `pipenv install`
- Install ffmpeg: https://ffmpeg.org/ (e.g. Debian/Ubuntu: `apt install ffmpeg`)

Use
---

Execute in terminal `pipenv run python shabda_cli.py <word1> <word2> <...> --num <number_of_sample_per_word>`

```
pipenv run python shabda_cli.py spaghetti monster --num 4
```

Launch the web application:

In debug mode:
```
FLASK_APP=shabda FLASK_DEBUG=1 pipenv run flask run
```
In production:
```
pipenv run gunicorn --workers=4 "shabda:create_app()" -b localhost:8000
```

Notes
-----

With Estuary, Shabda makes use of this feature: https://github.com/dktr0/estuary/wiki#adding-sound-files-to-estuarywebdirt-on-the-fly

To do
-----

- Move all this to github issues :)
- Explain how to launch on codespace / how to make port public
- Change allowed duration in definition ?
- List API and view
- Solidify: Retry, Queue workers, queue status?
  - https://huey.readthedocs.io/en/latest/index.html
  - https://github.com/litements/litequeue
  - (but with those there is no way to know a queue's status?)
- Explain risks about throttling: https://freesound.org/docs/api/overview.html
- Allow to rename sample ?
  - Allow emojis in sample name ?
  - Allow spaces in sample name ? special unicode spaces ? Reverse ?
- Record your voice
- Extract percussive ?
  - https://librosa.org/doc/latest/generated/librosa.effects.hpss.html
- Use advanced search in a funky way: https://freesound.org/docs/api/analysis_docs.html#analysis-docs
- Fix refresh token method. Refresh regularly ?
- Delete old samples (e.g. 7 days after last usage, note usage date)
- Autorun pylint
- Autorun pytest
- Better cli interface (pack definition, licenses) 
- pip module