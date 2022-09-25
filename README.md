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

Use (command line)
------------------

In order to download a sample pack, execute in the terminal `pipenv run python shabda_cli.py <definition> --licenses <license_name>`.

Any word can be a pack definition. If you want more than one sample, separate words by a comma: `blue,red`

You can define how many variations of a sample to assemble by adding a colon and a number.
e.g. `blue,red:3,yellow:2` will produce one 'blue' sample, three 'red' samples and two 'yellow' sample.

The optional `--licenses` parameter allows to fetch only samples that have the specified license. Multiple licenses can be allowed by repeating the `--licenses` argument. Possible licenses are `cc0` (Creative Commons Zero), `by` (Creative Commons Attribution), and `by-nc` (Creative Commons Attribution Non-Commercial).

Full example:
```
pipenv run python shabda_cli.py spaghetti:2,monster:4 --licenses cc0 --licenses by
```

Use (web application)
---------------------

Launch the web application:

In debug mode:
```
FLASK_APP=shabda FLASK_DEBUG=1 pipenv run flask run
```
In production:
```
pipenv run gunicorn --workers=4 "shabda:create_app()" -b localhost:8000
```

Test
----

```
pipenv run pytest
```

Notes
-----

With Estuary, Shabda makes use of this feature: https://github.com/dktr0/estuary/wiki#adding-sound-files-to-estuarywebdirt-on-the-fly

To do
-----

- Move all this to github issues or project :)
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
- Enforce all alpha minuscules and numbers in pack definition
- Generate speech ;
    - via external cli ? https://linuxhint.com/command-line-text-speech-apps-linux/
    - via python lib ? https://pypi.org/project/pyttsx3/
    - via TTS API? https://rapidapi.com/collection/best-text-to-speech-apis
- Delete old samples (e.g. 7 days after last usage, note usage date)
- Autorun pylint
- Autorun pytest
- Better cli interface (pack definition, licenses) 
- pip module