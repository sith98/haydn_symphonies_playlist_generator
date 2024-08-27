from dotenv import load_dotenv
import os
import requests
import json
import csv
import math

load_dotenv()

playlist_id = os.getenv("PLAYLIST_ID")


import spotipy
from spotipy.oauth2 import SpotifyOAuth


def get_token():
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        params={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    if resp.status_code != 200:
        resp
        data = resp.json()
        return data["access_token"]
    else:
        raise ValueError(
            f"Request failed with status code {response.status_code}: {response.text}"
        )


BWV = "BWV"
ends = [":", "("]


def get_name(track):
    return track["track"]["name"]


def get_bwv(name):
    if BWV in name.upper():
        start = name.index(BWV) + 4
        end = start
        while end < len(name) and name[end] in [str(i) for i in range(10)] + ["a", "b"]:
            end += 1
        try:
            bwv = name[start:end]
            return bwv
        except Exception:
            return None


special_bwv = {"Schlage doch, gewünschte Stunde": "53"}


def main():
    with open("bach_ranking.json") as file:
        ranking = json.load(file)
    with open("tracks_bach.json") as file:
        tracks = json.load(file)
    with open("christmas_oratorio.json") as file:
        christmas_oratorio = json.load(file)
    with open("cantata_order.txt") as file:
        order = {
            line.strip(): i
            for i, line in enumerate(file.readlines())
            if line.strip != ""
        }

    for cat in ranking:
        cat["bwvs"].sort(key=lambda bwv: order[bwv] if bwv in order else -1)

    tracks_by_bwv = {}
    for i, track in enumerate(tracks):
        name = get_name(track)
        bwv = get_bwv(name)
        # if "Ascension" in name:
        #     print(name)
        #     print(bwv == 11)
        if bwv is None:
            prev = get_name(tracks[i - 1])
            next = get_name(tracks[i + 1])
            if get_bwv(prev) == get_bwv(next):
                bwv = get_bwv(prev)
            elif prev[:10] == name[:10]:
                bwv = get_bwv(prev)
            elif next[:10] == name[:10]:
                bwv = get_bwv(next)
            elif name in special_bwv:
                bwv = special_bwv[name]
            else:
                print(f"No BWV:")
                print(name)
                print(prev)
                print(next)
                continue
        if name in christmas_oratorio:
            bwv += "/" + christmas_oratorio[name]
        if bwv not in tracks_by_bwv:
            tracks_by_bwv[bwv] = []
        # get rid of multiple version in Suzuki recordings
        if bwv == "21" and "Leipzig" not in name:
            continue
        if bwv == "82" and "Soprano" in name:
            continue
        tracks_by_bwv[bwv].append(track)

    new_tracks = []
    for cat in ranking:
        if cat["name"] == "1":
            for bwv in cat["bwvs"]:
                if bwv in tracks_by_bwv:
                    new_tracks.extend(tracks_by_bwv[bwv])
                    # print(bwv, len(tracks_by_bwv[bwv]))

    track_ids = [t["track"]["id"] for t in new_tracks]
    track_names = [t["track"]["name"] for t in new_tracks]

    for name in track_names:
        print(name)

    # return

    # tracks = get_symphoniy_tracks()
    # with open("tracks_bach.json", "w") as file:
    #     json.dump(tracks, file)

    # return

    scope = "playlist-modify-public playlist-modify-private"

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    batch_size = 100
    for offset in range(0, len(track_ids), batch_size):
        uris_batch = [
            f"spotify:track:{id}" for id in track_ids[offset : offset + batch_size]
        ]
        sp.playlist_add_items(playlist_id, uris_batch, offset)
    # print(resp.json())


def get_symphoniy_tracks():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=""))

    # token = get_token()
    # https://open.spotify.com/playlist/35L8p7admQlUfYpArEHFHX?si=3637beae90fb4dd3
    # album_id = "35L8p7admQlUfYpArEHFHX"
    album_id = "03ef53ts1S3KTQsdfkxV2i"

    playlist = sp.playlist(album_id)
    n_tracks = playlist["tracks"]["total"]

    limit = 100

    tracks = []
    for offset in range(0, n_tracks, limit):
        data = sp.playlist_tracks(album_id, limit=100, offset=offset)
        tracks.extend(data["items"])
        print(offset)
    return tracks


if __name__ == "__main__":
    main()
