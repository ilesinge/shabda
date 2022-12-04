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

Roadmap
-----

See: https://github.com/users/ilesinge/projects/4
