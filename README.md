Shabda
======

![Shabda logo](https://raw.githubusercontent.com/ilesinge/shabda/master/assets/logo.png)


Shabda is a tool to fetch random samples from https://freesound.org/ based on given words or to generate Text-to-Speech samples for use in impro sessions on instruments such as Tidal Cycles, Estuary or Strudel.

[Shabda](https://en.wikipedia.org/wiki/Shabda) is the Sanskrit word for "speech sound". In Sanskrit grammar, the term refers to an utterance in the sense of linguistic performance. 

Install
-------

- Install Python 3: https://www.python.org/
- Install pip: https://pypi.org/project/pip/
- Install ffmpeg: https://ffmpeg.org/ (e.g. Debian/Ubuntu: `apt install ffmpeg`)
- Install Shabda for standard usage: `pip install shabda`
or
- Install shabda for hacking:
    - Install poetry: https://python-poetry.org/docs/#installation
    - In Shabda repository, install dependencies: `poetry install`

Use (command line)
------------------

In order to download a sample pack, execute in the terminal `shabda <definition> --licenses <license_name>`.

Any word can be a pack definition. If you want more than one sample, separate words by a comma: `blue,red`

You can define how many variations of a sample to assemble by adding a colon and a number.
e.g. `blue,red:3,yellow:2` will produce one 'blue' sample, three 'red' samples and two 'yellow' sample.

The optional `--licenses` parameter allows to fetch only samples that have the specified license. Multiple licenses can be allowed by repeating the `--licenses` argument. Possible licenses are `cc0` (Creative Commons Zero), `by` (Creative Commons Attribution), and `by-nc` (Creative Commons Attribution Non-Commercial).

Full example:
```
shabda spaghetti:2,monster:4 --licenses cc0 --licenses by
```

The first time you execute this command, it will ask you for a Freesound token, that you will be redirected to. You will need a Freesound account.

By default, samples will be downloaded in a `samples` directory under the current working directory. You can override this by adding a `config.ini` file to the `$HOME/.shabda/` directory, containing:

```ini
[shabda]

samples_path=/path/to/your/desired/samples/directory/
```

Use (web application)
---------------------

Launch the web application:

In debug mode:
```
FLASK_APP=shabda FLASK_DEBUG=1 flask run

or 

FLASK_APP=shabda FLASK_DEBUG=1 poetry run flask run

```
In production:
```
gunicorn --workers=4 "shabda:create_app()" -b localhost:8000
```

Then navigate to `http://localhost:5000/` (or your production URL).

### Pack Tab

Fetch random audio samples from Freesound based on words.

- **Pack definition**: Enter one or more words separated by commas (e.g., `blue,red:3`).
- **Licenses**: Select which Creative Commons licenses to allow (cc0, by, by-nc).
- **Fetch pack**: Generates a reslist with sample URLs.

Use in Estuary:
```
!reslist "http://your-shabda-url/blue,red.json"
```

Use in Strudel:
```
samples('shabda:blue:2,red:3')
```

### Speech Tab

Generate Text-to-Speech samples from text input.

- **Speech definition**: Enter words or sentences (spaces become underscores; `hello_world` produces a "hello world" sample).
- **Gender**: Choose Female or Male voice.
- **Language**: Select from 50+ languages (e.g., en-GB, en-US, fr-FR, ja-JP).
- **Fetch speech**: Generates audio samples using the selected voice.

Use in Estuary:
```
!reslist "http://your-shabda-url/speech/hello_world.json?language=en-GB&gender=f"
```

Use in Strudel:
```
samples('shabda/speech/en-GB/f:hello_world')
```

### Phonemes Tab

Generate phoneme-level samples with musical timing alignment. Each phoneme chunk becomes a sample, with stress-aware line wrapping for Strudel integration.

**Inputs:**
- **Phoneme definition**: Enter lyrics (one or more sentences, any case). Commas and underscores separate phrases. Example:
  ```
  Papa was a rolling stone
  Wherever he laid his hat
  ```
- **ARPABET overrides**: Specify custom pronunciations for words in `word:PH1_PH2 format` (e.g., `papa:P_AA1_P_A;hat:HH_AE1_T`). Separate multiple overrides with semicolons.
- **Beats / bar**: Musical meter (default 4 for 4/4 time).
- **Bars / line**: Lines per phrase (default 2).
- **Target stress beat**: Which beat in the bar should primary stressed syllables land on (default 3 for a pickup feel; use 1 for downbeat emphasis).
- **Gender**: Choose Female or Male voice (default: Male).
- **Language**: Select pronunciation language (default: en-GB).

**Actions:**
- **Preview phonemes**: Returns text analysis and Strudel timing without synthesizing audio (fast).
- **Fetch phonemes**: Synthesizes all phoneme samples as WAV files (slower first time, then cached).

**Output includes:**
- IPA transcription of each word
- ARPABET phoneme breakdown
- Stress pattern analysis
- Timed Strudel phrases with beat alignment
- Direct audio sample URLs

Use in Strudel:
```
samples('shabda/phonemes/en-GB/m:papa_was_a_rolling_stone', { overrides: 'papa:P_AA1_P_A' })
s("phc_P_AA1_P_A phc_W_AA1_Z phc_AH0 ~ phc_R_OW1_L_IH0_NG ...")
```

**How stress alignment works:**
- If a line's first phoneme chunk is stressed (marked with 1 or 2), it lands on beat 1 (no rest needed).
- If a line starts unstressed, rests are added so the first stressed chunk lands on the target beat (default beat 3).
- This ensures consistent musical phrasing across all lines.

Test
----

```
poetry run pytest
```

Notes
-----

With Estuary, Shabda makes use of this feature: https://github.com/dktr0/estuary/wiki#adding-sound-files-to-estuarywebdirt-on-the-fly

All command line examples must be preceded by `poetry run` if in hacking/development mode.

Roadmap
-----

See: https://github.com/users/ilesinge/projects/4
