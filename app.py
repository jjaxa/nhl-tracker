from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# -------------------------------------------------------------------------
# Fetch all current NHL skaters (using the reliable skater-leaders endpoint)
# -------------------------------------------------------------------------
def get_all_skaters():
    print("[INFO] Fetching player list via skater-leaders endpoint...")
    players = {}
    url = "https://api-web.nhle.com/v1/skater-stats-leaders/current?limit=-1"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        data = resp.json().get("data", [])
        for row in data:
            # Some entries may not have player info (filter them out)
            name = row.get("skaterFullName")
            pid = row.get("playerId")
            if name and pid:
                players[name] = pid
        print(f"[INFO] Loaded {len(players)} skaters.")
    except Exception as e:
        print(f"[ERROR] Could not fetch skater list: {e}")

    return dict(sorted(players.items()))

# -------------------------------------------------------------------------
# Fetch individual skater live stats
# -------------------------------------------------------------------------
def get_player_stats(player_ids):
    stats = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for pid in player_ids:
        try:
            url = f"https://api-web.nhle.com/v1/player/{pid}/landing"
            resp = requests.get(url, headers=headers, timeout=15)
            data = resp.json()

            # Extract the latest season stats
            stats_splits = data.get("careerTotals", {}).get("regularSeason", {}).get("subSeason", [])
            if stats_splits:
                latest = stats_splits[-1]
                stats.append({
                    "name": data.get("firstName", "") + " " + data.get("lastName", ""),
                    "team": data.get("currentTeamAbbrev", ""),
                    "gamesPlayed": latest.get("gamesPlayed", 0),
                    "goals": latest.get("goals", 0),
                    "assists": latest.get("assists", 0),
                    "points": latest.get("points", 0),
                    "shots": latest.get("shots", 0)
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
