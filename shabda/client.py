"""Freesound client"""
import json
import webbrowser
import os

import requests
import freesound

from termcolor import colored


class Client:
    """Freesound client"""

    FS_CLIENT_ID = "vPkOlpykBDA4fU9fzGmE"
    token_data = {}
    client = None
    path = ""

    def __init__(self, path):
        self.path = path
        if len(path):
            os.makedirs(self.path, exist_ok=True)
        try:
            with open(
                os.path.join(self.path, "token_data"), "r", encoding="UTF-8"
            ) as file:
                self.token_data = json.load(file)
        except IOError:
            self.token_data = {}
        if "access_token" not in self.token_data:
            self._authorize()

        self.client = freesound.FreesoundClient()
        self.client.set_token(self.token_data["access_token"], "oauth")

        self._refresh_token()

    def _authorize(self):
        url = (
            "https://freesound.org/apiv2/oauth2/authorize/?client_id="
            + self.FS_CLIENT_ID
            + "&response_type=code"
        )
        print("")
        input(
            colored(
                "OAuth2 token needed. Press Enter to continue and come back with a code...",
                "blue",
            )
        )
        print("")
        print("If a browser has not opened, please manually go to " + url)
        print("")
        webbrowser.open(url)
        code = input("Please enter authorization code: ")
        url = "https://freesound.org/apiv2/oauth2/access_token/"
        params = {
            "client_id": self.FS_CLIENT_ID,
            "grant_type": "authorization_code",
            "code": code,
        }
        response = requests.post(url, params, timeout=5)
        if response.status_code == 200:
            self.token_data = response.json()
            with open(
                os.path.join(self.path, "token_data"), "w", encoding="UTF-8"
            ) as file:
                json.dump(self.token_data, file)
        else:
            raise Exception("An error occured while getting access token.", response)

    def _refresh_token(self):
        # Trying to get current user, to check if OAuth2 token is correct.
        uri = freesound.URIS.uri(freesound.URIS.ME)
        try:
            user = freesound.FSRequest.request(uri, None, self.client, freesound.User)
            print("Logged in as " + user.username)
        except freesound.FreesoundException as exception:
            if exception.code == 401:
                url = "https://freesound.org/apiv2/oauth2/access_token/"
                params = {
                    "client_id": self.FS_CLIENT_ID,
                    "grant_type": "refresh_token",
                    "refresh_token": self.token_data["refresh_token"],
                }
                response = requests.post(url, params, timeout=5)
                if response.status_code == 200:
                    self.token_data = response.json()
                    with open(
                        os.path.join(self.path, "token_data"), "w", encoding="UTF-8"
                    ) as file:
                        json.dump(self.token_data, file)
                    self.client.set_token(self.token_data["access_token"], "oauth")
                else:
                    raise Exception(
                        "An error occured while refreshing access token.", response
                    ) from exception
            else:
                raise exception

    def __getattr__(self, attr):
        def wrapped_method(*args, **kwargs):
            # try:
            result = getattr(self.client, attr)(*args, **kwargs)
            # except freesound.FreesoundException as exception:
            #     if exception.code == 401:
            #         self._refresh_token()
            #         result = getattr(self.client, attr)(*args, **kwargs)
            #     else:
            #         raise exception
            return result

        return wrapped_method
