from flask import Flask, render_template, request, jsonify
import requests, json

app = Flask(__name__)

# Primary & proxy URLs
PLAYER_API_MAIN = "https://api.nhle.com/stats/rest/en/skater/summary"
PROXIES = [
    "https://api.codetabs.com/v1/proxy?quest=",
    "https://thingproxy.freeboard.io/fetch/",
    "https://api.allorigins.win/raw?url="
]

# -------------------------------------------------------------------------
# Fetch all current skaters
# -------------------------------------------------------------------------
def get_all_skaters():
    print("[INFO] Fetching player list from NHL API...")
    players = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36"
    }

    params = {
        "isAggregate": "false",
        "isGame": "false",
        "sort": '[{"property":"points","direction":"DESC"}]',
        "start": 0,
        "limit": 5000,
        "factCayenneExp": "gameTypeId=2"
    }

    urls = [PLAYER_API_MAIN] + [p + PLAYER_API_MAIN for p in PROXIES]

    for url in urls:
        try:
            print(f"[TRY] {url}")
            resp = requests.get(url, params=params, headers=headers, timeout=25)
            text = resp.text.strip()
            if not text or not text.startswith("{"):
                print(f"[WARN] Invalid response from {url[:50]}...")
                continue
            data = resp.json()
            for row in data.get("data", []):
                name = f"{row['playerFirstName']} {row['playerLastName']}"
                players[name] = row["playerId"]
            if players:
                print(f"[INFO] Loaded {len(players)} skaters.")
                return dict(sorted(players.items()))
        except Exception as e:
            print(f"[ERROR] {url} failed: {e}")

    print("[ERROR] Could not fetch any player list from all sources.")
    return {}

# -------------------------------------------------------------------------
# Fetch live stats for selected players
# -------------------------------------------------------------------------
def get_player_stats(player_ids):
    stats = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36"
    }

    for pid in player_ids:
        urls = [f"{PLAYER_API_MAIN}?cayenneExp=playerId={pid}"] + \
               [f"{p}{PLAYER_API_MAIN}?cayenneExp=playerId={pid}" for p in PROXIES]
        for url in urls:
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                if not resp.text.startswith("{"):
                    continue
                data = resp.json().get("data", [])
                if not data:
                    continue
                p = data[0]
                stats.append({
                    "name": f"{p['playerFirstName']} {p['playerLastName']}",
                    "team": p.get("teamAbbrevs", ""),
                    "gamesPlayed": p.get("gamesPlayed", 0),
                    "goals": p.get("goals", 0),
                    "assists": p.get("assists", 0),
                    "points": p.get("points", 0),
                    "shots": p.get("shots", 0)
                })
                break  # success, no need to try next proxy
            except Exception as e:
                print(f"[WARN] Failed for {url[:50]}: {e}")
    return stats

# -------------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------------
@app.route("/")
def index():
    players = get_all_skaters()
    return render_template("index.html", players=players)

@app.route("/live_stats", methods=["POST"])
def live_stats():
    ids = request.form.getlist("player_ids[]")
    data = get_player_stats(ids)
    return jsonify(data)

# -------------------------------------------------------------------------
# Gunicorn will handle running this app
# -------------------------------------------------------------------------
