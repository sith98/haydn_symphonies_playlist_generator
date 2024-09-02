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


def main():
    with open("tracks.json") as file:
        album = json.load(file)

    chronology = []
    # source: https://www.joseph-haydn.art/de/sinfoniae/107
    with open("chronology.txt") as file:
        for line in file.readlines():
            chronology.append(int(line))

    rankings = {}
    categories = {}
    # source: https://www.talkclassical.com/threads/haydns-symphonies-ranked-in-order-of-greatness-by-ardent-haydn-listeners-all-106-symphonies.87080/
    with open("ranking.csv") as file:
        reader = csv.reader(file)
        next(reader)
        for rank, number, nickname, points, category in reader:
            rank = int(rank.strip())
            number = int(number.strip())
            points = float(points.replace(",", ".").strip())
            rankings[number] = (rank, nickname, points, category)
            if category not in categories:
                categories[category] = []
            categories[category].append((number, rank, nickname, points))

        ranking_csv = list(reader)

    symphonies = {}
    for song in album:
        name = song["name"]
        symphony = name.split(":")[0]
        lower = symphony.lower()

        if "version" in lower or "alternative" in lower:
            continue

        if '"A"' in symphony:
            number = 105
        elif '"B"' in symphony:
            number = 106
        elif "concertante" in symphony:
            number = 107
        else:
            parts = symphony.split(" ")
            index = parts.index("No.")
            number = int(parts[index + 1])
        if number not in symphonies:
            symphonies[number] = []

        symphonies[number].append(song)

    quantile = 0.5
    maximum_ranking = math.ceil((1 + len(rankings)) * quantile)

    track_ids = []

    numbers = []
    for number in chronology:
        if number in rankings and rankings[number][0] <= maximum_ranking:
            symphony_tracks = symphonies[number]
            # print(number, rankings[number][-1])
            numbers.append(number)
            for track in symphony_tracks:
                track_ids.append(track["id"])

    categories_in_order = []
    seen_categories = set()

    for number in chronology:
        if number in rankings:
            category = rankings[number][-1]
            if category not in seen_categories:
                categories_in_order.append(category)
                seen_categories.add(category)

    for c in categories_in_order:
        sym = categories[c]
        average_points = sum(s[-1] for s in sym) / len(sym)

        sorted_sym = sorted(sym, key=lambda s: s[-1], reverse=True)
        print(f"{c} ({len(sym)})")
        for s in sorted_sym[:3]:
            print(s[0], s[2], rankings[s[0]][0])
        print()

    print("total", len(numbers))

    return

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
    token = get_token()
    album_id = "4mXfYJF9lS2MgUDKaz6VCV"

    resp = requests.get(
        f"{api_url}/albums/{album_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    album = resp.json()
    n_tracks = album["total_tracks"]
    limit = 50

    tracks = []
    for offset in range(0, n_tracks, limit):
        resp = requests.get(
            f"{api_url}/albums/{album_id}/tracks",
            params={"offset": offset, "limit": 50},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = resp.json()
        tracks.extend(data["items"])
        print(offset)
    with open("tracks.json", "w") as file:
        json.dump(tracks, file)


if __name__ == "__main__":
    main()
