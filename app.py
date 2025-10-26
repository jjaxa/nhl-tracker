from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Modern NHL Stats API endpoint (stable, public)
PLAYER_API = "https://api.nhle.com/stats/rest/en/skater/summary"

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

    # use a reliable proxy mirror that fetches JSON safely
    proxy_url = (
        "https://api.codetabs.com/v1/proxy?quest="
        "https://api.nhle.com/stats/rest/en/skater/summary"
    )

    params = {
        "isAggregate": "false",
        "isGame": "false",
        "sort": '[{\"property\":\"points\",\"direction\":\"DESC\"}]',
        "start": 0,
        "limit": 5000,
        "factCayenneExp": "gameTypeId=2"
    }

    try:
        resp = requests.get(proxy_url, params=params, headers=headers, timeout=25)
        text = resp.text.strip()
        if not text or not text.startswith("{"):
            print("[WARN] Empty or invalid response from proxy.")
            return {}
        data = resp.json()
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
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36"
    }

    for pid in player_ids:
        try:
            url = f"https://api.nhle.com/stats/rest/en/skater/summary?cayenneExp=playerId={pid}"
            data = requests.get(url, headers=headers, timeout=10).json().get("data", [])
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
        except Exception as e:
            print(f"[WARN] Failed for player {pid}: {e}")
    return stats

# -------------------------------------------------------------------------
# Flask routes
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
# Gunicorn will handle running this app (no manual app.run)
# -------------------------------------------------------------------------
