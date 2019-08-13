#!/usr/bin/env python

import freesound
import argparse
import random
import os
import sys
import pydub
import webbrowser
from termcolor import colored
import requests
import json

parser = argparse.ArgumentParser(description='Dawnlods som ear shiiz')
parser.add_argument("w00t", nargs='+', help="Waddyawant?")
parser.add_argument('--num', type=int, default=5, nargs='?', help='Ow many?')
args = parser.parse_args()

FS_CLIENT_ID = "vPkOlpykBDA4fU9fzGmE"

try:
    with open('token_data', 'r') as file:
        token_data = json.load(file)
except IOError:
    token_data = {}

if 'access_token' not in token_data:
    url = "https://freesound.org/apiv2/oauth2/authorize/?client_id="+FS_CLIENT_ID+"&response_type=code"
    print("")
    raw_input(colored("OAuth2 token needed. Press Enter to continue and come back with a code...", "blue"))
    print("")
    print("If a browser has not opened, please manually go to "+url)
    print("")
    webbrowser.open(url)
    code = raw_input("Please enter authorization code: ")
    url = "https://freesound.org/apiv2/oauth2/access_token/"
    params = {
        'client_id': FS_CLIENT_ID,
        'grant_type': 'authorization_code',
        'code': code,
    }
    response = requests.post(url, params)
    if response.status_code == 200:
        token_data = response.json()
        with open("token_data", "w") as file:
            json.dump(token_data, file)
    else:
        print_error("An error occured while getting access token.", response)
        sys.exit()

client = freesound.FreesoundClient()
client.set_token(token_data['access_token'], "oauth")

# Trying to get current user, to check if OAuth2 token is correct.
uri = freesound.URIS.uri(freesound.URIS.ME)
try:
    user = freesound.FSRequest.request(uri, None, client, freesound.User)
    print("Logged in as "+user.username)
except freesound.FreesoundException as e:
    if e.code == 401:
        url = "https://freesound.org/apiv2/oauth2/access_token/"
        params = {
            'client_id': FS_CLIENT_ID,
            'grant_type': 'refresh_token',
            'refresh_token': token_data['refresh_token'],
        }
        response = requests.post(url, params)
        if response.status_code == 200:
            token_data = response.json()
            with open("token_data", "w") as file:
                json.dump(token_data, file)
            client.set_token(token_data['access_token'], "oauth")
        else:
            print_error("An error occured while refreshing access token.", response)
            sys.exit()
    else:
        raise e

def print_error(message, e=None):
    print("")
    print(colored(message, "red"))
    print("")
    if e:
        print(e)

def unicode_please(string):
    if (sys.version_info > (3, 0)):
        return string
    else:
        return string.encode('utf-8')

for word in args.w00t:
    word_dir = "samples/" + word
    if not os.path.exists(word_dir):
        os.makedirs(word_dir)
    print("")
    print(colored('Searching freesound for "' + word + '"...', "green"))
    print("")
    results = client.text_search(query=word, fields="id,name,type", page_size=100)
    result_number = len(results.results)
    similar = None
    while not similar:
        key = random.randint(0, result_number - 1)
        sound = results[key]
        try:
            similar = sound.get_similar(fields="id,name,type,previews", page_size=100)
        except freesound.FreesoundException as e:
            if e.code == 404:
                print_error("Missing sound, continue")
                continue
            else:
                print_error("Error while getting similar sounds", e)
                raise e
    name = unicode_please(sound.name)
    print("Sound found: " + name)
    result_number = len(similar.results)
    keys = []
    while( len(keys) < args.num):
        key = random.randint(0, result_number - 1)
        if key in keys:
            continue
        keys.append(key)

    # Define random common duration for word samples
    sample_duration = random.randint(200, 5000)
    print("Random sample duration: " + str(sample_duration) + "ms")
    sample_num = 1
    for key in keys:
        try:
            ssound = similar[key]
            ssound_name = unicode_please(ssound.name)
            source_name = ssound_name + "-source"
            source_path = word_dir + "/" + source_name
            print("Dowloading similar sample #" + str(sample_num) + "...")
            ssound.retrieve(word_dir, source_name)

            sound = pydub.AudioSegment.from_file(source_path)
            export_name = ssound_name + ".wav"
            duration = len(sound)
            begin = random.randint(0, max(duration - sample_duration, 0))
            sound = sound[begin : begin + sample_duration] # random cut
            sound.export(word_dir + "/" + export_name, format="wav")
            sample_num += 1
        except pydub.exceptions.CouldntDecodeError as e:
            print_error("Error while decoding source file", e)
            continue
        except freesound.FreesoundException as e:
            print_error("Error while downloading sound", e)
            continue
        if os.path.exists(source_path):
            os.remove(source_path)

print("")
print("Done!")