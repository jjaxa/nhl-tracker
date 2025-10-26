from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Modern NHL Stats API endpoint (stable, public)
PLAYER_API = "https://api.nhle.com/stats/rest/en/skater/summary"
PLAYER_DETAIL = "https://api.nhle.com/stats/rest/en/skater/{}"

# -------------------------------------------------------------------------
# Fetch all current skaters
# -------------------------------------------------------------------------
def get_all_skaters():
    print("[INFO] Fetching player list from NHL API...")
    players = {}

    # We’ll get all skaters from the 2024-25 regular season
    params = {
        "isAggregate": "false",
        "isGame": "false",
        "sort": "[{\"property\":\"points\",\"direction\":\"DESC\"}]",
        "start": 0,
        "limit": 5000,
        "factCayenneExp": "gameTypeId=2"  # regular season
    }

    try:
        data = requests.get(PLAYER_API, params=params, timeout=20).json()
        for row in data.get("data", []):
            name = f"{row['playerFirstName']} {row['playerLastName']}"
            players[name] = row["playerId"]
        print(f"[INFO] Loaded {len(players)} skaters.")
    except Exception as e:
        print(f"[ERROR] Could not fetch player list: {e}")

    return dict(sorted(players.items()))

# -------------------------------------------------------------------------
# Fetch live stats for selected players
# -------------------------------------------------------------------------
def get_player_stats(player_ids):
    stats = []
    for pid in player_ids:
        try:
            url = f"https://api.nhle.com/stats/rest/en/skater/summary?cayenneExp=playerId={pid}"
            data = requests.get(url, timeout=10).json().get("data", [])
            if not data:
                continue
            p = data[0]
            stats.append({
                "name": f"{p['playerFirstName']} {p['playerLastName']}",
                "goals": p.get("goals", 0),
                "assists": p.get("assists", 0),
                "points": p.get("points", 0),
                "shots": p.get("shots", 0),
                "gamesPlayed": p.get("gamesPlayed", 0),
                "team": p.get("teamAbbrevs", "")
            })
        except Exception as e:
            print(f"[WARN] Failed for player {pid}: {e}")
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
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
