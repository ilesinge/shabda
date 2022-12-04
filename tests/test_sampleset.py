"""Test SampleSet"""

import os
from shabda.sampleset import SampleSet


def test_init_new(fake_filesystem):  # pylint:disable=unused-argument
    """Initialize non existing sample"""
    SampleSet("test1")
    assert os.path.exists("samples/test1/")


def test_init_existing(fake_filesystem):
    """Initialize existing sample"""
    fake_filesystem.create_file(
        "samples/test1/config", contents='{"master": 1, "sounds": [2, 3]}'
    )

    sample = SampleSet("test1")
    assert sample.master_id == 1
    assert sample.sounds == [2, 3]


def test_dir(fake_filesystem):  # pylint:disable=unused-argument
    """Check sample directory"""
    sample = SampleSet("test1")
    assert sample.dir() == "samples/test1"


def test_add(mocker, fake_filesystem):  # pylint:disable=unused-argument
    """Add a sample"""
    sound = mocker.Mock()
    sound.id = 4
    sound.username = "bob"
    sound.licensename = "cc0"
    sound.url = "https://sample/"
    sound.file = "samples/tchak/0.wav"
    sound.gender = None
    sound.language = None
    sample = SampleSet("test1")
    sample.add(sound)
    assert {
        "id": 4,
        "username": "bob",
        "license": "cc0",
        "url": "https://sample/",
        "file": "samples/tchak/0.wav",
        "gender": None,
        "language": None,
    } in sample.sounds


def test_list(fake_filesystem):
    """List samples"""
    fake_filesystem.create_file(
        "samples/test1/config",
        contents="""{"master": 1, "sounds": [{"id": 337514, "url":
            "https://freesound.org/people/eardeer/sounds/337514/", "username": "eardeer",
            "license": "Attribution", "file": "samples/test1/0.wav"}]}""",
    )

    sample = SampleSet("test1")

    assert sample.list()[0].__dict__ == {
        "id": 337514,
        "url": "https://freesound.org/people/eardeer/sounds/337514/",
        "username": "eardeer",
        "licensename": "Attribution",
        "file": "samples/test1/0.wav",
    }


def test_clean(fake_filesystem):  # pylint:disable=unused-argument
    """Cleaning sample folder"""
    sample = SampleSet("test1")
    sample.clean()
    assert not os.path.exists("samples/test1/")


def test_saveconfig(fake_filesystem):  # pylint:disable=unused-argument
    """Saving sample config file"""
    sample = SampleSet("test1")
    sample.master_id = 1
    sample.sounds = [
        {
            "id": 4,
            "username": "bob",
            "license": "Creative Commons 0",
            "url": "https://sample/",
        }
    ]
    sample.saveconfig()
    assert os.path.exists("samples/test1/config")
    sample2 = SampleSet("test1")
    assert sample2.master_id == 1
    assert sample2.sounds == [
        {
            "id": 4,
            "username": "bob",
            "license": "Creative Commons 0",
            "url": "https://sample/",
        }
    ]


def test_contains(fake_filesystem):  # pylint:disable=unused-argument
    """Checking if sample set contains a sound id"""
    sample = SampleSet("test1")
    sample.master_id = 1
    sample.sounds = [
        {
            "id": 4,
            "username": "bob",
            "license": "Creative Commons 0",
            "url": "https://sample/",
        }
    ]
    assert sample.contains(4)
    assert not sample.contains(5)
