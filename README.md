DJMF
====

A tool to fetch random samples from https://freesound.org/ based on given words, for use in impro sessions on instruments such as Tidal Cycles.

Install
-------

- Install Python (2 and 3 are supported): https://www.python.org/
- Install pip: https://pypi.org/project/pip/
- Install dependencies: `pip install -r requirements.txt`

Use
---

Execute in terminal `python DJMF.py <word1> <word2> <...> --num <number_of_sample_per_word>`

```
python DJMF.py spaghetti monster --num 4
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

- Normalize samples volume
- Use advanced search in a funky way: https://freesound.org/docs/api/analysis_docs.html#analysis-docs
- ???
