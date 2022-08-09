"""A single sound file and mappings from Freesound"""

# TODO: make that a wrapper around Freesound object
class Sound:
    """A sound file"""

    id = None
    username = None
    url = None
    licensename = None

    def __init__(self, sound):
        self.id = sound.id
        self.username = sound.username
        self.url = sound.url
        self.licensename = self._translate_license(sound.license)

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
