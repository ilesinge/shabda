from shabda.sound import Sound


def test_translatelicence(mocker):
    """Test translate licence"""

    ssound = mocker.Mock()
    ssound.license = "https://creativecommons.org/licenses/by-nc/4.0/"
    sound = Sound(freesound=ssound)
    assert sound.licensename == "by-nc"

    ssound = mocker.Mock()
    ssound.license = "http://creativecommons.org/publicdomain/zero/1.0/"
    sound = Sound(freesound=ssound)
    assert sound.licensename == "cc0"

    ssound = mocker.Mock()
    ssound.license = "http://creativecommons.org/licenses/by/3.0/"
    sound = Sound(freesound=ssound)
    assert sound.licensename == "by"
