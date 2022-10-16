"""A single sound file and mappings from Freesound"""


class Sound:
    """A sound file"""

    id = None
    username = None
    url = None
    licensename = None
    file = None
    language = None
    gender = None

    def __init__(self, freesound=None, configsound=None, speechsound=None):
        if freesound is not None:
            self.id = freesound.id
            self.username = freesound.username
            self.url = freesound.url
            self.licensename = self._translate_license(freesound.license)
        if configsound is not None:
            self.id = configsound["id"]
            self.username = configsound["username"]
            self.url = configsound["url"]
            self.licensename = configsound["license"]
            self.file = configsound["file"]
        if speechsound is not None:
            self.language = speechsound["language"]
            self.gender = speechsound["gender"]
            self.file = speechsound["file"]

    def _translate_license(self, licenseurl):
        """Translate a license URL into a license  name"""
        if "/licenses/by-nc/" in licenseurl:
            # "Attribution Noncommercial"
            return "by-nc"
        if "/publicdomain/zero/" in licenseurl:
            # "Creative Commons 0"
            return "cc0"
        if "/licenses/by/" in licenseurl:
            # "Attribution"
            return "by"
        return "Unknown"
