from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# -------------------------------------------------------------------------
# Fetch all current NHL skaters from the season leaders endpoint
# -------------------------------------------------------------------------
def get_all_skaters():
    print("[INFO] Fetching player list from NHL API (2024–25 season)...")
    players = {}
    url = "https://api-web.nhle.com/v1/skater-stats-leaders/20242025?limit=-1"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        data = resp.json().get("data", [])
        for row in data:
            name = row.get("skaterFullName")
            pid = row.get("playerId")
            if name and pid:
                players[name] = pid
        print(f"[INFO] Loaded {len(players)} skaters.")
    except Exception as e:
        print(f"[ERROR] Could not fetch skater list: {e}")

    return dict(sorted(players.items()))

# -------------------------------------------------------------------------
# Fetch individual skater stats
# -------------------------------------------------------------------------
def get_player_stats(player_ids):
    stats = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for pid in player_ids:
        try:
            url = f"https://api-web.nhle.com/v1/player/{pid}/landing"
            resp = requests.get(url, headers=headers, timeout=15)
            data = resp.json()

            # Pull latest regular season stats
            latest = data.get("careerTotals", {}).get("regularSeason", {}).get("subSeason", [])
            if latest:
                season = latest[-1]
                stats.append({
                    "name": f"{data.get('firstName', '')} {data.get('lastName', '')}",
                    "team": data.get("currentTeamAbbrev", ""),
                    "gamesPlayed": season.get("gamesPlayed", 0),
                    "goals": season.get("goals", 0),
                    "assists": season.get("assists", 0),
                    "points": season.get("points", 0),
                    "shots": season.get("shots", 0)
                })
        except Exception as e:
            print(f"[WARN] Failed to get player stats for {pid}: {e}")

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
# Gunicorn entry point
# -------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
